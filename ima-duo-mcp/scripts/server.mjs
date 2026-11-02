import readline from 'node:readline';
import {pathToFileURL} from 'node:url';
import {loadCredentials} from './store.mjs';
import {ImaClient} from './client.mjs';

const page={cursor:{type:'string'},limit:{type:'integer',minimum:1,maximum:50}};
const base={knowledge_base_id:{type:'string',description:'从本服务查库工具返回的 OpenAPI ID；不要混用官方 MCP ID'}};
export const tools=[
  {name:'list_knowledge_bases',description:'列举 ima OpenAPI 知识库，一次一页，保留 next_cursor/is_end。',inputSchema:{type:'object',properties:page,additionalProperties:false},annotations:{readOnlyHint:true,idempotentHint:true}},
  {name:'list_knowledge',description:'列举指定知识库根目录或文件夹内资料；用于取得真实 media_id 和文件夹 ID。',inputSchema:{type:'object',properties:{...base,folder_id:{type:'string'},...page},required:['knowledge_base_id'],additionalProperties:false},annotations:{readOnlyHint:true,idempotentHint:true}},
  {name:'move_knowledge',description:'按用户明确要求，在同一知识库内移动资料，不能移动文件夹。目标根目录必须显式传空字符串。检查逐项结果；失败或超时不能直接重试。',inputSchema:{type:'object',properties:{...base,media_ids:{type:'array',items:{type:'string'},minItems:1,maxItems:50,uniqueItems:true},destination_folder_id:{type:'string',description:'真实目标文件夹 ID，根目录显式传空字符串'}},required:['knowledge_base_id','media_ids','destination_folder_id'],additionalProperties:false},annotations:{readOnlyHint:false,destructiveHint:true,idempotentHint:false}}
];
export async function dispatch(message,{getClient=()=>new ImaClient(loadCredentials())}={}) {
  const {method,params={}}=message;
  if(method==='initialize')return {protocolVersion:['2025-11-25','2025-06-18','2025-03-26','2024-11-05'].includes(params.protocolVersion)?params.protocolVersion:'2025-03-26',capabilities:{tools:{}},serverInfo:{name:'ima-duo-codex',version:'1.0.0'}};
  if(method==='ping')return {};
  if(method==='tools/list')return {tools};
  if(method==='tools/call') {
    try {
      if(!tools.some(x=>x.name===params.name))throw Error('不支持的工具');
      const client=getClient();
      const args=params.arguments??{};
      const data=await ({list_knowledge_bases:()=>client.listBases(args),list_knowledge:()=>client.listKnowledge(args),move_knowledge:()=>client.move(args)})[params.name]();
      return {content:[{type:'text',text:JSON.stringify(data)}],isError:data.success===false};
    }catch(error){return {isError:true,content:[{type:'text',text:error.message}]};}
  }
  throw Object.assign(Error('Method not found'),{code:-32601});
}
export async function run() {
  const input=readline.createInterface({input:process.stdin,crlfDelay:Infinity});
  for await(const line of input) {
    if(!line.trim())continue;
    let message;
    try {message=JSON.parse(line);}catch{process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:null,error:{code:-32700,message:'Parse error'}})+'\n');continue;}
    if(!message||message.jsonrpc!=='2.0'||typeof message.method!=='string') {process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:message?.id??null,error:{code:-32600,message:'Invalid request'}})+'\n');continue;}
    if(message.id===undefined)continue;
    try {process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:message.id,result:await dispatch(message)})+'\n');}
    catch(error){process.stdout.write(JSON.stringify({jsonrpc:'2.0',id:message.id,error:{code:error.code??-32603,message:error.message}})+'\n');}
  }
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href)run().catch(()=>{process.stderr.write('ima-duo MCP 启动失败\n');process.exitCode=1;});
