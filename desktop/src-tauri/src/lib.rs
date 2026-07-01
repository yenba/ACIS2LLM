use tauri::{AppHandle, Emitter, Manager, State};
use std::process::{Command, Stdio, Child};
use std::io::{BufRead, BufReader};
use std::sync::{Arc, Mutex};

struct AppState {
    // Arc so the streaming thread can reclaim the child to read its exit status,
    // while `stop_omp` can still lock the same handle to kill it.
    active_process: Arc<Mutex<Option<Child>>>,
}

// Build an environment with expanded PATH so omp/bun work when launched from Applications
fn get_expanded_env() -> Vec<(String, String)> {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let current_path = std::env::var("PATH").unwrap_or_default();

    // Prepend common user bin paths that macOS GUI apps don't inherit
    let extra_paths = [
        format!("{}/.bun/bin", home),
        format!("{}/.local/bin", home),
        "/opt/homebrew/bin".to_string(),
        "/opt/homebrew/sbin".to_string(),
        "/usr/local/bin".to_string(),
    ];

    let new_path = extra_paths.join(":") + ":" + &current_path;

    let mut env: Vec<(String, String)> = std::env::vars().collect();
    // Update or add PATH
    if let Some(entry) = env.iter_mut().find(|(k, _)| k == "PATH") {
        entry.1 = new_path;
    } else {
        env.push(("PATH".to_string(), new_path));
    }
    // Ensure BUN_INSTALL is set
    if !env.iter().any(|(k, _)| k == "BUN_INSTALL") {
        env.push(("BUN_INSTALL".to_string(), format!("{}/.bun", home)));
    }

    env
}

// Helper to resolve omp path
fn get_omp_path() -> String {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    let bun_omp = format!("{}/.bun/bin/omp", home);
    if std::path::Path::new(&bun_omp).exists() {
        bun_omp
    } else {
        "omp".to_string()
    }
}

/// Map raw omp stderr into a short, user-friendly message.
/// The full stderr is always written to the log; this is only what we show in the UI.
fn classify_omp_error(stderr: &str) -> String {
    let s = stderr.to_lowercase();
    if s.contains("no api key") {
        "Missing API key for this model's provider. Configure it in omp, then try again."
            .to_string()
    } else if s.contains("model not found") || s.contains("unknown model") || s.contains("not found")
    {
        "That model isn't available. Try selecting a different one.".to_string()
    } else if s.contains("network")
        || s.contains("timeout")
        || s.contains("timed out")
        || s.contains("connection")
        || s.contains("econnrefused")
        || s.contains("fetch failed")
    {
        "Network error reaching the model provider. Check your connection and retry.".to_string()
    } else {
        "The model call failed. See the log for details.".to_string()
    }
}

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
async fn get_models() -> Result<String, String> {
    let omp_path = get_omp_path();
    let env = get_expanded_env();
    log::info!("get_models: running `{} models ls --json`", omp_path);
    // Run `omp models ls --json`
    let output = Command::new(&omp_path)
        .arg("models")
        .arg("ls")
        .arg("--json")
        .envs(env)
        .output()
        .map_err(|e| {
            let msg = format!("Failed to execute omp: {}", e);
            log::error!("get_models: {}", msg);
            msg
        })?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        log::error!(
            "get_models failed (exit {:?}): {}",
            output.status.code(),
            stderr.trim()
        );
        Err(stderr)
    }
}

#[derive(serde::Deserialize)]
pub struct Message {
    role: String,
    content: String,
}

#[tauri::command]
async fn ask_omp(app: AppHandle, state: State<'_, AppState>, message: String, model: String, system_prompt: String, history: Vec<Message>) -> Result<(), String> {
    let omp_path = get_omp_path();

    let mut full_prompt = String::new();
    if !system_prompt.trim().is_empty() {
        full_prompt.push_str(&format!("System Instructions:\n{}\n\n", system_prompt.trim()));
    }

    if !history.is_empty() {
        full_prompt.push_str("Here is the conversation history so far:\n\n");
        for msg in &history {
            let role_name = if msg.role == "user" { "User" } else { "Assistant" };
            full_prompt.push_str(&format!("{}: {}\n\n", role_name, msg.content));
        }
        full_prompt.push_str("Now, reply to the user's new message:\n\n");
    }
    full_prompt.push_str(&message);

    let preview: String = message.chars().take(80).collect();
    log::info!(
        "ask_omp: model={} history={} msg=\"{}{}\"",
        model,
        history.len(),
        preview,
        if message.chars().count() > 80 { "…" } else { "" }
    );

    let env = get_expanded_env();
    // Spawn `omp -p <full_prompt> --model <model>`
    let mut child = Command::new(&omp_path)
        .arg("-p")
        .arg(&full_prompt)
        .arg("--model")
        .arg(&model)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .envs(env)
        .spawn()
        .map_err(|e| {
            let msg = format!("Failed to spawn omp: {}", e);
            log::error!("ask_omp: {}", msg);
            msg
        })?;

    let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
    let stderr = child.stderr.take().ok_or("Failed to capture stderr")?;

    let proc = state.active_process.clone();
    {
        let mut p = proc.lock().unwrap();
        if let Some(mut old) = p.take() {
            let _ = old.kill();
        }
        *p = Some(child);
    }

    // Collect stderr on its own thread so an errored model doesn't hang silently.
    let stderr_handle = std::thread::spawn(move || {
        let mut buf = String::new();
        let reader = BufReader::new(stderr);
        for line_content in reader.lines().map_while(Result::ok) {
            buf.push_str(&line_content);
            buf.push('\n');
        }
        buf
    });

    // Read stdout in a new thread, then check the exit status.
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        let mut got_output = false;
        for line_content in reader.lines().map_while(Result::ok) {
            got_output = true;
            let _ = app.emit("omp-output", line_content + "\n");
        }

        let stderr_output = stderr_handle.join().unwrap_or_default();

        // Reclaim the child to read its exit status. If it's already gone, `stop_omp`
        // cancelled it — that's not an error.
        let child_opt = proc.lock().unwrap().take();
        match child_opt {
            Some(mut child) => {
                let status = child.wait();
                let code = status.as_ref().ok().and_then(|s| s.code());
                let success = status.as_ref().map(|s| s.success()).unwrap_or(false);

                if !success || (!got_output && !stderr_output.trim().is_empty()) {
                    log::error!(
                        "ask_omp: omp exited with {:?}. stderr: {}",
                        code,
                        stderr_output.trim()
                    );
                    if !got_output {
                        let friendly = classify_omp_error(&stderr_output);
                        let _ = app.emit("omp-output", format!("⚠️ {}", friendly));
                    }
                } else {
                    log::info!("ask_omp: completed successfully (exit 0)");
                }
            }
            None => {
                log::info!("ask_omp: process was cancelled by stop_omp");
            }
        }

        let _ = app.emit("omp-done", ());
    });

    Ok(())
}

#[tauri::command]
async fn generate_title(message: String, model: String) -> Result<String, String> {
    let omp_path = get_omp_path();
    let env = get_expanded_env();
    let prompt = format!("Generate a title for a weather query that starts with this message. The title MUST be strictly formatted as '[Location] - [Topic]' (ensure the location includes a comma before the state), for example 'Denver, CO - Winter Snowfall Probability' or 'Miami, FL - Historical Hurricane Records'. Keep it succinct. Do not include quotes or any other text, just the title itself. Message: {}", message);

    let output = Command::new(&omp_path)
        .arg("-p")
        .arg(&prompt)
        .arg("--model")
        .arg(&model)
        .envs(env)
        .output()
        .map_err(|e| {
            let msg = format!("Failed to execute omp: {}", e);
            log::error!("generate_title: {}", msg);
            msg
        })?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).trim().trim_matches('"').to_string())
    } else {
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        log::error!(
            "generate_title failed (exit {:?}): {}",
            output.status.code(),
            stderr.trim()
        );
        Err(stderr)
    }
}

#[tauri::command]
async fn stop_omp(state: State<'_, AppState>) -> Result<(), String> {
    let mut p = state.active_process.lock().unwrap();
    if let Some(mut child) = p.take() {
        log::info!("stop_omp: killing active omp process");
        let _ = child.kill();
    }
    Ok(())
}

/// Reveal the app's log directory in the system file manager.
#[tauri::command]
async fn open_log_folder(app: AppHandle) -> Result<(), String> {
    use tauri_plugin_opener::OpenerExt;
    let dir = app
        .path()
        .app_log_dir()
        .map_err(|e| format!("Could not resolve log directory: {}", e))?;
    let dir_str = dir.to_string_lossy().to_string();
    log::info!("open_log_folder: {}", dir_str);
    app.opener()
        .open_path(dir_str, None::<&str>)
        .map_err(|e| format!("Could not open log directory: {}", e))
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    let log_level = if cfg!(debug_assertions) {
        log::LevelFilter::Debug
    } else {
        log::LevelFilter::Info
    };

    tauri::Builder::default()
        .plugin(
            tauri_plugin_log::Builder::new()
                // Replace the plugin's default targets so records aren't written twice.
                .clear_targets()
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::LogDir { file_name: None },
                ))
                .target(tauri_plugin_log::Target::new(
                    tauri_plugin_log::TargetKind::Stdout,
                ))
                .level(log_level)
                .max_file_size(10_000_000)
                .rotation_strategy(tauri_plugin_log::RotationStrategy::KeepOne)
                .build(),
        )
        .manage(AppState {
            active_process: Arc::new(Mutex::new(None)),
        })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![
            get_models,
            ask_omp,
            generate_title,
            stop_omp,
            open_log_folder
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::classify_omp_error;

    #[test]
    fn classifies_missing_api_key() {
        // The exact string omp emits when a model resolves to a provider with no key.
        let stderr = "error: No API key found for xiaomi.\n\nUse /login, set an API key...";
        assert_eq!(
            classify_omp_error(stderr),
            "Missing API key for this model's provider. Configure it in omp, then try again."
        );
    }

    #[test]
    fn classifies_model_not_found() {
        assert_eq!(
            classify_omp_error("Error: model not found: bogus/model"),
            "That model isn't available. Try selecting a different one."
        );
        assert_eq!(
            classify_omp_error("unknown model 'foo'"),
            "That model isn't available. Try selecting a different one."
        );
    }

    #[test]
    fn classifies_network_errors() {
        assert_eq!(
            classify_omp_error("fetch failed: ECONNREFUSED"),
            "Network error reaching the model provider. Check your connection and retry."
        );
        assert_eq!(
            classify_omp_error("request timed out"),
            "Network error reaching the model provider. Check your connection and retry."
        );
    }

    #[test]
    fn falls_back_for_unknown_errors() {
        assert_eq!(
            classify_omp_error("some totally unexpected panic"),
            "The model call failed. See the log for details."
        );
    }

    #[test]
    fn api_key_takes_priority_over_generic_not_found() {
        // "No API key" also contains no "not found"; ensure ordering is sane even if both appear.
        let stderr = "No API key found for provider; model not found either";
        assert_eq!(
            classify_omp_error(stderr),
            "Missing API key for this model's provider. Configure it in omp, then try again."
        );
    }
}
