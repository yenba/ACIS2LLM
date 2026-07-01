import re

with open("src-tauri/src/lib.rs", "r") as f:
    content = f.read()

# 1. Imports and AppState
new_imports = """use tauri::{AppHandle, Emitter, State};
use std::process::{Command, Stdio, Child};
use std::io::{BufRead, BufReader};
use std::sync::Mutex;

struct AppState {
    active_process: Mutex<Option<Child>>,
}"""

content = content.replace(
    "use tauri::{AppHandle, Emitter};\nuse std::process::{Command, Stdio};\nuse std::io::{BufRead, BufReader};",
    new_imports
)

# 2. ask_omp signature and state saving
old_ask_omp = """#[tauri::command]
async fn ask_omp(app: AppHandle, message: String, model: String, history: Vec<Message>) -> Result<(), String> {"""

new_ask_omp = """#[tauri::command]
async fn ask_omp(app: AppHandle, state: State<'_, AppState>, message: String, model: String, history: Vec<Message>) -> Result<(), String> {"""

content = content.replace(old_ask_omp, new_ask_omp)

old_stdout_take = """    let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;"""

new_stdout_take = """    let stdout = child.stdout.take().ok_or("Failed to capture stdout")?;
    
    {
        let mut p = state.active_process.lock().unwrap();
        if let Some(mut old) = p.take() {
            let _ = old.kill();
        }
        *p = Some(child);
    }"""

content = content.replace(old_stdout_take, new_stdout_take)

# 3. stop_omp command
stop_omp = """#[tauri::command]
async fn stop_omp(state: State<'_, AppState>) -> Result<(), String> {
    let mut p = state.active_process.lock().unwrap();
    if let Some(mut child) = p.take() {
        let _ = child.kill();
    }
    Ok(())
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]"""

content = content.replace("#[cfg_attr(mobile, tauri::mobile_entry_point)]", stop_omp)

# 4. register state and stop_omp
old_builder = """    tauri::Builder::default()
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![get_models, ask_omp, generate_title])"""

new_builder = """    tauri::Builder::default()
        .manage(AppState { active_process: Mutex::new(None) })
        .plugin(tauri_plugin_shell::init())
        .plugin(tauri_plugin_opener::init())
        .invoke_handler(tauri::generate_handler![get_models, ask_omp, generate_title, stop_omp])"""

content = content.replace(old_builder, new_builder)

with open("src-tauri/src/lib.rs", "w") as f:
    f.write(content)
