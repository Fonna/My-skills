import fs from 'node:fs';
import {connectWb} from './wbipc.mjs';
import {extractToken} from './bridge.mjs';
import {authPath,loadAuth,saveAuth} from './auth-store.mjs';

const action=process.argv[2] || 'status';
try {
  if (action==='login') {
    const client=await connectWb();
    try {
      const value=extractToken(await client.request('accesstoken'));
      saveAuth(value);
      console.log(JSON.stringify({authorized:true,expiresAt:new Date(value.expiresAt).toISOString(),storage:'Windows DPAPI CurrentUser',workBuddyMayBeClosed:true}));
    } finally {client.close();}
  } else if (action==='status') {
    const value=loadAuth();
    console.log(JSON.stringify({authorized:!!value,...value?{expiresAt:new Date(value.expiresAt).toISOString()}:{} }));
    if(!value)process.exitCode=1;
  } else if (action==='clear') {
    const filename=authPath();if(fs.existsSync(filename))fs.unlinkSync(filename);
    console.log(JSON.stringify({localAuthorizationRemoved:true,remoteAuthorizationRevoked:false}));
  } else throw Error('Usage: node auth.mjs login|status|clear');
} catch(error) {console.error(error.message);process.exitCode=1;}
