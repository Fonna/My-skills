import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

export function authPath() {
  return process.env.IMA_MCP_AUTH_FILE || path.join(process.env.CODEX_HOME || path.join(os.homedir(),'.codex'),'ima-mcp','auth.dpapi.json');
}

export function dpapi(operation, input) {
  if (process.platform !== 'win32') throw Error('Encrypted authorization storage currently supports Windows only');
  const executable=path.join(process.env.SystemRoot || 'C:/Windows','System32/WindowsPowerShell/v1.0/powershell.exe');
  const script=fileURLToPath(new URL('./dpapi.ps1',import.meta.url));
  const result=spawnSync(executable,['-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',script,operation],{input,encoding:'utf8',windowsHide:true,timeout:15000,maxBuffer:1024*1024});
  if (result.error || result.status !== 0) throw Error('Cannot access encrypted IMA authorization for this Windows user; run auth.mjs login');
  return result.stdout.trim();
}

export function validateAuth(value, now=Date.now()) {
  if (!value || typeof value.token !== 'string' || !value.token.trim() || /[\r\n]/.test(value.token) || !Number.isFinite(value.expiresAt)) throw Error('Invalid IMA authorization');
  if (value.expiresAt <= now+30000) throw Error('IMA authorization expired; run auth.mjs login with WorkBuddy running');
  return value;
}

export function loadAuth(filename=authPath(), now=Date.now()) {
  if (!fs.existsSync(filename)) return null;
  let envelope;
  try { envelope=JSON.parse(fs.readFileSync(filename,'utf8')); }
  catch { throw Error('Cannot read IMA authorization cache; run auth.mjs login'); }
  if (envelope.version !== 1 || typeof envelope.encrypted !== 'string') throw Error('Unsupported IMA authorization cache');
  let value;
  try { value=JSON.parse(dpapi('unprotect',envelope.encrypted)); }
  catch { throw Error('Cannot decrypt IMA authorization for this Windows user; run auth.mjs login'); }
  return validateAuth(value,now);
}

export function saveAuth(value, filename=authPath()) {
  validateAuth(value);
  const encrypted=dpapi('protect',JSON.stringify(value));
  fs.mkdirSync(path.dirname(filename),{recursive:true});
  const temporary=filename+'.'+process.pid+'.tmp';
  try {
    fs.writeFileSync(temporary,JSON.stringify({version:1,encrypted})+'\n',{flag:'wx',mode:0o600});
    fs.renameSync(temporary,filename);
  } finally { if (fs.existsSync(temporary)) fs.unlinkSync(temporary); }
}
