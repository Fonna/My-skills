import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {spawnSync} from 'node:child_process';
import {fileURLToPath} from 'node:url';

export function credentialPath() {
  return path.join(process.env.CODEX_HOME || path.join(os.homedir(), '.codex'), 'ima-duo-mcp', 'credentials.dpapi.json');
}
export function validateCredentials(value) {
  if (!value || !['clientId','apiKey'].every(k => typeof value[k] === 'string' && value[k].trim() && value[k].length <= 4096 && !/[\r\n\x00]/.test(value[k]))) {
    throw Error('Client ID 和 API Key 格式不正确');
  }
  return {clientId:value.clientId.trim(),apiKey:value.apiKey.trim()};
}
export function readEnvironmentCredentials(clientId) {
  const script=fileURLToPath(new URL('./read-env.ps1',import.meta.url));
  const executable=path.join(process.env.SystemRoot || 'C:/Windows','System32/WindowsPowerShell/v1.0/powershell.exe');
  const r=spawnSync(executable,['-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',script],{encoding:'utf8',windowsHide:true,timeout:15000,maxBuffer:65536});
  if(r.error||r.status!==0)throw Error('无法读取 ima 环境变量');
  let values;
  try {values=JSON.parse(r.stdout);}catch{throw Error('无法读取 ima 环境变量');}
  return validateCredentials({clientId:clientId||values.IMA_OPENAPI_CLIENTID||values.IMA_CLIENT_ID,apiKey:values.IMA_OPENAPI_APIKEY||values.IMA_API_KEY});
}
function protect(operation, input) {
  if (process.platform !== 'win32') throw Error('本接入包使用 Windows DPAPI');
  const executable=path.join(process.env.SystemRoot || 'C:/Windows','System32/WindowsPowerShell/v1.0/powershell.exe');
  const script=fileURLToPath(new URL('./dpapi.ps1',import.meta.url));
  const r=spawnSync(executable,['-NoLogo','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',script,operation],{input,encoding:'utf8',windowsHide:true,timeout:15000,maxBuffer:65536});
  if (r.error || r.status !== 0) throw Error('无法访问当前 Windows 用户的加密凭证');
  return r.stdout.trim();
}
export function loadCredentials(filename=credentialPath()) {
  try {
    const envelope=JSON.parse(fs.readFileSync(filename,'utf8'));
    if (envelope.version !== 1 || typeof envelope.encrypted !== 'string') throw Error();
    return validateCredentials(JSON.parse(protect('unprotect',envelope.encrypted)));
  } catch { throw Error('ima-duo 尚未授权或缓存不可读，请运行 auth.mjs login'); }
}
export function saveCredentials(value, filename=credentialPath()) {
  const credentials=validateCredentials(value);
  const encrypted=protect('protect',JSON.stringify(credentials));
  fs.mkdirSync(path.dirname(filename),{recursive:true});
  const temporary=filename+'.'+process.pid+'.tmp';
  try {
    fs.writeFileSync(temporary,JSON.stringify({version:1,encrypted})+'\n',{flag:'wx',mode:0o600});
    fs.renameSync(temporary,filename);
  } finally { if (fs.existsSync(temporary)) fs.unlinkSync(temporary); }
}
