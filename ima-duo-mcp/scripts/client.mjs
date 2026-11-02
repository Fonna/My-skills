// Request contracts adapted from ima-duo (MIT), see ../LICENSE and ../UPSTREAM.md.
const BASE='https://ima.qq.com/';
const PATHS=new Set(['search_knowledge_base','get_knowledge_list','move_knowledge']);
export class ImaClient {
  constructor(credentials,{fetchImpl=fetch}={}) {this.credentials=credentials;this.fetch=fetchImpl;}
  async call(endpoint,body) {
    if (!PATHS.has(endpoint)) throw Error('不支持该接口');
    let response;
    try {
      response=await this.fetch(BASE+'openapi/wiki/v1/'+endpoint,{
        method:'POST',redirect:'error',signal:AbortSignal.timeout(45000),
        headers:{'Content-Type':'application/json','ima-openapi-clientid':this.credentials.clientId,'ima-openapi-apikey':this.credentials.apiKey},
        body:JSON.stringify(body)
      });
    } catch {throw Error(endpoint==='move_knowledge'?'ima 移动请求未完成，可能已生效；请先核实位置，不要直接重试':'ima 只读请求未完成，请检查网络');}
    let payload;
    try {payload=await response.json();} catch {throw Error('ima 返回非 JSON 响应');}
    if (!response.ok || payload?.code !== 0) {
      const code=Number.isInteger(payload?.code)?payload.code:'unknown';
      throw Error(`ima 接口失败：HTTP ${response.status}，code ${code}；未自动重试`);
    }
    if (!payload.data || typeof payload.data !== 'object') throw Error('ima 响应缺少数据');
    return payload.data;
  }
  async listBases({cursor='',limit=20}={}) {
    checkPage(cursor,limit);
    return this.call('search_knowledge_base',{query:'',cursor,limit});
  }
  async listKnowledge({knowledge_base_id,folder_id='',cursor='',limit=50}) {
    checkId(knowledge_base_id);checkPage(cursor,limit);
    if(typeof folder_id!=='string')throw Error('folder_id 必须是字符串');
    return this.call('get_knowledge_list',{knowledge_base_id,cursor,limit,...(folder_id?{folder_id}:{})});
  }
  async move({knowledge_base_id,media_ids,destination_folder_id}) {
    checkId(knowledge_base_id);
    if(typeof destination_folder_id!=='string')throw Error('必须显式指定目标文件夹；根目录传空字符串');
    if(!Array.isArray(media_ids)||media_ids.length===0||media_ids.length>50)throw Error('一次移动 1 至 50 个资料');
    media_ids.forEach(checkId);
    if(new Set(media_ids).size!==media_ids.length)throw Error('资料 ID 不得重复');
    const body={src_knowledge_base_id:knowledge_base_id,dst_knowledge_base_id:knowledge_base_id,infos:media_ids.map(media_id=>({media_id})),...(destination_folder_id?{dst_folder_id:destination_folder_id}:{})};
    const data=await this.call('move_knowledge',body);
    const outcomes=media_ids.map(media_id=>{
      const code=data.move_results?.[media_id]?.ret_code;
      return {media_id,success:code===0||code==='0',ret_code:code??null};
    });
    return {success:outcomes.every(x=>x.success),knowledge_base_id,destination_folder_id,outcomes};
  }
}
function checkId(value) {if(typeof value!=='string'||!value.trim()||value.length>1024||/[\r\n\x00]/.test(value))throw Error('必须使用接口返回的真实 ID');}
function checkPage(cursor,limit) {if(typeof cursor!=='string'||!Number.isInteger(limit)||limit<1||limit>50)throw Error('游标必须为字符串，limit 范围 1 至 50');}
