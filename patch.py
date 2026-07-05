with open("desktop/src-tauri/src/lib.rs", "r") as f:
    text = f.read()

text = text.replace("""    let env = get_expanded_env();
    // Spawn `omp -p <full_prompt> --model <model> --mode json`
    // JSON mode emits structured events (tool calls, text deltas) that
    // let us show real-time progress in the UI during the TTFT wait.
    let mut child = Command::new(&omp_path)
        .arg("-p")
        .arg(&full_prompt)
        .arg("--model")
        .arg(&model)
        .arg("--mode")
        .arg("json")
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .envs(env)""", """    args.extend(["-p", &full_prompt, "--model", &model, "--mode", "json"].map(String::from));
    let mut child = Command::new(&prog)
        .args(&args)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .envs(sidecar_env(&app))""")

text = text.replace("""async fn generate_title(message: String, model: String) -> Result<String, String> {
    let omp_path = get_omp_path();
    let env = get_expanded_env();
    let prompt = format!("Generate a title for a weather query that starts with this message. The title MUST be strictly formatted as '[Location] - [Topic]' (ensure the location includes a comma before the state), for example 'Denver, CO - Winter Snowfall Probability' or 'Miami, FL - Historical Hurricane Records'. Keep it succinct. Do not include quotes or any other text, just the title itself. Message: {}", message);

    let output = Command::new(&omp_path)
        .arg("-p")
        .arg(&prompt)
        .arg("--model")
        .arg(&model)
        .envs(env)""", """async fn generate_title(app: AppHandle, message: String, model: String) -> Result<String, String> {
    let (prog, mut args) = resolve_sidecar();
    let prompt = format!("Generate a title for a weather query that starts with this message. The title MUST be strictly formatted as '[Location] - [Topic]' (ensure the location includes a comma before the state), for example 'Denver, CO - Winter Snowfall Probability' or 'Miami, FL - Historical Hurricane Records'. Keep it succinct. Do not include quotes or any other text, just the title itself. Message: {}", message);
    args.extend(["-p".into(), prompt, "--model".into(), model]);

    let output = Command::new(&prog)
        .args(&args)
        .envs(sidecar_env(&app))""")

with open("desktop/src-tauri/src/lib.rs", "w") as f:
    f.write(text)
