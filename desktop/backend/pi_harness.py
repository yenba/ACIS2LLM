#!/usr/bin/env python3
"""
Embedded Pi Harness (Sidecar Prototype)
Replaces `omp` CLI with a local Python process.
"""

import sys
import json
import argparse
from typing import List, Dict, Any

def print_json_event(event_type: str, data: Dict[str, Any]):
    payload = {"type": event_type}
    payload.update(data)
    print(json.dumps(payload), flush=True)

def handle_chat_json(prompt: str, model: str):
    print_json_event("tool_execution_start", {
        "toolName": "acis2llm_integration",
        "intent": "Initializing Pi embedded harness..."
    })
    
    print_json_event("agent_end", {
        "messages": [
            {
                "role": "assistant",
                "content": [
                    {
                        "type": "text",
                        "text": f"Embedded Pi Harness (Model: {model}) received: {prompt[:30]}...\n\nIntegrating ACIS tools natively!"
                    }
                ]
            }
        ]
    })

def handle_chat_text(prompt: str, model: str):
    # Just output the text response directly (used for generate_title)
    print(f"Mock City, ST - Mocked Weather Topic")

def main():
    parser = argparse.ArgumentParser(description="Embedded Pi Harness")
    parser.add_argument("-p", "--prompt", type=str, help="Full prompt string")
    parser.add_argument("--model", type=str, help="Model selector")
    parser.add_argument("--mode", type=str, default="text", help="Output mode (e.g., json)")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    
    args = parser.parse_args()
    
    if args.list_models:
        print(json.dumps({
            "models": [
                {"id": "pi/embedded", "selector": "pi/embedded", "name": "Pi Embedded Harness", "provider": "pi.dev"}
            ]
        }))
        sys.exit(0)
        
    if not args.prompt or not args.model:
        print("Error: --prompt and --model are required", file=sys.stderr)
        sys.exit(1)
        
    if args.mode == "json":
        handle_chat_json(args.prompt, args.model)
    else:
        handle_chat_text(args.prompt, args.model)

if __name__ == "__main__":
    main()
