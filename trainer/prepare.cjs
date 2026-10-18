/* Verify the embedded domain and build the exact eligible-cell index. */
const fs=require('node:fs'),zlib=require('node:zlib'),path=require('node:path'),assert=require('node:assert/strict');
const C=require('./core.js');const dir=process.argv[2],D=JSON.parse(fs.readFileSync(path.join(dir,'trainer-test-data.json'),'utf8'));
const cells=new Map(),counts={},audit={boards:0,eligibleCombos:0,cells:0,policyChecks:0,blocked:0,rangeChecks:0,transitionChecks:0,sampledPairs:0};
for(let bi=0;bi<D.boards.length;bi++){
 const board=D.boards[bi],block=C.decodeBlock(JSON.parse(zlib.gunzipSync(Buffer.from(D.blocks[bi],'base64'))));audit.boards++;
 for(let s=0;s<3;s++)for(const n of s===2?['01','04']:['01','02','03','04','05']){
  const hero=C.branch(D,s,n).actor,history=C.prefix(s,n).map(x=>[...x,s===0&&n==='05'&&x[0]==='01']);
  const hw=C.reached(D,block,s,board,history,hero,hero),vw=C.reached(D,block,s,board,history,1-hero,hero);
  const live=vw.map((v,i)=>v>0?i:-1).filter(x=>x>=0);const rows=new Set();
  for(let actor=0;actor<2;actor++){
   const w=actor===hero?hw:vw;
   for(let cid=0;cid<w.length;cid++){
    assert(w[cid]>=0&&w[cid]<=D.studies[s].weights[actor][cid]+1e-9);
    if(!C.legal(D,board,cid))assert.equal(w[cid],0);
    audit.rangeChecks++;
   }
  }
  hw.forEach((w,cid)=>{
   if(w<=0)return;const sp=C.spec(D,s,n,board,block.meta[cid]),p=C.policy(D,s,n,board,block.meta[cid],cid);
   if(!p)return;
   if(!live.some(v=>C.compatible(D,cid,v))){audit.blocked++;return}
   assert(Math.abs(Object.values(p).reduce((a,b)=>a+b,0)-1)<1e-9);
   assert(Object.keys(p).every(a=>C.branch(D,s,n).actions.includes(a)));audit.policyChecks++;
   for(const a of Object.keys(p)){
    const nn=C.next(s,n,a);
    if(nn){assert.notEqual(C.branch(D,s,n).actor,C.branch(D,s,nn).actor);assert(C.prefix(s,nn).some(x=>x[0]===n&&x[1]===a))}
    audit.transitionChecks++;
   }
   rows.add(sp.row);audit.eligibleCombos++;
  });
  for(const r of rows){
   const g=C.nine(board),key=C.cellKey(s,n,g,r);if(!cells.has(key))cells.set(key,{key,s,n,g,r,boards:[]});cells.get(key).boards.push(bi);
   const hi=hw.findIndex((w,id)=>w>0&&block.meta[id]&&C.spec(D,s,n,board,block.meta[id])?.row===r&&C.policy(D,s,n,board,block.meta[id],id));
   const vi=live.find(id=>C.compatible(D,hi,id));assert(hi>=0&&vi!==undefined);
   assert.equal(new Set([...D.combos[hi],...D.combos[vi],...board.split(' ').map(c=>D.deck.indexOf(c))]).size,7);audit.sampledPairs++;
  }
 }
}
D.cells=[...cells.values()];audit.cells=D.cells.length;
// No branch/hand cell can starve: complete cycles select every eligible cell once.
let seed=12345;const rng=()=>{seed=(1664525*seed+1013904223)>>>0;return seed/4294967296};
for(let i=0;i<D.cells.length*20+17;i++){const c=C.chooseCell(D.cells,counts,rng);counts[c.key]=(counts[c.key]||0)+1}
const values=D.cells.map(c=>counts[c.key]||0);audit.coverageMin=Math.min(...values);audit.coverageMax=Math.max(...values);assert(audit.coverageMax-audit.coverageMin<=1);
assert.equal(C.nine('Ks 7h 2d'),1);assert.equal(C.nine('As 5h 3d'),8);assert.equal(C.nine('Js 9h 8d'),5);
assert.equal(C.next(0,'03','raise'),'04');assert.equal(C.next(0,'05','raise'),null);assert.equal(C.next(1,'05','raise'),null);assert.equal(C.next(2,'04','raise'),null);
assert.deepEqual(C.policy(D,0,'02','Js 9h 8d',[2,-1,1],0),{bet:1});
assert.deepEqual(C.policy(D,1,'02','Js 9h 8d',[2,-1,1],0),{check:.5,bet:.5});
assert.deepEqual(C.policy(D,1,'03','Ts 8h 7d',[10,-1,1],0),{fold:1});
for(let s=0;s<2;s++)for(const n of ['01','02','03','04','05'])assert(D.cells.some(c=>c.s===s&&c.n===n),`Missing ${s}/${n}`);
assert(!D.cells.some(c=>c.n==='06'));
assert(!D.tables.dr_btn&&!D.tables.dr_utg);
audit.branches=12;
let template=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
template=template.replace('/*__CSS__*/',fs.readFileSync(path.join(__dirname,'style.css'),'utf8')).replace('/*__CORE__*/',fs.readFileSync(path.join(__dirname,'core.js'),'utf8')).replace('/*__APP__*/',fs.readFileSync(path.join(__dirname,'app.js'),'utf8')).replace('"__PAYLOAD__"',JSON.stringify(D).replaceAll('</','<\\/'));
assert(!/\bfetch\s*\(|<script[^>]+src=|<link[^>]+href=/.test(template),'Standalone artifact has external dependency');
fs.writeFileSync(path.join(dir,'poker_trainer.html'),template);
fs.writeFileSync(path.join(dir,'trainer-test-data.json'),JSON.stringify(D));
fs.writeFileSync(path.join(dir,'test-report.json'),JSON.stringify(audit,null,2));
const manifest=JSON.parse(fs.readFileSync(path.join(dir,'trainer-manifest.json'),'utf8'));
manifest.htmlBytes=Buffer.byteLength(template);manifest.htmlSHA256=require('node:crypto').createHash('sha256').update(template).digest('hex');manifest.cells=audit.cells;
fs.writeFileSync(path.join(dir,'trainer-manifest.json'),JSON.stringify(manifest,null,2));
console.log(audit);
