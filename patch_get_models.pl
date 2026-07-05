undef $/;
$_ = <>;
s/async fn get_models\(\) -> Result<String, String> \{.*?\n\s*let omp_path = get_omp_path\(\);\n\s*let env = get_expanded_env\(\);\n\s*log::info!\("get_models: running `\{\} --list-models`", omp_path\);\n\s*\/\/ Run `omp models ls --json`\n\s*let output = Command::new\(&omp_path\)\n\s*\.arg\("--list-models"\)\n\s*\.envs\(env\)/async fn get_models(app: AppHandle) -> Result<String, String> {\n    let (prog, mut args) = resolve_sidecar();\n    args.push("--list-models".into());\n    log::info!("get_models: running `{} {:?}`", prog, args);\n    let output = Command::new(&prog)\n        .args(&args)\n        .envs(sidecar_env(&app))/s;
print;
