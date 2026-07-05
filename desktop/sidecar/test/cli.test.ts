import { describe, expect, test } from "bun:test";
import { parseArgs } from "../src/cli";

describe("parseArgs", () => {
  test("parses json chat invocation", () => {
    expect(parseArgs(["-p", "hi there", "--model", "anthropic/claude-sonnet-5", "--mode", "json"])).toEqual({
      prompt: "hi there",
      model: "anthropic/claude-sonnet-5",
      mode: "json",
      listModels: false,
    });
  });

  test("defaults to text mode", () => {
    const args = parseArgs(["-p", "title please", "--model", "anthropic/claude-haiku-4-5"]);
    expect(args.mode).toBe("text");
  });

  test("parses --list-models", () => {
    expect(parseArgs(["--list-models"]).listModels).toBe(true);
  });

  test("accepts --prompt long form", () => {
    expect(parseArgs(["--prompt", "x", "--model", "m"]).prompt).toBe("x");
  });
});
