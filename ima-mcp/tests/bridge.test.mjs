import {test} from 'node:test';
import assert from 'node:assert/strict';
import {ImaConnection,extractToken,parseResponse} from '../scripts/bridge.mjs';
const valid=()=>({token:'synthetic-mcp-token',expiresAt:Date.now()+3600000});
const result=(status,body)=>new Response(body?JSON.stringify(body):null,{status});

test('Requires a dedicated unexpired MCP token with a verified expiry',()=>{
  for(const data of [{access_token:'ordinary-token'},{mcp_token:'x'},{mcp_token:'x\r\nInjected: yes',mcp_token_expire_at:100}]) {
    assert.throws(()=>extractToken({httpStatus:200,code:0,data},0));
  }
  assert.throws(()=>extractToken({httpStatus:401,code:0,data:{mcp_token:'x'}}));
  assert.throws(()=>extractToken({httpStatus:200,code:0,data:{mcp_token:'x',mcp_token_expire_at:10}},20000),/expired/);
  assert.equal(extractToken({httpStatus:200,code:0,data:{mcp_token:'x',mcp_token_expire_at:100}},0).expiresAt,100000);
});
test('Parses JSON, CRLF and multi-line SSE without losing Chinese content',()=>{
  assert.equal(parseResponse('{"id":1,"result":"中文"}',1).result,'中文');
  assert.equal(parseResponse('data: {"id":2}\r\n\r\ndata: {"id":1,\r\ndata: "result":"中文"}\r\n\r\n',1).result,'中文');
  assert.equal(parseResponse('',1),undefined);
  assert.throws(()=>parseResponse('data: {"id":2}\n\n',1),/invalid response/);
});
test('Standalone mode sends cached authorization directly to IMA and never opens WorkBuddy',async()=>{
  let calls=0;
  const c=new ImaConnection({allowWorkBuddy:false,load:()=>valid(),connect:()=>{throw Error('WorkBuddy must not be called');},fetchImpl:async(url,options)=>{
    calls++;assert.equal(url,'https://ima.qq.com/mcp');assert.equal(options.headers.Authorization,'Bearer synthetic-mcp-token');assert.equal(options.redirect,'error');
    return result(200,{jsonrpc:'2.0',id:1,result:{protocolVersion:'2025-03-26'}});
  }});
  const reply=await c.request({jsonrpc:'2.0',id:1,method:'initialize'});
  assert.equal(reply.id,1);assert.equal(calls,1);
});
test('Missing or unreadable standalone cache never falls back to WorkBuddy',async()=>{
  for(const load of [()=>null,()=>{throw Error('cache expired');}]) {
    const c=new ImaConnection({allowWorkBuddy:false,load,connect:()=>assert.fail('must not connect')});
    await assert.rejects(()=>c.getAuth());
  }
});
test('Auto mode can obtain and persist a new authorization when no cache exists',async()=>{
  let closed=false,saved;
  const response={httpStatus:200,code:0,data:{mcp_token:'new-token',mcp_token_expire_at:Math.floor(Date.now()/1000)+3600}};
  const c=new ImaConnection({load:()=>null,connect:async()=>({request:async()=>response,close(){closed=true;}}),save:value=>{saved=value;}});
  assert.equal(await c.getAuth(),'new-token');assert.equal(saved.token,'new-token');assert.equal(closed,true);
});
test('401 retries only after obtaining a different token',async()=>{
  let calls=0;
  const c=new ImaConnection({load:()=>valid(),connect:async()=>({request:async()=>({httpStatus:200,code:0,data:{mcp_token:'replacement',mcp_token_expire_at:Math.floor(Date.now()/1000)+3600}}),close(){}}),save(){},fetchImpl:async()=>++calls===1?result(401):result(200,{id:1,result:{}})});
  await c.request({id:1,method:'tools/call'});assert.equal(calls,2);
});
test('Standalone 401, permission denial and uncertain writes are never retried',async()=>{
  for(const failure of [401,403,'timeout']) {
    let calls=0;
    const c=new ImaConnection({allowWorkBuddy:false,load:()=>valid(),connect:()=>assert.fail('must not connect'),fetchImpl:async()=>{calls++;if(failure==='timeout')throw Error('timeout');return result(failure);}});
    await assert.rejects(()=>c.request({id:1,method:'tools/call'}));assert.equal(calls,1);
  }
});
test('Sessions and negotiated protocol are retained; business errors pass through',async()=>{
  let calls=0;
  const c=new ImaConnection({allowWorkBuddy:false,load:()=>valid(),fetchImpl:async(url,options)=>{
    if(++calls===1)return new Response('{"id":1,"result":{"protocolVersion":"2025-03-26"}}',{headers:{'Mcp-Session-Id':'test-session'}});
    assert.equal(options.headers['Mcp-Session-Id'],'test-session');assert.equal(options.headers['MCP-Protocol-Version'],'2025-03-26');
    return result(200,{id:2,result:{isError:true,content:[{type:'text',text:'permission denied'}]}});
  }});
  await c.request({id:1,method:'initialize'});
  assert.equal((await c.request({id:2,method:'tools/call'})).result.isError,true);assert.equal(calls,2);
});
