undef $/;
$_ = <>;
s/let env = get_expanded_env\(\);\n\s*\/\/ Spawn `omp -p <full_prompt> --model <model> --mode json`\n\s*\/\/ JSON mode emits structured events \(tool calls, text deltas\) that\n\s*\/\/ let us show real-time progress in the UI during the TTFT wait.\n\s*let mut child = Command::new\(&omp_path\)\n\s*\.arg\("-p"\)\n\s*\.arg\(&full_prompt\)\n\s*\.arg\("--model"\)\n\s*\.arg\(&model\)\n\s*\.arg\("--mode"\)\n\s*\.arg\("json"\)\n\s*\.envs\(env\)/args.extend(["-p", &full_prompt, "--model", &model, "--mode", "json"].map(String::from));\n    let mut child = Command::new(&prog)\n        .args(&args)\n        .envs(sidecar_env(&app))/s;
print;
