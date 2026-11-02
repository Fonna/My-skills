import {test} from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {authPath,saveAuth,loadAuth,validateAuth} from '../scripts/auth-store.mjs';

test('Invalid and expired cached credentials are rejected',()=>{
  for(const value of [null,{token:'x'},{token:'x\nheader',expiresAt:100000},{token:'x',expiresAt:10000}])assert.throws(()=>validateAuth(value,0));
});
test('Default cache stays outside the skill/repository and honors Codex home',()=>{
  const oldHome=process.env.CODEX_HOME,oldAuth=process.env.IMA_MCP_AUTH_FILE;
  try {
    delete process.env.IMA_MCP_AUTH_FILE;process.env.CODEX_HOME=path.join(os.tmpdir(),'codex-fixture');
    assert.equal(authPath(),path.join(process.env.CODEX_HOME,'ima-mcp','auth.dpapi.json'));
  }finally {
    if(oldHome===undefined)delete process.env.CODEX_HOME;else process.env.CODEX_HOME=oldHome;
    if(oldAuth===undefined)delete process.env.IMA_MCP_AUTH_FILE;else process.env.IMA_MCP_AUTH_FILE=oldAuth;
  }
});
test('DPAPI round-trip never stores a plaintext token and corrupt caches fail closed',{skip:process.platform!=='win32'},()=>{
  const dir=fs.mkdtempSync(path.join(os.tmpdir(),'ima-mcp-auth-test-')),file=path.join(dir,'auth.json');
  const token='synthetic-secret-that-must-not-appear-in-cache';
  try {
    assert.equal(loadAuth(file),null);
    saveAuth({token,expiresAt:Date.now()+3600000},file);
    const bytes=fs.readFileSync(file,'utf8');assert.equal(bytes.includes(token),false);assert.equal(loadAuth(file).token,token);
    const data=JSON.parse(bytes);data.encrypted='invalid';fs.writeFileSync(file,JSON.stringify(data));
    assert.throws(()=>loadAuth(file),/decrypt/);
  }finally {fs.unlinkSync(file);fs.rmdirSync(dir);}
});
