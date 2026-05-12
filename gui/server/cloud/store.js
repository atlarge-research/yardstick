const fs = require('fs');
const path = require('path');
const os = require('os');
const crypto = require('crypto');

const BASE_DIR = path.join(os.homedir(), '.yardstick-gui');
const CONFIG_PATH = path.join(BASE_DIR, 'cloud.json');
const KEY_PATH = path.join(BASE_DIR, '.master.key');
const KEYS_DIR = path.join(BASE_DIR, 'keys');

function ensureBaseDir() {
  if (!fs.existsSync(BASE_DIR)) fs.mkdirSync(BASE_DIR, { recursive: true, mode: 0o700 });
  if (!fs.existsSync(KEYS_DIR)) fs.mkdirSync(KEYS_DIR, { recursive: true, mode: 0o700 });
}

function loadMasterKey() {
  ensureBaseDir();
  if (fs.existsSync(KEY_PATH)) return fs.readFileSync(KEY_PATH);
  const key = crypto.randomBytes(32);
  fs.writeFileSync(KEY_PATH, key, { mode: 0o600 });
  return key;
}

function encrypt(plaintext) {
  const key = loadMasterKey();
  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
  const enc = Buffer.concat([cipher.update(plaintext, 'utf8'), cipher.final()]);
  const tag = cipher.getAuthTag();
  return Buffer.concat([iv, tag, enc]).toString('base64');
}

function decrypt(payload) {
  const key = loadMasterKey();
  const buf = Buffer.from(payload, 'base64');
  const iv = buf.subarray(0, 12);
  const tag = buf.subarray(12, 28);
  const enc = buf.subarray(28);
  const decipher = crypto.createDecipheriv('aes-256-gcm', key, iv);
  decipher.setAuthTag(tag);
  return Buffer.concat([decipher.update(enc), decipher.final()]).toString('utf8');
}

function readConfig() {
  ensureBaseDir();
  if (!fs.existsSync(CONFIG_PATH)) return { aws: { profiles: {} }, azure: { profiles: {} } };
  try {
    const raw = fs.readFileSync(CONFIG_PATH, 'utf8');
    const obj = JSON.parse(raw);
    obj.aws ||= { profiles: {} };
    obj.azure ||= { profiles: {} };
    return obj;
  } catch {
    return { aws: { profiles: {} }, azure: { profiles: {} } };
  }
}

function writeConfig(obj) {
  ensureBaseDir();
  fs.writeFileSync(CONFIG_PATH, JSON.stringify(obj, null, 2), { mode: 0o600 });
}

function listProfiles(provider) {
  const cfg = readConfig();
  const profiles = cfg[provider]?.profiles || {};
  return Object.entries(profiles).map(([id, p]) => ({
    id,
    name: p.meta?.name || id,
    defaultRegion: p.meta?.defaultRegion || null,
    accountId: p.meta?.accountId || null,
    createdAt: p.meta?.createdAt || null,
  }));
}

function saveProfile(provider, id, secrets, meta) {
  const cfg = readConfig();
  cfg[provider] ||= { profiles: {} };
  cfg[provider].profiles[id] = {
    encrypted: encrypt(JSON.stringify(secrets)),
    meta: { ...meta, createdAt: meta?.createdAt || new Date().toISOString() },
  };
  writeConfig(cfg);
}

function loadProfile(provider, id) {
  const cfg = readConfig();
  const entry = cfg[provider]?.profiles?.[id];
  if (!entry) return null;
  return { secrets: JSON.parse(decrypt(entry.encrypted)), meta: entry.meta };
}

function deleteProfile(provider, id) {
  const cfg = readConfig();
  if (cfg[provider]?.profiles?.[id]) {
    delete cfg[provider].profiles[id];
    writeConfig(cfg);
    return true;
  }
  return false;
}

function saveKeyMaterial(provider, profileId, keyName, privateKeyPem) {
  ensureBaseDir();
  const dir = path.join(KEYS_DIR, provider, profileId);
  fs.mkdirSync(dir, { recursive: true, mode: 0o700 });
  const file = path.join(dir, `${keyName}.pem`);
  fs.writeFileSync(file, privateKeyPem, { mode: 0o600 });
  return file;
}

function loadKeyMaterial(provider, profileId, keyName) {
  const file = path.join(KEYS_DIR, provider, profileId, `${keyName}.pem`);
  if (!fs.existsSync(file)) return null;
  return fs.readFileSync(file, 'utf8');
}

function listKeyMaterial(provider, profileId) {
  const dir = path.join(KEYS_DIR, provider, profileId);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((n) => n.endsWith('.pem'))
    .map((n) => n.slice(0, -4));
}

module.exports = {
  listProfiles,
  saveProfile,
  loadProfile,
  deleteProfile,
  saveKeyMaterial,
  loadKeyMaterial,
  listKeyMaterial,
};
