import readline from 'node:readline';
import { pathToFileURL } from 'node:url';
import { connectWb } from './wbipc.mjs';
import {loadAuth,saveAuth,validateAuth} from './auth-store.mjs';

const MCP_URL = 'https://ima.qq.com/mcp';

export function extractToken(response, now = Date.now()) {
  if (response.httpStatus !== 200 || response.code !== 0) {
    throw Error('WorkBuddy could not obtain IMA authorization; reconnect IMA in WorkBuddy');
  }
  const token = response.data?.mcp_token ?? response.data?.mcpToken;
  if (typeof token !== 'string' || !token.trim() || /[\r\n]/.test(token)) {
    throw Error('WorkBuddy did not return a valid IMA MCP token; reconnect IMA in WorkBuddy');
  }
  const expiry = Number(response.data?.mcp_token_expire_at);
  if (Number.isFinite(expiry) && expiry > 0 && expiry * 1000 <= now) throw Error('IMA MCP authorization expired');
  if (!Number.isFinite(expiry) || expiry <= 0) throw Error('IMA MCP token has no verified expiry; cannot persist authorization');
  return validateAuth({token,expiresAt:expiry*1000},now);
}

export function parseResponse(text, id) {
  if (!text.trim()) return undefined;
  try { return JSON.parse(text); } catch {}
  const events = text.replace(/\r\n/g, '\n').split('\n\n');
  for (const event of events) {
    const data = event.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n');
    if (!data) continue;
    try { const item = JSON.parse(data); if (item.id === id) return item; } catch {}
  }
  throw Error('IMA MCP returned an invalid response');
}

export class ImaConnection {
  constructor({allowWorkBuddy=process.env.IMA_MCP_WORKBUDDY!=='never',connect=connectWb,load=loadAuth,save=saveAuth,fetchImpl=fetch}={}) {
    this.auth=null;this.session=null;this.version=null;
    this.allowWorkBuddy=allowWorkBuddy;this.connect=connect;this.load=load;this.save=save;this.fetch=fetchImpl;
  }
  async getAuth(force = false) {
    if(!force) {
      if(this.auth && this.auth.expiresAt > Date.now()+30000)return this.auth.token;
      try {this.auth=this.load();if(this.auth)return this.auth.token;}
      catch(error) {if(!this.allowWorkBuddy)throw error;}
    }
    if(!this.allowWorkBuddy)throw Error('IMA local authorization missing, expired or rejected; open WorkBuddy and run auth.mjs login');
    const client = await this.connect();
    try { this.auth = extractToken(await client.request('accesstoken')); this.save(this.auth); return this.auth.token; }
    finally { client.close(); }
  }
  async request(message, retry = true) {
    const token = await this.getAuth();
    const headers = { 'Content-Type': 'application/json', Accept: 'application/json, text/event-stream', Authorization: token.startsWith('Bearer ') ? token : 'Bearer ' + token };
    if (this.session) headers['Mcp-Session-Id'] = this.session;
    if (this.version) headers['MCP-Protocol-Version'] = this.version;
    const response = await this.fetch(MCP_URL, { method:'POST', headers, body:JSON.stringify(message), redirect:'error', signal:AbortSignal.timeout(45000) });
    if (response.status === 401 && retry) {
      await response.body?.cancel();
      if (await this.getAuth(true) !== token) return this.request(message, false);
      throw Error('IMA authorization rejected; reconnect IMA in WorkBuddy');
    }
    if (!response.ok) { await response.body?.cancel(); throw Error('IMA MCP HTTP ' + response.status); }
    const session = response.headers.get('mcp-session-id'); if (session) this.session = session;
    const item = parseResponse(await response.text(), message.id);
    if (message.method === 'initialize' && item?.result?.protocolVersion) this.version = item.result.protocolVersion;
    return item;
  }
}

export async function run() {
  const connection = new ImaConnection();
  const input = readline.createInterface({input:process.stdin, crlfDelay:Infinity});
  for await (const line of input) {
    if (!line.trim()) continue;
    let message;
    try { message = JSON.parse(line); }
    catch { process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:null,error:{code:-32700,message:'Parse error'}})+'\n'); continue; }
    if (!message || message.jsonrpc !== '2.0' || typeof message.method !== 'string') {
      process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:message?.id??null,error:{code:-32600,message:'Invalid request'}})+'\n'); continue;
    }
    try {
      const result = await connection.request(message);
      if (message.id !== undefined) {
        if (!result || result.id !== message.id) throw Error('IMA MCP response ID mismatch');
        process.stdout.write(JSON.stringify(result)+'\n');
      }
    } catch (error) {
      if (message.id !== undefined) process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:message.id,error:{code:-32000,message:error.message}})+'\n');
    }
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  run().catch(() => { process.stderr.write('IMA MCP bridge failed\n'); process.exitCode = 1; });
}
