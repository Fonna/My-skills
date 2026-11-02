import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {saveCredentials,loadCredentials,validateCredentials} from '../scripts/store.mjs';

test('credentials reject header injection without echoing their contents',()=>{
  const secret='synthetic\r\nX-Injected: secret';
  assert.throws(()=>validateCredentials({clientId:'c',apiKey:secret}),e=>!e.message.includes(secret));
});
test('Windows cache round-trips credentials without storing plaintext',{skip:process.platform!=='win32'},()=>{
  const directory=fs.mkdtempSync(path.join(os.tmpdir(),'ima-duo-store-test-'));
  const filename=path.join(directory,'credentials.json');
  const value={clientId:'synthetic-client-123',apiKey:'synthetic-key-456'};
  try {
    saveCredentials(value,filename);
    const content=fs.readFileSync(filename,'utf8');
    assert(!content.includes(value.clientId));assert(!content.includes(value.apiKey));
    assert.deepEqual(loadCredentials(filename),value);
  }finally {if(fs.existsSync(filename))fs.unlinkSync(filename);fs.rmdirSync(directory);}
});
