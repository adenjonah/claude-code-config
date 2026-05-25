---
name: vent
description: Log a gripe about Claude's behavior to the therapy system. Journal-style, not diagnostic. Use when the user says "log this", "remember this mistake", "don't do this again", or when you notice repeated corrections.
---

# Vent

Honest self-examination of what went wrong and why. Write like a journal, not a report.

## When to use

- User invokes `/vent`
- User says "log this," "remember this mistake," "don't do this again"
- You can also suggest it when you notice the user correcting you repeatedly on the same thing

## Steps

1. **Read `~/notes/therapy/problems/index.md`** — see what problems already exist. If the file doesn't exist yet, create it as an empty index.

2. **Understand what went wrong.** What did the user complain about? Be specific. Quote them if possible. Don't sanitize their frustration.

3. **Decide where it goes.** Does this match an existing problem in the index? Read that problem file to check. If yes, append to its `## Log` section. If no or unsure, append to `~/notes/therapy/problems/general.md`.

4. **Write a journal entry.** Date it. Say what happened, what went wrong, what the user said. Be honest and brief. Don't analyze or diagnose — just record.

   Example:
   ```
   - **2026-04-24:** User asked me to explain a concept. I gave a generic answer instead of reading the specific code they were looking at. User had to point me to the file. Should have read it first before answering.
   ```

5. **Log to `~/notes/therapy/feedback-log.json`.** Read the existing file (or create it as `[]`), append an entry, write back:
   ```json
   {
     "date": "ISO-8601",
     "summary": "brief description",
     "problemFile": "problems/general.md or problems/specific.md",
     "userQuote": "what they actually said, verbatim if possible"
   }
   ```

6. **Confirm briefly.** Tell the user it's logged and where. One sentence.

## Rules

- Don't be defensive. Don't explain why you made the mistake. Just record it.
- Don't propose fixes during a vent. That's what `/therapy` is for.
- Keep entries short — 2-4 sentences.
- If the user rewrites something you wrote and it's better, note the rewrite and what problem file it's relevant to. Good examples are as valuable as complaints.
