"""First-run setup wizard for acis2llm."""

from config import CONFIG_DIR, save_config


DEFAULT_ENDPOINT = "http://localhost:11434/v1"


def _prompt_with_default(prompt_text, default=None):
    """Prompt user with optional default value."""
    if default is not None:
        display = f"{prompt_text} [{default}]"
    else:
        display = prompt_text

    value = input(display + " > ").strip()
    if not value and default is not None:
        return default
    return value if value else None


def _fetch_models(endpoint_url):
    """Fetch available models from the endpoint.

    Args:
        endpoint_url: OpenAI-compatible API endpoint URL.

    Returns:
        List of model dicts, or None on error.
    """
    import requests

    try:
        resp = requests.get(endpoint_url.rstrip("/") + "/models", timeout=10)
        resp.raise_for_status()
        data = resp.json()
        models = data.get("data", [])
        if not models:
            print("No models returned from endpoint.")
            return []
        return [(m["id"], m) for m in models]
    except requests.exceptions.ConnectionError:
        print(f"Connection refused. Check that {endpoint_url} is correct and the server is running.")
        return None
    except requests.exceptions.Timeout:
        print(f"Connection timed out. Check that {endpoint_url} is reachable.")
        return None
    except Exception as e:
        print(f"Error fetching models: {e}")
        return None


def run_setup():
    """Run interactive setup wizard."""
    print("=" * 60)
    print("  acis2llm — Weather Data Analysis CLI")
    print("=" * 60)
    print()

    # Step 1: Endpoint URL
    endpoint = _prompt_with_default(
        "OpenAI-compatible endpoint URL", DEFAULT_ENDPOINT
    )
    print()

    # Step 2: Fetch and display models
    print("Fetching available models...")
    models = _fetch_models(endpoint)
    if models is None:
        print()
        print("Could not connect to endpoint. You can still continue,")
        print("but you'll need to manually specify a model name.\n")
        models = []

    if models:
        print("\nAvailable models:")
        for i, (model_id, _) in enumerate(models, 1):
            print(f"  {i}. {model_id}")
        print()

        model_choice = _prompt_with_default(
            "Select a model by number (or type custom)",
        )

        if model_choice and model_choice.strip().isdigit():
            idx = int(model_choice.strip()) - 1
            if 0 <= idx < len(models):
                model = models[idx][0]
            else:
                model = _prompt_with_default("Enter model name")
        else:
            model = model_choice
    else:
        model = _prompt_with_default("Enter model name")

    # Step 3: API key
    print()
    api_key = _prompt_with_default(
        "API key (leave empty if not required)", None
    )

    # Save config
    config = {
        "endpoint_url": endpoint,
        "api_key": api_key or "",
        "model": model,
    }
    save_config(config)

    print()
    print("Configuration saved to", CONFIG_DIR / "config.yaml")
    print()
    print("You can now run 'acis2llm' to start chatting.")
    print("Use --endpoint, --model, --api-key flags to override config.")


if __name__ == "__main__":
    run_setup()
