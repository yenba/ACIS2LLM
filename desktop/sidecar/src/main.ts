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

  // Chat modes are implemented in Task 2.
  console.error("Error: chat mode not implemented yet");
  process.exit(1);
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
