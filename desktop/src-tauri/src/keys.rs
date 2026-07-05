use keyring::Entry;

const SERVICE: &str = "com.yenba.acis-weather-bot";

/// Providers we surface in Settings, with the env var pi's AuthStorage reads.
pub const PROVIDERS: [(&str, &str); 6] = [
    ("anthropic", "ANTHROPIC_API_KEY"),
    ("openai", "OPENAI_API_KEY"),
    ("google", "GEMINI_API_KEY"),
    ("xai", "XAI_API_KEY"),
    ("groq", "GROQ_API_KEY"),
    ("openrouter", "OPENROUTER_API_KEY"),
];

fn env_var_for(provider: &str) -> Option<&'static str> {
    PROVIDERS
        .iter()
        .find(|(p, _)| *p == provider)
        .map(|(_, v)| *v)
}

fn entry(provider: &str) -> Result<Entry, String> {
    Entry::new(SERVICE, provider).map_err(|e| format!("keychain error: {}", e))
}

#[derive(serde::Serialize)]
pub struct KeyStatus {
    pub provider: String,
    pub configured: bool,
}

#[tauri::command]
pub fn set_api_key(provider: String, key: String) -> Result<(), String> {
    if env_var_for(&provider).is_none() {
        return Err(format!("unknown provider: {}", provider));
    }
    let trimmed = key.trim();
    if trimmed.is_empty() {
        return Err("key is empty".to_string());
    }
    entry(&provider)?
        .set_password(trimmed)
        .map_err(|e| format!("keychain error: {}", e))
}

#[tauri::command]
pub fn delete_api_key(provider: String) -> Result<(), String> {
    match entry(&provider)?.delete_credential() {
        Ok(()) => Ok(()),
        Err(keyring::Error::NoEntry) => Ok(()),
        Err(e) => Err(format!("keychain error: {}", e)),
    }
}

#[tauri::command]
pub fn get_api_key_status() -> Result<Vec<KeyStatus>, String> {
    Ok(PROVIDERS
        .iter()
        .map(|(provider, _)| KeyStatus {
            provider: provider.to_string(),
            configured: entry(provider)
                .and_then(|e| e.get_password().map_err(|err| err.to_string()))
                .is_ok(),
        })
        .collect())
}

/// (ENV_VAR, key) pairs for every configured provider — used when spawning the sidecar.
/// Keys must never be logged.
pub fn collect_api_keys() -> Vec<(String, String)> {
    PROVIDERS
        .iter()
        .filter_map(|(provider, env_var)| {
            let key = entry(provider).ok()?.get_password().ok()?;
            Some((env_var.to_string(), key))
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn env_var_mapping() {
        assert_eq!(env_var_for("anthropic"), Some("ANTHROPIC_API_KEY"));
        assert_eq!(env_var_for("google"), Some("GEMINI_API_KEY"));
        assert_eq!(env_var_for("bogus"), None);
    }

    #[test]
    fn rejects_unknown_provider_and_empty_key() {
        assert!(set_api_key("bogus".into(), "k".into()).is_err());
        assert!(set_api_key("anthropic".into(), "   ".into()).is_err());
    }
}