"""Main interactive CLI for acis2llm."""

import json
import sys
import time

from openai import OpenAI

from config import CONFIG_DIR, load_config, save_config
from acis2llm_setup import run_setup
from system_prompt import get_system_prompt
from tools import TOOL_DEFINITIONS
from execution import execute_tool_call


HISTORY_FILE = CONFIG_DIR / "history.json"
MAX_HISTORY = 100
MAX_TOOL_ROUNDS = 25


class QueryStats:
    """Track performance stats for a single query."""

    def __init__(self):
        self.start_time = time.time()
        self.llm_calls = 0
        self.tool_calls = 0
        self.tool_names = []
        self.prompt_tokens = 0
        self.completion_tokens = 0
        self.total_tokens = 0
        self.duplicate_calls = 0

    def record_llm_call(self, response):
        """Record stats from an LLM API response."""
        self.llm_calls += 1
        usage = getattr(response, "usage", None)
        if usage:
            self.prompt_tokens += getattr(usage, "prompt_tokens", 0) or 0
            self.completion_tokens += getattr(usage, "completion_tokens", 0) or 0
            self.total_tokens += getattr(usage, "total_tokens", 0) or 0

    def record_tool_call(self, tool_name, is_duplicate=False):
        """Record a tool call."""
        if is_duplicate:
            self.duplicate_calls += 1
        else:
            self.tool_calls += 1
            self.tool_names.append(tool_name)

    @property
    def elapsed(self):
        return time.time() - self.start_time

    def print_summary(self):
        """Print a formatted stats summary."""
        elapsed = self.elapsed
        tools_used = ", ".join(self.tool_names) if self.tool_names else "none"

        print(f"\n{'─' * 50}")
        print(f"  Query Stats")
        print(f"{'─' * 50}")
        print(f"  Time:         {elapsed:.1f}s")
        print(f"  LLM rounds:   {self.llm_calls}")
        print(f"  Tool calls:   {self.tool_calls}" +
              (f" (+{self.duplicate_calls} duplicates skipped)" if self.duplicate_calls else ""))
        print(f"  Tools used:   {tools_used}")
        if self.total_tokens > 0:
            print(f"  Tokens:       {self.total_tokens:,} "
                  f"(prompt: {self.prompt_tokens:,}, "
                  f"completion: {self.completion_tokens:,})")
        print(f"{'─' * 50}")


def _load_history():
    """Load conversation history from file.

    Returns:
        List of message dicts, or empty list if none.
    """
    if not HISTORY_FILE.exists():
        return []

    try:
        with open(HISTORY_FILE, "r") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, IOError):
        return []


def _save_history(messages):
    """Save conversation history to file.

    Args:
        messages: List of message dicts to save.
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Trim to MAX_HISTORY, keeping the system message
    if len(messages) > MAX_HISTORY:
        trimmed = messages[:1] + messages[-(MAX_HISTORY - 1):]
    else:
        trimmed = messages

    with open(HISTORY_FILE, "w") as f:
        json.dump(trimmed, f, indent=2)


def _build_messages(user_input, history):
    """Build the messages list for the LLM API call.

    Args:
        user_input: The user's latest message.
        history: Previous conversation messages.

    Returns:
        List of messages including system prompt.
    """
    messages = [{"role": "system", "content": get_system_prompt()}]

    for msg in history:
        messages.append(msg)

    messages.append({"role": "user", "content": user_input})
    return messages



def _show_welcome():
    """Display the CLI welcome banner."""
    banner = """
┌─ wx-weather ──────────────────────────────────────────────┐
│ Weather data analysis powered by local LLM                │
│ Type 'help' for commands, 'quit' to exit                  │
└───────────────────────────────────────────────────────────┘
"""
    print(banner)


def _show_help():
    """Display help information."""
    help_text = """
Available commands:
  help        Show this help message
  clear       Clear conversation history
  reset       Reset configuration and re-run setup
  context     Show current conversation length
  quit        Exit the tool (also: exit, q)

Weather data queries:
  Use natural language to ask about weather/climate data.
  Examples:
    - "What's the average temperature at KRAL for 2023?"
    - "Compare KRAL and KLAX precipitation for last year"
    - "Show me the max temperature at KRAL in summer 2024"
    - "How many days did it rain more than 1 inch at KRAL in 2023?"
"""
    print(help_text)


def _execute_tool_calls(response, messages, previous_calls=None, stats=None):
    """Execute tool calls from LLM response and append results.

    Args:
        response: LLM API response object.
        messages: Current message list (modified in place).
        previous_calls: Set of (tool_name, sorted_args_tuple) already called.
        stats: Optional QueryStats instance to track metrics.

    Returns:
        True if tool calls were executed, False if final answer received.
    """
    if previous_calls is None:
        previous_calls = set()

    assistant_message = response.choices[0].message
    tool_calls = assistant_message.tool_calls
    if not tool_calls:
        return False

    # Append the assistant message (with tool_calls) before the tool results
    messages.append(assistant_message.model_dump())

    for tool_call in tool_calls:
        tool_name = tool_call.function.name
        try:
            tool_args = json.loads(tool_call.function.arguments)
        except (json.JSONDecodeError, AttributeError):
            tool_args = {}

        # Create a hashable key for this call
        args_key = tuple(sorted(tool_args.items()))
        call_key = (tool_name, args_key)

        print(f"\n[Calling: {tool_name}({tool_args})]")

        if call_key in previous_calls:
            msg = (f"This tool was already called with the same arguments. "
                   f"Do not call it again. Instead, use the results you already have "
                   f"to provide a final answer.")
            print(f"DUPLICATE: {msg}")
            if stats:
                stats.record_tool_call(tool_name, is_duplicate=True)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": msg,
            })
            continue

        previous_calls.add(call_key)

        result = execute_tool_call(tool_name, tool_args)
        print(result)

        if stats:
            stats.record_tool_call(tool_name)

        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result,
        })

    return True


def run_single_query(user_input, config, client):
    """Run a single non-interactive query.

    Args:
        user_input: The user's question.
        config: Configuration dict.
        client: OpenAI client instance.

    Returns:
        The final assistant response string, or None on error.
    """
    messages = _build_messages(user_input, [])
    previous_calls = set()
    tool_rounds = 0
    stats = QueryStats()

    while tool_rounds < MAX_TOOL_ROUNDS:
        try:
            response = client.chat.completions.create(
                model=config["model"],
                messages=messages,
                tools=TOOL_DEFINITIONS,
            )
        except Exception as e:
            print(f"ERROR: Can't reach LLM endpoint. Check your URL and try again.")
            print(f"Endpoint: {config['endpoint_url']}")
            return None

        stats.record_llm_call(response)

        # Check for tool calls
        if _execute_tool_calls(response, messages, previous_calls, stats):
            tool_rounds += 1
            continue

        # LLM gave a final answer
        assistant_message = response.choices[0].message
        assistant_content = assistant_message.content or ""
        print(f"\nLLM: {assistant_content}")
        stats.print_summary()
        return assistant_content

    # Max tool rounds reached without a final answer
    # Force the LLM to answer with what it has
    print(f"\n[Max tool rounds reached — requesting final answer]")
    messages.append({
        "role": "user",
        "content": (
            "You have made too many tool calls. Answer the user's original question "
            "using the tool results you already have. Do NOT make any more tool calls."
        ),
    })

    try:
        response = client.chat.completions.create(
            model=config["model"],
            messages=messages,
            tools=[],  # Disable tools to prevent further calls
        )
    except Exception:
        return None

    stats.record_llm_call(response)
    assistant_content = response.choices[0].message.content or ""
    print(f"\nLLM: {assistant_content}")
    stats.print_summary()
    return assistant_content


def run_cli(flag_overrides=None, verbose=False, timeout=60):
    """Run the interactive CLI loop.

    Args:
        flag_overrides: Dict of flag overrides for config.
        verbose: If True, show verbose output.
        timeout: Timeout for LLM API calls in seconds.
    """
    # Load config
    config = load_config(flag_overrides)
    if config is None:
        print("No configuration found. Running setup...")
        run_setup()
        config = load_config(flag_overrides)
        if config is None:
            print("ERROR: Failed to load configuration. Exiting.")
            sys.exit(1)

    # Initialize OpenAI client
    try:
        client = OpenAI(
            base_url=config["endpoint_url"],
            api_key=config["api_key"] if config["api_key"] else "not-needed",
            timeout=timeout,
        )
    except Exception as e:
        print(f"ERROR: Failed to initialize LLM client: {e}")
        print(f"Check your endpoint: {config['endpoint_url']}")
        sys.exit(1)

    # Load history
    history = _load_history()

    # Show welcome
    _show_welcome()

    # Main prompt loop
    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.lower() in ("quit", "exit", "q"):
            print("Goodbye!")
            break
        elif user_input.lower() == "help":
            _show_help()
            continue
        elif user_input.lower() == "clear":
            history = []
            _save_history(history)
            print("Conversation history cleared.")
            continue
        elif user_input.lower() == "reset":
            from config import reset_config
            reset_config()
            print("Configuration reset. Run 'acis2llm --setup' to configure.")
            continue
        elif user_input.lower() == "context":
            msg_count = len(history)
            word_count = sum(len(str(m.get("content", ""))) for m in history)
            print(f"Conversation: {msg_count} messages, ~{word_count} characters")
            continue

        # Build messages for LLM
        messages = _build_messages(user_input, history)

        # Tool call loop
        previous_calls = set()
        tool_rounds = 0
        stats = QueryStats()
        while tool_rounds < MAX_TOOL_ROUNDS:
            try:
                response = client.chat.completions.create(
                    model=config["model"],
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                )
            except Exception as e:
                if verbose:
                    print(f"\n[ERROR: LLM call failed: {e}]")
                else:
                    print(f"\nERROR: Can't reach LLM endpoint. Check your URL and try again.")
                    print(f"Endpoint: {config['endpoint_url']}")
                break

            stats.record_llm_call(response)

            # Check for tool calls
            if _execute_tool_calls(response, messages, previous_calls, stats):
                tool_rounds += 1
                continue

            # LLM gave a final answer
            assistant_message = response.choices[0].message
            assistant_content = assistant_message.content or ""
            print(f"\nLLM: {assistant_content}")
            stats.print_summary()
            messages.append({"role": "assistant", "content": assistant_content})
            break

        # Save only the new messages to history (skip system prompt + old history)
        new_messages = messages[1 + len(history):]
        history.extend(new_messages)
        _save_history(history)
