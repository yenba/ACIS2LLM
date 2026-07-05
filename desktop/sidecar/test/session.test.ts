import { describe, expect, test } from "bun:test";
import { buildSession } from "../src/session";

describe("buildSession model selector parsing", () => {
  test("splits provider/model on the FIRST slash only (multi-slash model ids)", async () => {
    // OpenRouter model ids themselves contain slashes, e.g. "anthropic/claude-haiku-4.5",
    // so the full selector "openrouter/anthropic/claude-haiku-4.5" has two slashes.
    // Splitting on the wrong slash (e.g. lastIndexOf) would look up provider
    // "openrouter/anthropic" (invalid) instead of provider "openrouter",
    // model "anthropic/claude-haiku-4.5". buildSession resolves the model synchronously
    // against the local registry (no network/auth needed), so we can assert directly
    // on the resolved model's provider and id.
    const session = await buildSession("openrouter/anthropic/claude-haiku-4.5", { withTools: false });
    expect(session.model?.provider).toBe("openrouter");
    expect(session.model?.id).toBe("anthropic/claude-haiku-4.5");
  });

  test("rejects a selector with no slash", async () => {
    await expect(buildSession("no-slash-here", { withTools: false })).rejects.toThrow(
      "model not found: no-slash-here (expected provider/model-id)",
    );
  });

  test("rejects an unknown provider/model pair", async () => {
    await expect(
      buildSession("bogus-provider/bogus-model", { withTools: false }),
    ).rejects.toThrow("model not found: bogus-provider/bogus-model");
  });
});
