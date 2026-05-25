#!/usr/bin/env node
/**
 * PreToolUse hook: pre-marks files with skip-listed extensions in gateguard's
 * state file so gateguard's fact-forcing gate never fires for them.
 *
 * Why: gateguard's investigation prompt (importers, public API, data schema) is
 * pure friction for markdown notes, plain text, SVG assets, and config files.
 * Pre-marking the file path makes gateguard's `isChecked()` return true on
 * first call → silent allow.
 *
 * How it works:
 *   1. Read the PreToolUse hook input from stdin.
 *   2. For Edit/Write/MultiEdit, extract candidate file paths.
 *   3. If a path's extension is in the skip list, append it to the same state
 *      file gateguard reads (~/.gateguard/state-<session-key>.json).
 *   4. Always exit 0 with no permissionDecision (i.e. allow). Gateguard runs
 *      next, sees the path already marked, and short-circuits without firing
 *      the gate.
 *
 * Configurable via env var:
 *   GATEGUARD_SKIP_EXTENSIONS — comma-separated list of extensions
 *     (default: .md,.txt,.svg,.json,.yml,.yaml,.csv,.tex,.aux,.log,.bbl,.toc)
 *
 * Other gateguard gates remain intact:
 *   - Edit/Write/MultiEdit on code files (.ts, .tsx, .js, .py, .swift, etc.)
 *   - Destructive bash gate (rm -rf, force-push, drop table, etc.)
 *   - Routine bash gate (already silenced by gateguard-prime-state.js)
 *
 * Mirrors gateguard's session-key derivation (resolveSessionKey from
 * gateguard-fact-force.js) so the state file path matches what gateguard
 * will look up.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');

const STATE_DIR = process.env.GATEGUARD_STATE_DIR || path.join(os.homedir(), '.gateguard');
const DEFAULT_SKIP_EXTENSIONS = '.md,.txt,.svg,.json,.yml,.yaml,.csv,.tex,.aux,.log,.bbl,.toc';

function getSkipExtensions() {
  const raw = process.env.GATEGUARD_SKIP_EXTENSIONS || DEFAULT_SKIP_EXTENSIONS;
  return raw.split(',').map(e => e.trim().toLowerCase()).filter(Boolean);
}

function hashSessionKey(prefix, value) {
  return `${prefix}-${crypto.createHash('sha256').update(String(value)).digest('hex').slice(0, 24)}`;
}

function sanitizeSessionKey(value) {
  const raw = String(value || '').trim();
  if (!raw) return '';
  const sanitized = raw.replace(/[^a-zA-Z0-9_-]/g, '_');
  if (sanitized && sanitized.length <= 64) return sanitized;
  return hashSessionKey('sid', raw);
}

function resolveSessionKey(data) {
  const candidates = [
    data && data.session_id,
    data && data.sessionId,
    data && data.session && data.session.id,
    process.env.CLAUDE_SESSION_ID,
    process.env.ECC_SESSION_ID
  ];
  for (const c of candidates) {
    const k = sanitizeSessionKey(c);
    if (k) return k;
  }
  const tx = (data && (data.transcript_path || data.transcriptPath)) || process.env.CLAUDE_TRANSCRIPT_PATH;
  if (tx && String(tx).trim()) {
    return hashSessionKey('tx', path.resolve(String(tx).trim()));
  }
  return hashSessionKey('proj', path.resolve(process.env.CLAUDE_PROJECT_DIR || process.cwd()));
}

function readStdinSync() {
  try {
    return fs.readFileSync(0, 'utf8');
  } catch (_) {
    return '';
  }
}

function hasSkipExtension(filePath, skipExts) {
  if (!filePath) return false;
  const lower = String(filePath).toLowerCase();
  return skipExts.some(ext => lower.endsWith(ext));
}

function collectPaths(toolName, toolInput) {
  const name = String(toolName || '').toLowerCase();
  if (name === 'edit' || name === 'write') {
    return toolInput && toolInput.file_path ? [toolInput.file_path] : [];
  }
  if (name === 'multiedit') {
    const edits = (toolInput && toolInput.edits) || [];
    return edits.map(e => e && e.file_path).filter(Boolean);
  }
  return [];
}

(function main() {
  let data = {};
  try {
    const raw = readStdinSync();
    if (raw) data = JSON.parse(raw);
  } catch (_) {
    return; // allow on parse error
  }

  const skipExts = getSkipExtensions();
  if (skipExts.length === 0) return;

  const paths = collectPaths(data.tool_name, data.tool_input)
    .filter(p => hasSkipExtension(p, skipExts));
  if (paths.length === 0) return;

  const key = resolveSessionKey(data);
  const stateFile = path.join(STATE_DIR, `state-${key}.json`);

  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
  } catch (_) {
    return;
  }

  let state = { checked: [], last_active: Date.now() };
  try {
    if (fs.existsSync(stateFile)) {
      const existing = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
      if (existing && Array.isArray(existing.checked)) {
        state = existing;
      }
    }
  } catch (_) {
    /* fall through to fresh state */
  }

  let changed = false;
  for (const p of paths) {
    if (!state.checked.includes(p)) {
      state.checked.push(p);
      changed = true;
    }
  }
  if (!changed) return;

  state.last_active = Date.now();
  const tmp = `${stateFile}.tmp.${process.pid}`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(state, null, 2), 'utf8');
    fs.renameSync(tmp, stateFile);
  } catch (_) {
    try { fs.unlinkSync(tmp); } catch (_) { /* ignore */ }
  }
})();
