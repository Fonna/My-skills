import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import crypto from 'node:crypto';
import {connectWb} from '../scripts/wbipc.mjs';

async function broker(mode, callback) {
  const endpoint='\\\\.\\pipe\\wbipc-ima-test-'+crypto.randomBytes(8).toString('hex'),ticket='synthetic-ticket';
  const dir=await fs.mkdtemp(path.join(os.tmpdir(),'ima-wbipc-test-')),discovery=path.join(dir,'endpoint.json');
  await fs.writeFile(discovery,JSON.stringify({endpoint,ticket}));
  const sockets=new Set();
  const server=net.createServer(socket=>{
    sockets.add(socket);socket.on('close',()=>sockets.delete(socket));
    let buffer='',nonce;
    const proof=role=>crypto.createHmac('sha256',ticket).update(Buffer.concat([role,'1',endpoint,nonce,'server-nonce'].flatMap(value=>{const b=Buffer.from(value),n=Buffer.alloc(4);n.writeUInt32BE(b.length);return[n,b];}))).digest('base64url');
    socket.on('data',data=>{
      buffer+=data.toString();
      while(buffer.includes('\n')) {
        const i=buffer.indexOf('\n'),m=JSON.parse(buffer.slice(0,i));buffer=buffer.slice(i+1);
        const send=value=>socket.write(JSON.stringify(value)+'\n');
        if(m.type==='session_hello') {
          nonce=m.client_nonce;
          if(mode==='early-ack')send({type:'session_hello_ack',protocol:1});
          else send({type:'session_challenge',protocol:1,server_nonce:'server-nonce',server_proof:mode==='bad-proof'?'invalid':proof('wbipc-s')});
        } else if(m.type==='session_prove') {
          assert.equal(m.client_proof,proof('wbipc-c'));
          send({type:'session_hello_ack',protocol:1});
        } else if(m.method==='broker/GetPipe') {
          assert.equal(m.params.pipe,'wb.request');send({id:m.id,result:{channel:'c:wb.request'}});
        } else {
          assert.equal(m.params.path,'/v2/as/connector/oauth/ima/status');assert.equal(m.params.method,'GET');
          send({id:m.id,result:{status:200,body_b64:Buffer.from('{"code":0,"data":{"status":"connected"}}').toString('base64')}});
        }
      }
    });
  });
  await new Promise(resolve=>server.listen(endpoint,resolve));
  try {await callback(discovery);}finally {for(const socket of sockets)socket.destroy();await new Promise(resolve=>server.close(resolve));await fs.unlink(discovery);await fs.rmdir(dir);}
}
test('WorkBuddy IPC authenticates both sides and restricts API access',{skip:process.platform!=='win32'},async()=>{
  await broker('valid',async discovery=>{
    const client=await connectWb(discovery);
    try {assert.equal((await client.request('status')).data.status,'connected');await assert.rejects(()=>client.request('start'),/Unsupported/);}
    finally {client.close();}
  });
});
test('Bad server proofs and acknowledgements before proof are rejected',{skip:process.platform!=='win32'},async()=>{
  for(const mode of ['bad-proof','early-ack'])await broker(mode,async discovery=>{await assert.rejects(()=>connectWb(discovery),/proof|acknowledgement/);});
});
