use tauri::{AppHandle, Emitter, State};
use std::process::{Command, Stdio, Child};
use std::io::{BufRead, BufReader};
use std::sync::Mutex;

struct AppState {
    active_process: Mutex<Option<Child>>,
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

// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
async fn get_models() -> Result<String, String> {
    let omp_path = get_omp_path();
    let env = get_expanded_env();
    // Run `omp models ls --json`
    let output = Command::new(&omp_path)
        .arg("models")
        .arg("ls")
        .arg("--json")
        .envs(env)
        .output()
        .map_err(|e| format!("Failed to execute omp: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
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
        .map_err(|e| format!("Failed to spawn omp: {}", e))?;

    let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
    
    {
        let mut p = state.active_process.lock().unwrap();
        if let Some(mut old) = p.take() {
            let _ = old.kill();
        }
        *p = Some(child);
    }
    
    // Read stdout in a new thread
    std::thread::spawn(move || {
        let reader = BufReader::new(stdout);
        for line in reader.lines() {
            if let Ok(line_content) = line {
                // Emit each line to the frontend
                let _ = app.emit("omp-output", line_content + "\n");
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
        .map_err(|e| format!("Failed to execute omp: {}", e))?;

    if output.status.success() {
        Ok(String::from_utf8_lossy(&output.stdout).trim().trim_matches('"').to_string())
    } else {
        Err(String::from_utf8_lossy(&output.stderr).to_string())
    }
}

#[tauri::command]
async fn stop_omp(state: State<'_, AppState>) -> Result<(), String> {
    let mut p = state.active_process.lock().unwrap();
    if let Some(mut child) = p.take() {
        let _ = child.kill();
    }
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .manage(AppState { active_process: Mutex::new(None) })
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![get_models, ask_omp, generate_title, stop_omp])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
