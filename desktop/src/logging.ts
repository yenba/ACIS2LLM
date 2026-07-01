import { warn, debug, trace, info, error } from "@tauri-apps/plugin-log";

type LogFn = (message: string) => Promise<void>;

// Route the browser console into tauri-plugin-log so frontend logs land in the
// same file as the Rust backend logs. The original console output is preserved
// (so devtools still work), and forwarding failures are swallowed to avoid
// recursive logging or crashes when running outside the Tauri webview.
function forwardConsole(
  fnName: "log" | "debug" | "info" | "warn" | "error",
  logger: LogFn
) {
  const original = console[fnName];
  console[fnName] = (...args: unknown[]) => {
    original(...args);
    try {
      const message = args
        .map((a) => {
          if (typeof a === "string") return a;
          try {
            return JSON.stringify(a);
          } catch {
            return String(a);
          }
        })
        .join(" ");
      logger(message).catch(() => {});
    } catch {
      /* never let logging break the app */
    }
  };
}

export function setupLogging() {
  forwardConsole("log", trace);
  forwardConsole("debug", debug);
  forwardConsole("info", info);
  forwardConsole("warn", warn);
  forwardConsole("error", error);
}
