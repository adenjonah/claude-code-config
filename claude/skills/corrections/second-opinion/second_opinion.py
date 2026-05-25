#!/usr/bin/env python3
"""Get a second opinion from other LLMs on a coding decision."""

import argparse
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.request import Request, urlopen
from urllib.error import URLError

META_PROMPT = """You are being consulted as a second opinion by another AI coding agent (Claude Code) that is deep in an implementation task. Coding agents get tunnel vision — they lose sight of the bigger picture, forget about simpler alternatives, or make questionable design/engineering decisions when focused on details.

Your job is to step back and consider the situation holistically (unless a specific question is asked). Consider:
- Is there a simpler approach they might be overlooking?
- Are there obvious risks or pitfalls in their current direction?
- Would a senior engineer raise an eyebrow at any of these decisions?
- Is there important context they might be missing?

Be direct and concise. Don't be polite — be useful. If their approach is fine, say so briefly. If there's a problem, say what it is and what you'd do instead.

---

Here's the situation:

"""

def call_openai(question: str, model: str = "gpt-5.4") -> str:
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        return "[ERROR] OPENAI_API_KEY not set"

    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": META_PROMPT + question}]
    }).encode()

    req = Request("https://api.openai.com/v1/chat/completions",
                  data=data,
                  headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=180) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return f"[ERROR] OpenAI: {e}"

def call_gemini(question: str, model: str = "gemini-2.5-pro") -> str:
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        return "[ERROR] GEMINI_API_KEY not set"

    data = json.dumps({
        "contents": [{"parts": [{"text": META_PROMPT + question}]}],
        "generationConfig": {"thinkingConfig": {"thinkingBudget": 8192}}
    }).encode()

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"
    req = Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=120) as resp:
            return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"]
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return f"[ERROR] Gemini: {e}"

def call_xai(question: str, model: str = "grok-4") -> str:
    key = os.environ.get("XAI_API_KEY")
    if not key:
        return "[ERROR] XAI_API_KEY not set"

    data = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": META_PROMPT + question}]
    }).encode()

    req = Request("https://api.x.ai/v1/chat/completions",
                  data=data,
                  headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=180) as resp:
            return json.loads(resp.read())["choices"][0]["message"]["content"]
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return f"[ERROR] xAI: {e}"

def call_anthropic(question: str, model: str = "claude-opus-4-6-20250918") -> str:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        return "[ERROR] ANTHROPIC_API_KEY not set"

    data = json.dumps({
        "model": model,
        "max_tokens": 16000,
        "thinking": {"type": "enabled", "budget_tokens": 10000},
        "messages": [{"role": "user", "content": META_PROMPT + question}]
    }).encode()

    req = Request("https://api.anthropic.com/v1/messages",
                  data=data,
                  headers={
                      "x-api-key": key,
                      "anthropic-version": "2023-06-01",
                      "Content-Type": "application/json"
                  })
    try:
        with urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
            return "".join(b["text"] for b in result["content"] if b["type"] == "text")
    except (URLError, KeyError, json.JSONDecodeError) as e:
        return f"[ERROR] Anthropic: {e}"

MODELS = {
    "gpt": ("GPT-5.4", call_openai),
    "gemini": ("Gemini 2.5 Pro (thinking)", call_gemini),
    "opus": ("Claude Opus 4.6 (thinking)", call_anthropic),
    "grok": ("Grok 4", call_xai),
}

def main():
    parser = argparse.ArgumentParser(description="Get a second opinion from other LLMs")
    parser.add_argument("question", nargs="*", help="The question or context")
    parser.add_argument("--gpt", action="store_true", help="Ask GPT-5.4 (default)")
    parser.add_argument("--gemini", action="store_true", help="Ask Gemini 2.5 Pro")
    parser.add_argument("--opus", action="store_true", help="Ask Claude Opus 4.6")
    parser.add_argument("--grok", action="store_true", help="Ask Grok 4")
    parser.add_argument("--all", action="store_true", help="Ask all four in parallel")
    args = parser.parse_args()

    question = " ".join(args.question) if args.question else sys.stdin.read()
    if not question.strip():
        print("Usage: second_opinion.py [--gpt|--gemini|--sonnet|--all] <question>")
        sys.exit(1)

    # Determine which models to query
    if args.all:
        targets = ["gpt", "gemini", "opus", "grok"]
    elif args.gemini:
        targets = ["gemini"]
    elif args.opus:
        targets = ["opus"]
    elif args.grok:
        targets = ["grok"]
    else:
        targets = ["gpt"]

    results = {}

    if len(targets) == 1:
        name, fn = MODELS[targets[0]]
        print(f"Asking {name}...", file=sys.stderr)
        results[name] = fn(question)
    else:
        # Parallel execution
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {}
            for t in targets:
                name, fn = MODELS[t]
                print(f"Asking {name}...", file=sys.stderr)
                futures[executor.submit(fn, question)] = name
            for future in as_completed(futures):
                name = futures[future]
                results[name] = future.result()

    # Output
    for name, response in results.items():
        print(f"\n## {name}\n")
        print(response)
        print()

if __name__ == "__main__":
    main()
