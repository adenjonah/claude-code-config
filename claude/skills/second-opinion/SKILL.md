---
name: second-opinion
description: Get a different perspective from other LLMs (GPT, Gemini, Grok) on design decisions, architecture, debugging, or judgment calls. Use when deep in a problem and might have tunnel vision.
user-invocable: true
---

# Second Opinion

Get an outside perspective from another LLM when you're deep in a problem and might have tunnel vision.

## Usage

```
/second-opinion Should I use WebSockets or SSE for streaming?
/second-opinion --gemini Is this schema going to scale?
/second-opinion --all What's the best approach here?
```

## How to Execute

Run the Python script:

```bash
# Default (GPT)
python3 ~/.claude/skills/corrections/second-opinion/second_opinion.py "the question or context here"

# Gemini
python3 ~/.claude/skills/corrections/second-opinion/second_opinion.py --gemini "the question"

# All in parallel
python3 ~/.claude/skills/corrections/second-opinion/second_opinion.py --all "the question"

# Pipe context in
echo "context here" | python3 ~/.claude/skills/corrections/second-opinion/second_opinion.py --all
```

Include relevant context — code snippets, the decision at hand, what you've already considered.

Present the output to the user, then add your own synthesis: where the models agree, where they disagree, what you'd recommend.

## Setup (one-time)

Add API keys to `~/.zshrc` for whichever models you want:

```bash
export OPENAI_API_KEY="sk-..."
export GEMINI_API_KEY="AI..."
export ANTHROPIC_API_KEY="sk-ant-..."
```

Works with any subset — only the models with keys will be queried.
