import {ImaConnection} from './bridge.mjs';

const standalone=process.argv.includes('--standalone');
const readTest=process.argv.includes('--read-test');
function toolData(result) {
  if(result.isError)throw Error('IMA tool returned an execution error');
  if(result.structuredContent)return result.structuredContent;
  const text=result.content?.filter(x=>x.type==='text').map(x=>x.text).join('\n');
  try {return JSON.parse(text);}catch{throw Error('IMA tool returned an unsupported data format');}
}
try {
  if(process.platform!=='win32'||Number(process.versions.node.split('.')[0])<22)throw Error('Windows and Node.js 22+ are required');
  const connection=new ImaConnection({allowWorkBuddy:!standalone});
  let id=0;
  const request=async(method,params)=>{
    const response=await connection.request({jsonrpc:'2.0',id:++id,method,params});
    if(response?.error||!response?.result)throw Error('MCP request failed: '+method);
    return response.result;
  };
  const init=await request('initialize',{protocolVersion:'2025-03-26',capabilities:{},clientInfo:{name:'ima-mcp-doctor',version:'1.0.0'}});
  await connection.request({jsonrpc:'2.0',method:'notifications/initialized'});
  const catalog=await request('tools/list',{});
  const report={ok:true,standalone,workBuddyAccessAllowed:!standalone,server:init.serverInfo,tools:catalog.tools?.map(x=>x.name),authorizationExpiresAt:new Date(connection.auth.expiresAt).toISOString()};
  if(readTest) {
    const call=async(name,args)=>toolData(await request('tools/call',{name,arguments:args}));
    const libraries=await call('get_knowledge_base_list',{params:[{type:'KBT_MINE_KB',limit:1,cursor:''}]});
    const kb=libraries.results?.[0]?.knowledge_base_list?.[0];
    report.readTest={knowledgeBaseList:'passed',scope:'first personal knowledge base, one item'};
    if(kb) {
      if(typeof kb.id!=='string')throw Error('Knowledge-base result schema changed; update doctor.mjs');
      const items=await call('get_knowledge_list',{knowledge_base_id:kb.id,limit:1,cursor:'',sort_type:'UPDATE_TS_DESC_SORT_TYPE',filters:[{filter_type:'MEDIA_STATE_FILTER_TYPE',media_state_filter:{media_states:['MEDIA_PARSE_SUCCESS']}},{filter_type:'MEDIA_TYPE_FILTER_OUT_TYPE',media_type_filter_out:{media_type:['FOLDER']}}]});
      report.readTest.knowledgeList='passed';
      const item=items.knowledge_list?.[0];
      if(item?.can_fetch_content&&item.media_id) {
        const content=await call('fetch_media_content',{media_id:item.media_id});
        if(typeof content.content!=='string'||!content.content.length)throw Error('IMA returned no readable content');
        report.readTest.contentRead='passed';report.readTest.contentCharacters=content.content.length;
      }else report.readTest.contentRead='skipped: no readable item';
    }else report.readTest.knowledgeList='skipped: no personal knowledge base';
  }
  console.log(JSON.stringify(report,null,2));
} catch(error) {console.error(JSON.stringify({ok:false,message:error.message}));process.exitCode=1;}
