import fs from 'node:fs';
import http from 'node:http';
import crypto from 'node:crypto';
import {spawn} from 'node:child_process';
import {credentialPath,loadCredentials,saveCredentials,validateCredentials,readEnvironmentCredentials} from './store.mjs';
import {ImaClient} from './client.mjs';

async function login() {
  const nonce=crypto.randomBytes(24).toString('hex');
  const route='/'+nonce;
  let origin,busy=false;
  const server=http.createServer(async(req,res)=>{
    const respond=(status,text,type='text/html; charset=utf-8')=>{res.writeHead(status,{'Content-Type':type,'Cache-Control':'no-store','X-Content-Type-Options':'nosniff','Referrer-Policy':'same-origin','Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'"});res.end(text);};
    if(req.headers.host!==new URL(origin).host)return respond(403,'拒绝请求');
    if(req.method==='GET'&&req.url===route) {
      return respond(200,`<!doctype html><html lang="zh"><meta charset="utf-8"><title>ima-duo · Codex 授权配置</title><style>body{font:17px system-ui;max-width:680px;margin:60px auto;padding:20px;line-height:1.8}input{display:block;box-sizing:border-box;width:100%;padding:12px;margin:8px 0 24px}button{padding:12px 25px}small{color:#555}</style><h1>连接 ima-duo 到 Codex</h1><p>在 <a href="https://ima.qq.com/agent-interface" target="_blank" rel="noopener noreferrer">ima 官方授权配置页</a> 登录并取得 Client ID 与 API Key，然后填写到下面。</p><p>凭证仅发往本机接入程序和 ima 官方接口；验证成功后使用 Windows DPAPI 加密保存。这不是扫码 OAuth 授权。</p><form method="post" action="${route}/authorize" autocomplete="off"><input type="hidden" name="nonce" value="${nonce}"><label>Client ID<input name="clientId" type="password" required maxlength="4096" autocomplete="off"></label><label>API Key<input name="apiKey" type="password" required maxlength="4096" autocomplete="off"></label><button type="submit">验证并加密保存</button></form><small>只读验证会查询一页知识库，不会移动、创建或删除资料。</small></html>`);
    }
    if(req.method!=='POST'||req.url!==route+'/authorize')return respond(404,'页面不存在');
    if(req.headers.origin!==origin||!String(req.headers['content-type']||'').startsWith('application/x-www-form-urlencoded'))return respond(403,'请求来源不符');
    if(busy)return respond(409,'正在验证，请稍后');
    busy=true;
    try {
      const chunks=[];let size=0;
      for await(const chunk of req){size+=chunk.length;if(size>16384)throw Error('表单过大');chunks.push(chunk);}
      const form=new URLSearchParams(Buffer.concat(chunks).toString('utf8'));
      if(form.get('nonce')!==nonce)throw Error('表单已失效');
      const creds=validateCredentials({clientId:form.get('clientId'),apiKey:form.get('apiKey')});
      const data=await new ImaClient(creds).listBases({limit:1});
      if(!Array.isArray(data.info_list))throw Error('只读授权验证返回格式不符');
      saveCredentials(creds);
      respond(200,'<!doctype html><meta charset="utf-8"><title>授权完成</title><h1>授权配置成功</h1><p>已通过 ima 只读验证，凭证已在本机加密保存。可以关闭此页面并返回 Codex。</p>');
      console.log(JSON.stringify({authorized:true,readOnlyVerification:true,recordsReturned:data.info_list.length}));
      clearTimeout(expiry);server.close();server.closeIdleConnections();
    } catch {
      respond(400,'<!doctype html><meta charset="utf-8"><h1>未能完成配置</h1><p>凭证未保存。请确认 Client ID/API Key 正确且 ima 网络可达，再返回重试。</p>');
      console.log(JSON.stringify({authorized:false,message:'验证失败，未保存凭证'}));
    } finally {busy=false;}
  });
  server.requestTimeout=60000;server.headersTimeout=15000;
  const expiry=setTimeout(()=>{server.close();server.closeAllConnections();console.log(JSON.stringify({authorized:false,message:'本地授权页面已超时，请重新运行 login'}));},15*60*1000);
  await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(0,'127.0.0.1',resolve);});
  origin='http://127.0.0.1:'+server.address().port;
  const url=origin+route;
  console.log(JSON.stringify({authorizationPage:url,expiresInMinutes:15}));
  const opener=spawn('rundll32.exe',['url.dll,FileProtocolHandler',url],{detached:true,stdio:'ignore',windowsHide:true});
  opener.on('error',()=>{});opener.unref();
}
try {
  const command=process.argv[2];
  if(command==='login')await login();
  else if(command==='import-env'){
    const creds=readEnvironmentCredentials(process.argv[3]);
    const data=await new ImaClient(creds).listBases({limit:1});
    if(!Array.isArray(data.info_list))throw Error('只读授权验证返回格式不符');
    saveCredentials(creds);
    console.log(JSON.stringify({authorized:true,readOnlyVerification:true,recordsReturned:data.info_list.length}));
  }
  else if(command==='status'){console.log(JSON.stringify({cacheExists:fs.existsSync(credentialPath())}));}
  else if(command==='check'){const d=await new ImaClient(loadCredentials()).listBases({limit:1});if(!Array.isArray(d.info_list))throw Error('授权验证返回格式不符');console.log(JSON.stringify({authorized:true,readOnlyVerification:true,recordsReturned:d.info_list.length}));}
  else throw Error('使用 auth.mjs login / import-env [ClientID] / status / check');
}catch(error){console.error(JSON.stringify({ok:false,message:error.message}));process.exitCode=1;}
