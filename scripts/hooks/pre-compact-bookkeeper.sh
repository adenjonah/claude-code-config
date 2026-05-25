#!/bin/bash
# PreCompact hook: Prompt Claude to run the bookkeeper before context compaction.
# Fires automatically when context is running low (~20-30% remaining).

echo "SYSTEM [pre-compact-bookkeeper]: Context window is approaching compaction. You MUST invoke the bookkeeper agent NOW with a full summary of everything done in this session before compaction occurs. If you skip this, session work will be lost from the vault. Invoke it immediately, then continue."

exit 0
