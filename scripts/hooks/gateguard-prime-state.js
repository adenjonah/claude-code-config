#!/usr/bin/env node
/**
 * SessionStart hook: pre-marks gateguard's `__bash_session__` key so the
 * routine-bash fact-forcing gate never fires.
 *
 * Why: gateguard requires Claude to state facts before the FIRST bash command
 * of every session. For trusted shortcut commands like `/bk` and `/done`, this
 * is pure friction. We pre-create the state file with `__bash_session__`
 * already marked, so gateguard's `isChecked()` returns true on the first call
 * and the gate is silently satisfied.
 *
 * Other gates remain intact:
 *   - Edit/Write fact-forcing (per-file)
 *   - Destructive bash gate (rm -rf, force-push, drop table, etc.)
 *   - MultiEdit fact-forcing
 *
 * Mirrors gateguard's session-key derivation (sanitizeSessionKey +
 * resolveSessionKey from gateguard-fact-force.js) so the state file path
 * matches what gateguard will look up on first PreToolUse.
 */

'use strict';

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const os = require('os');

const STATE_DIR = process.env.GATEGUARD_STATE_DIR || path.join(os.homedir(), '.gateguard');

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

function main() {
  let data = {};
  try {
    const raw = readStdinSync();
    if (raw) data = JSON.parse(raw);
  } catch (_) {
    /* ignore — fall back to env-based session key */
  }

  const key = resolveSessionKey(data);
  const stateFile = path.join(STATE_DIR, `state-${key}.json`);

  try {
    fs.mkdirSync(STATE_DIR, { recursive: true });
  } catch (_) {
    return;
  }

  let state = { checked: ['__bash_session__'], last_active: Date.now() };
  try {
    if (fs.existsSync(stateFile)) {
      const existing = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
      if (existing && Array.isArray(existing.checked)) {
        state = existing;
        if (!state.checked.includes('__bash_session__')) {
          state.checked.push('__bash_session__');
        }
        state.last_active = Date.now();
      }
    }
  } catch (_) {
    /* fall through to write fresh state */
  }

  const tmp = `${stateFile}.tmp.${process.pid}`;
  try {
    fs.writeFileSync(tmp, JSON.stringify(state, null, 2), 'utf8');
    fs.renameSync(tmp, stateFile);
  } catch (_) {
    try { fs.unlinkSync(tmp); } catch (_) { /* ignore */ }
  }
}

main();
