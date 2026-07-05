export interface CliArgs {
  prompt?: string;
  model?: string;
  mode: "text" | "json";
  listModels: boolean;
}

export function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { mode: "text", listModels: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case "-p":
      case "--prompt":
        args.prompt = argv[++i];
        break;
      case "--model":
        args.model = argv[++i];
        break;
      case "--mode":
        args.mode = argv[++i] === "json" ? "json" : "text";
        break;
      case "--list-models":
        args.listModels = true;
        break;
    }
  }
  return args;
}
