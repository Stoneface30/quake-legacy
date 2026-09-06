// Isolated mobile review regression. All HTTP responses and verdicts are synthetic.
// Uses an existing Playwright installation; never installs dependencies.
// Supply PLAYWRIGHT_MODULE, PLAYWRIGHT_CHROMIUM_EXECUTABLE and REVIEW_TEST_VIDEO.
// Run from the repository root with node scripts/check_review_mobile.cjs.
const fs = require('fs');
const assert = require('node:assert/strict');
const { chromium } = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
(async () => {
 const browser = await chromium.launch({executablePath:process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE,headless:true});
 const page = await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
 const errors=[]; page.on('pageerror',e=>errors.push(e.message));
 const items=Array.from({length:4},(_,i)=>({item_id:'USER_FRAG:'+(i+1),source_id:i+1,item_type:'USER_FRAG',machine_rank:i+1,total_items:4,machine_score:1,weapon:'ROCKET',round_no:1,victim:2,duration_s:6,frag_offset_s:3,note:'',human_role:null}));
 let votes=[], sceneState='QUEUED', failVote=false, notes=[];
 const media=fs.readFileSync(process.env.REVIEW_TEST_VIDEO || '.tmp/review-20260905/synthetic.mp4');
 const scene={available:true,mode:'SCENE_MODE',scene_id:'test-scene',media_start_ms:0,media_end_ms:20000,events:items.slice(0,3).map((it,i)=>({occurrence_id:it.source_id,item_id:it.item_id,event_id:'event-'+i,t_ms:3000+i*6000,offset_ms:3000+i*6000,label:'F'+(i+1),takes_verdict:true}))};
 await page.route('**/*', async route=>{
  const u=new URL(route.request().url()), p=u.pathname;
  let d={}; let status=200;
  if(p==='/') return route.fulfill({contentType:'text/html',body:fs.readFileSync('creative_suite/frontend/review.html','utf8')});
  if(p.endsWith('/queue')) d={items,offset:0,total:4};
  else if(p.endsWith('/progress')) d={reviewed:votes.length,total:4,roles:{}};
  else if(p.endsWith('/corpora')) d={corpora:[],item_types:[]};
  else if(p.endsWith('/facets')) d={weapons:[],maps:[],traits:[],death_causes:[]};
  else if(p.includes('/media_state/scene/')) d={ready:sceneState==='READY',state:sceneState,error:sceneState==='FAILED'?'synthetic render failure':null};
  else if(p.includes('/media_state/')) d={ready:true,state:'READY'};
  else if(p.startsWith('/api/review/scene/')) d=p.endsWith(':4')?{available:false}:scene;
  else if(p.includes('/item/')) d=items.find(x=>p.endsWith(x.item_id));
  else if(p.includes('/media_retry/scene/')) {sceneState='READY';d={state:'QUEUED'};}
  else if(p.endsWith('/verdict')) {if(failVote){status=500;d={detail:'test save failure'};}else{votes.push(route.request().postDataJSON());await new Promise(r=>setTimeout(r,150));d={};}}
  else if(p.includes('/media/')) return route.fulfill({contentType:'video/mp4',body:media});
  else if(p.endsWith('/note')) {notes.push(route.request().postDataJSON());d={};}
  else if(p.includes('/dossier/')) d={available:false};
  else if(p.includes('/round/')) d={available:false};
  return route.fulfill({status,contentType:'application/json',body:JSON.stringify(d)});
 });
 try {
  await page.goto('http://review.test/'); await page.waitForFunction(()=>typeof cur!=='undefined' && cur?.source_id===1);
  await page.waitForTimeout(300);
  assert(!await page.locator('#v').getAttribute('src').then(x=>x?.includes('/media/scene/')), 'pending scene must not replace ready proxy');
  await page.locator('#d-note summary').click();
  await page.locator('#note').fill('synthetic annotation');
  await page.evaluate(()=>{verdict('T4_KEEP_NORMAL');verdict('T4_KEEP_NORMAL');}); await page.waitForTimeout(500);
  assert.equal(votes.length,1,'double tap saves once');
  assert.equal(votes[0].note,'synthetic annotation','note travels with original verdict');
  assert.equal(await page.evaluate(()=>cur.source_id),2,'advance to second event');
  failVote=true; await page.evaluate(()=>verdict('T4_KEEP_NORMAL'));
  assert.equal(await page.evaluate(()=>cur.source_id),2,'failed save must not advance');
  failVote=false;
  sceneState='READY';
  await page.waitForFunction(()=>document.querySelector('#v').dataset.sceneId==='test-scene');
  await page.waitForFunction(()=>document.querySelector('#v').readyState>=2);
  const sceneURL=await page.locator('#v').getAttribute('src');
  for(let n=2;n<=3;n++){
   await page.locator('#b4').click();await page.waitForFunction(n=>cur.source_id===n+1,n);
   if(n===2) assert.equal(await page.locator('#v').getAttribute('src'),sceneURL,'same-scene vote reuses media');
  }
  sceneState='FAILED'; await page.evaluate(()=>show(items[0]));
  await page.waitForFunction(()=>document.querySelector('#rail').textContent.includes('RENDER FAILED'));
  await page.locator('#rail button').filter({hasText:'RETRY'}).click();
  await page.waitForFunction(()=>document.querySelector('#rail').textContent.includes('Scene context ready'));
  await page.waitForFunction(()=>document.querySelector('#v').readyState>=2);

  assert.deepEqual(votes.map(x=>x.item_id),items.slice(0,3).map(x=>x.item_id));
  console.log('PASS mobile votes, note preservation, pending-scene fallback, READY upgrade, scene reuse, FAILED and retry');
 } finally { console.log('page errors:',errors); await page.screenshot({path:process.env.REVIEW_SCREENSHOT || '.tmp/review-20260905/mobile-proof.png',fullPage:true});await browser.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
