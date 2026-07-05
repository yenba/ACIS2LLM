undef $/;
$_ = <>;
s/fn classify_omp_error\(/
\/\/\/ Locate the sidecar. Release builds use the bundled binary next to the app
\/\/\/ executable (Tauri externalBin). Debug builds run the TypeScript source via bun.
fn resolve_sidecar() -> (String, Vec<String>) {
    if cfg!(debug_assertions) {
        let sidecar_main = concat!(env!("CARGO_MANIFEST_DIR"), "\/..\/sidecar\/src\/main.ts");
        ("bun".to_string(), vec!["run".to_string(), sidecar_main.to_string()])
    } else {
        let exe_dir = std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.to_path_buf()))
            .unwrap_or_default();
        (exe_dir.join("pi-sidecar").to_string_lossy().to_string(), vec![])
    }
}

\/\/\/ Environment for the sidecar: expanded PATH (so bun\/uv resolve in dev),
\/\/\/ workspace\/data dirs, bundled resources, and API keys from the keychain.
\/\/\/ Keys must never be logged.
fn sidecar_env(app: &AppHandle) -> Vec<(String, String)> {
    let mut env = get_expanded_env();

    if let Ok(data_dir) = app.path().app_data_dir() {
        env.push(("ACIS_DATA_DIR".into(), data_dir.join("sidecar").to_string_lossy().into()));
        env.push(("ACIS_WORKSPACE_DIR".into(), data_dir.join("workspace").to_string_lossy().into()));
    }
    if let Ok(resource_dir) = app.path().resource_dir() {
        let uv = resource_dir.join("uv");
        if uv.exists() {
            env.push(("ACIS_UV_DIR".into(), uv.to_string_lossy().into()));
        }
        let skill = resource_dir.join("skills\/acis-weather");
        if skill.exists() {
            env.push(("ACIS_SKILL_DIR".into(), skill.to_string_lossy().into()));
        }
    }
    if cfg!(debug_assertions) {
        let skill = concat!(env!("CARGO_MANIFEST_DIR"), "\/..\/..\/skills\/acis-weather");
        env.push(("ACIS_SKILL_DIR".into(), skill.to_string()));
    }

    for (var, key) in crate::keys::collect_api_keys() {
        env.push((var, key));
    }
    env
}

fn classify_omp_error(/s;
print;
