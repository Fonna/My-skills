import fs from 'node:fs';
import net from 'node:net';
import crypto from 'node:crypto';
import os from 'node:os';
import path from 'node:path';

export async function connectWb(discoveryPath = path.join(process.env.WORKBUDDY_CONFIG_DIR || path.join(os.homedir(), '.workbuddy'),'wbipc/endpoint.json')) {
  let discovery;
  try {discovery=JSON.parse(fs.readFileSync(discoveryPath,'utf8'));}
  catch {throw Error('WorkBuddy authorization interface unavailable; start WorkBuddy, log in and connect IMA');}
  const {endpoint,ticket}=discovery;
  if (typeof endpoint!=='string' || !endpoint.startsWith('\\\\.\\pipe\\wbipc-') || typeof ticket!=='string' || !ticket) throw Error('Unexpected WorkBuddy IPC discovery data');
  const nonce = crypto.randomBytes(16).toString('base64url');
  const socket = net.connect(endpoint);
  let buffer = '', sequence = 0, state = 'hello';
  const pending = new Map();
  let readyResolve, readyReject;
  const ready = new Promise((resolve, reject) => { readyResolve = resolve; readyReject = reject; });
  const send = frame => socket.write(JSON.stringify(frame) + '\n');
  const proof = (role, frame) => {
    const fields = [role === 'server' ? 'wbipc-s' : 'wbipc-c', '1', endpoint, nonce, frame.server_nonce];
    return crypto.createHmac('sha256', ticket).update(Buffer.concat(fields.flatMap(value => {
      const b = Buffer.from(value), length = Buffer.alloc(4); length.writeUInt32BE(b.length); return [length,b];
    }))).digest('base64url');
  };
  const fail = error => { readyReject(error); for (const p of pending.values()) p.reject(error); pending.clear(); socket.destroy(); };
  const handshakeTimer=setTimeout(()=>fail(Error('WorkBuddy IPC handshake timed out')),5000);
  socket.setTimeout(15000, () => fail(Error('IPC timeout; ensure WorkBuddy is running and logged in')));
  socket.on('error', () => fail(Error('Cannot connect to WorkBuddy; start WorkBuddy and log in')));
  socket.on('close', () => {clearTimeout(handshakeTimer);fail(Error('IPC connection closed'));});
  socket.on('connect', () => send({type:'session_hello',protocol_min:1,protocol_max:1,client_nonce:nonce,ticket_id:crypto.createHash('sha256').update(ticket).digest('hex').slice(0,16),client:{kind:'codex',id:'ima-mcp',version:'1.0.0'}}));
  socket.setEncoding('utf8');
  socket.on('data', data => {
    buffer += data.toString('utf8');
    if (buffer.length > 2_000_000) return fail(Error('IPC frame too large'));
    while (buffer.includes('\n')) {
      const pos = buffer.indexOf('\n'), line = buffer.slice(0,pos); buffer = buffer.slice(pos+1);
      if (!line) continue;
      try {
        const frame = JSON.parse(line);
        if (frame.type === 'session_challenge') {
          if(state!=='hello'||frame.protocol!==1||typeof frame.server_nonce!=='string')throw Error('Invalid IPC handshake');
          const expected = Buffer.from(proof('server',frame)), actual = Buffer.from(frame.server_proof || '');
          if (actual.length !== expected.length || !crypto.timingSafeEqual(expected,actual)) throw Error('Invalid IPC server proof');
          state='prove';
          send({type:'session_prove',client_proof:proof('client',frame)});
        } else if (frame.type === 'session_hello_ack') {
          if(state!=='prove'||frame.protocol!==1)throw Error('Unauthenticated IPC acknowledgement');
          state='ready';clearTimeout(handshakeTimer);readyResolve(frame);
        }
        else if (frame.type === 'session_hello_error') throw Error('IPC handshake rejected: '+frame.code);
        else if (pending.has(frame.id)) { const p=pending.get(frame.id); pending.delete(frame.id); frame.error ? p.reject(Error('WorkBuddy IPC request rejected')) : p.resolve(frame.result); }
      } catch (error) { fail(error); }
    }
  });
  try { await ready; } catch (error) { socket.destroy(); throw error; }
  const rpc = (method,params,mode) => new Promise((resolve,reject) => { const id=++sequence; pending.set(id,{resolve,reject}); send({jsonrpc:'2.0',id,method,params,...mode?{mode}:{}}); });
  let channel;
  try { channel = await rpc('broker/GetPipe',{pipe:'wb.request'}); }
  catch (error) { socket.destroy(); throw error; }
  return {
    async request(action) {
      if (!['status','accesstoken'].includes(action)) throw Error('Unsupported action');
      const params={method:'GET',path:'/v2/as/connector/oauth/ima/'+action,headers:{'accept':'application/json'}};
      const result=await rpc(channel.channel+'/http.fetch',params,'call');
      const decoded=JSON.parse(Buffer.from(result.body_b64,'base64').toString('utf8'));
      return {...decoded,httpStatus:result.status};
    },
    close() { socket.destroy(); }
  };
}
