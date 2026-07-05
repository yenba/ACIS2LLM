import { AuthStorage, ModelRegistry } from "@earendil-works/pi-coding-agent";

export interface ModelEntry {
  id: string;
  selector: string;
  name: string;
  provider: string;
}

export async function listModels(): Promise<{ models: ModelEntry[] }> {
  const authStorage = AuthStorage.create();
  const registry = ModelRegistry.create(authStorage);
  // Only models whose provider has a usable API key (env var or ~/.pi auth).
  // Note: getAvailable() is synchronous in the installed SDK version, not async
  // as shown in the brief; awaiting a non-promise value is a harmless no-op.
  const available = registry.getAvailable();
  const models = available.map((m) => ({
    id: m.id,
    selector: `${m.provider}/${m.id}`,
    name: m.name ?? m.id,
    provider: m.provider,
  }));
  return { models };
}
