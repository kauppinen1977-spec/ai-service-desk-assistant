// Repeatable public PoC UI regression suite. Private report fixtures are excluded.
const fs=require('node:fs'),assert=require('node:assert/strict');
const html=fs.readFileSync('index.html','utf8');
require('./ui_state_test.cjs');
const candidate=require('./ui_candidate_visibility_test.cjs');
(async()=>{for(const name of ['ui_safety_stop_test','ui_startup_fact_test','ui_ticket_clear_test']){const result=await require('./'+name+'.cjs')(html);console.log(name,result);assert(!result.failed&&result.passed!==false);}})().catch(error=>{console.error(error);process.exitCode=1;});
