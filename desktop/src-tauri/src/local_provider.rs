use std::fs;
use std::path::PathBuf;
use serde::Deserialize;
use serde_json::{Value, json};
use reqwest::Client;

fn get_models_json_path() -> PathBuf {
    let home = std::env::var("HOME").unwrap_or_else(|_| "/tmp".to_string());
    PathBuf::from(home).join(".pi").join("agent").join("models.json")
}

#[tauri::command]
pub async fn set_local_provider(url: String) -> Result<(), String> {
    let path = get_models_json_path();
    
    // Ensure dir exists
    if let Some(parent) = path.parent() {
        fs::create_dir_all(parent).map_err(|e| e.to_string())?;
    }

    // Read existing
    let mut data = if path.exists() {
        let content = fs::read_to_string(&path).map_err(|e| e.to_string())?;
        serde_json::from_str::<Value>(&content).unwrap_or_else(|_| json!({}))
    } else {
        json!({})
    };

    if data.get("providers").is_none() {
        data["providers"] = json!({});
    }

    if url.trim().is_empty() {
        if let Some(providers) = data["providers"].as_object_mut() {
            providers.remove("local");
        }
    } else {
        let base_url = url.trim().trim_end_matches('/').to_string();
        
        // Fetch models from the OpenAI-compatible endpoint
        let client = Client::new();
        let models_url = format!("{}/models", base_url);
        
        let response = client.get(&models_url)
            .send()
            .await
            .map_err(|e| format!("Failed to connect to local provider: {}", e))?;
            
        if !response.status().is_success() {
            return Err(format!("Server returned error: {}", response.status()));
        }
        
        let models_data: Value = response.json()
            .await
            .map_err(|e| format!("Invalid JSON response: {}", e))?;
            
        let mut models_arr = Vec::new();
        if let Some(data_arr) = models_data.get("data").and_then(|d| d.as_array()) {
            for item in data_arr {
                if let Some(id) = item.get("id").and_then(|i| i.as_str()) {
                    models_arr.push(json!({ "id": id }));
                }
            }
        }
        
        if models_arr.is_empty() {
            return Err("Connected successfully, but no models found.".to_string());
        }
        
        let local = json!({
            "baseUrl": base_url,
            "api": "openai-completions",
            "apiKey": "dummy",
            "models": models_arr
        });
        
        data["providers"]["local"] = local;
    }

    fs::write(&path, serde_json::to_string_pretty(&data).map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;

    Ok(())
}

#[tauri::command]
pub async fn get_local_provider() -> Result<Option<String>, String> {
    let path = get_models_json_path();
    if !path.exists() {
        return Ok(None);
    }
    let content = fs::read_to_string(&path).map_err(|e| e.to_string())?;
    let data = serde_json::from_str::<Value>(&content).unwrap_or_else(|_| json!({}));
    
    if let Some(local) = data.get("providers").and_then(|p| p.get("local")) {
        if let Some(url) = local.get("baseUrl").and_then(|u| u.as_str()) {
            return Ok(Some(url.to_string()));
        }
    }
    
    Ok(None)
}
