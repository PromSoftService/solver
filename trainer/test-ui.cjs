'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const D=JSON.parse(fs.readFileSync(path.resolve(process.argv[2]||'output/trainer','trainer-test-data.json'),'utf8'));
const app=fs.readFileSync(path.join(__dirname,'app.js'),'utf8');
const template=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
const elements=new Map(),selected=[];
function el(id){if(!elements.has(id))elements.set(id,{textContent:id==='trainer-data'?JSON.stringify(D):'',innerHTML:'',querySelectorAll:()=>selected});return elements.get(id)}
const context=vm.createContext({document:{getElementById:el,querySelectorAll:()=>[]},TrainerCore:require('./core.js'),localStorage:{getItem:()=>null},console});
// Test presentation functions without starting a hand or replacing browser QA.
vm.runInContext(app.slice(0,app.indexOf("$('next').onclick=newHand")),context);
let checked=0;
for(const key of ['cb_btn','cb_utg','df_btn','df_utg']){
 const s=key.endsWith('utg')?1:0,n=key.startsWith('cb')?'02':'03';
 vm.runInContext(`review={s:${s},n:'${n}',sp:{key:'${key}',row:2,col:5}};renderDecisions()`,context);
 const html=el('decisions').innerHTML;
 assert(!html.includes(s===1?'BTN':'UTG'),`Opposite position leaked in ${key}`);
 const rows=[...html.matchAll(/<tr data-hand-row="(\d+)"[^>]*>([\s\S]*?)<\/tr>/g)];assert.equal(rows.length,12);
 for(const [,rString,row]of rows){const r=Number(rString),corrections=new Map();for(const [,gs,a]of row.matchAll(/data-flops="([\d,]+)" data-action="([^"]*)"/g))for(const g of gs.split(',').map(Number))corrections.set(g,a);
  for(let g=0;g<9;g++){const actual=D.tables[key].rows[r][g];if(actual==='—')continue;const base=vm.runInContext(`standardAt('${key}',${r},${g})`,context);assert.equal(corrections.get(g)||base,actual,`${key}/${r}/${g}`);checked++}
 }
}
for(const [key,s,cols]of [['donk',0,[0]],['donk',1,[1,2,3]],['vsdonk',0,[0]],['vsdonk',1,[1]],['vsxr',0,[0]],['vsxr',1,[1]],['oopcb',2,[0,1,2]],['stabdef',2,[0,1,2,3]]]){
 const actual=vm.runInContext(`decisionColumns('${key}',${s})`,context);assert.deepEqual(Array.from(actual),cols);
}
for(let s=0;s<3;s++)for(const n of s===2?['01','04']:['01','02','03','04','05']){selected.splice(0,selected.length,{value:s+':'+n});const cells=vm.runInContext('eligible()',context);assert(cells.length);assert(cells.every(c=>c.s===s&&c.n===n))}
selected.splice(0,selected.length,{value:'0:02'},{value:'1:02'});assert(vm.runInContext('eligible().every(c=>c.n==="02"&&c.s<2)',context));
selected.length=0;assert.equal(vm.runInContext('eligible().length',context),0);
for(const id of ['mode','filter','flopFilter','strict','score','reveal','studyLock','progress','covered','coverageGrid','settingsBtn'])assert(!template.includes(`id="${id}"`),`Obsolete UI ${id}`);
assert.equal((template.match(/role="tab"/g)||[]).length,3);
assert(!app.includes('unlocked'));
// All reviewed cases for a flop must be shown for every hand and branch.
const boards=['As Kh Qd','Ks 7h 2d','Ks Qh 2d','Ks 7h 6d','9s 6h 2d','Js 9h 8d','Ts 8h 7d','As 9h 7d','As 5h 3d'];
const expected=[['high'],['dry','gutdry','weakdry','over'],['weakcb','weakdf','gutbb'],['weakdry','over'],['weakxxx','over'],['third','topcc','weakwheel','gutcc'],['third','drawlow','weakwheel','over','overslow'],['weakcb','ace','weakdf'],['ace','weakwheel']];
for(let g=0;g<9;g++){
 const keys=require('./core.js').explanations(D,g).map(x=>x[0]);assert.deepEqual(keys,expected[g]);
 for(let s=0;s<3;s++)for(let r=0;r<12;r++){
  vm.runInContext(`review={s:${s},n:'02',board:'${boards[g]}',sp:{row:${r}}};renderExplanation()`,context);
  const html=el('explanation').innerHTML;
  assert.equal((html.match(/class="case-summary"/g)||[]).length,keys.length);
  for(const key of keys){assert(html.includes(D.explanations[key].lead));assert(html.includes(D.explanations[key].html));}
 }
}
// Invalid actions leave both UI and state unchanged. Either side of a mix is OK.
for(const p of [{call:1},{call:.5,raise:.5},{check:.5,bet:.5}]){
 vm.runInContext(`state={p:${JSON.stringify(p)},answered:false,expected:'fold',roll:39};review=null;busy=false`,context);
 el('feedback').textContent='';el('feedback').className='';el('continue').hidden=true;
 vm.runInContext("answer('fold')",context);
 assert.equal(vm.runInContext('state.answered',context),false);assert.equal(el('feedback').textContent,'');assert.equal(el('continue').hidden,true);
 vm.runInContext(`answer('${Object.keys(p)[0]}')`,context);
 assert.equal(vm.runInContext('state.answered',context),true);assert.equal(el('feedback').textContent,'OK');assert.equal(el('continue').hidden,false);
}
assert(!app.includes('При числе'));assert(!app.includes('Допустимое действие'));assert(!app.includes('BB против рейза донка'));
console.log({displayedActionChecks:checked,positionColumnChecks:8,branchFilters:12,flopHandExplanationChecks:324,ignoredWrongClicks:true,allowedMixOK:true,alwaysAvailableTabs:3});
