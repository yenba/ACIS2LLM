import { parseArgs } from "./cli";
import { listModels } from "./models";

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.listModels) {
    const result = await listModels();
    console.log(JSON.stringify(result));
    return;
  }

  if (!args.prompt || !args.model) {
    console.error("Error: --prompt and --model are required");
    process.exit(1);
  }

  if (args.mode === "json") {
    const { runJson } = await import("./run");
    await runJson(args.prompt, args.model);
  } else {
    const { runText } = await import("./run");
    await runText(args.prompt, args.model);
  }
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
