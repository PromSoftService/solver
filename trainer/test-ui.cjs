'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),assert=require('node:assert/strict');
const D=JSON.parse(fs.readFileSync(path.resolve(process.argv[2]||'output/trainer','trainer-test-data.json'),'utf8'));
const app=fs.readFileSync(path.join(__dirname,'app.js'),'utf8');
const template=fs.readFileSync(path.join(__dirname,'index.html'),'utf8');
const elements=new Map(),selected=[];
function el(id){if(!elements.has(id))elements.set(id,{textContent:id==='trainer-data'?JSON.stringify(D):'',innerHTML:'',querySelectorAll:()=>selected});return elements.get(id)}
const context=vm.createContext({document:{getElementById:el},TrainerCore:require('./core.js'),localStorage:{getItem:()=>null},console});
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
for(const [key,s,cols]of [['donk',0,[0]],['donk',1,[1,2,3]],['vsdonk',0,[0]],['vsdonk',1,[1]],['vsxr',0,[0]],['vsxr',1,[1]],['oopcb',2,[0,1,2]],['stabdef',2,[0,1,2,3]],['dr_btn',0,[0,1,2,3,4]],['dr_utg',1,[0,1,2,3,4]]]){
 const actual=vm.runInContext(`decisionColumns('${key}',${s})`,context);assert.deepEqual(Array.from(actual),cols);
}
for(let s=0;s<3;s++)for(const n of s===2?['01','04']:['01','02','03','04','05','06']){selected.splice(0,selected.length,{value:s+':'+n});const cells=vm.runInContext('eligible()',context);assert(cells.length);assert(cells.every(c=>c.s===s&&c.n===n))}
selected.splice(0,selected.length,{value:'0:02'},{value:'1:02'});assert(vm.runInContext('eligible().every(c=>c.n==="02"&&c.s<2)',context));
selected.length=0;assert.equal(vm.runInContext('eligible().length',context),0);
for(const id of ['mode','filter','flopFilter','strict','score','reveal','studyLock','progress','covered','coverageGrid','settingsBtn'])assert(!template.includes(`id="${id}"`),`Obsolete UI ${id}`);
assert.equal((template.match(/role="tab"/g)||[]).length,3);
assert(!app.includes('unlocked'));
console.log({displayedActionChecks:checked,positionColumnChecks:10,branchFilters:14,multiSelect:true,emptySelection:true,alwaysAvailableTabs:3});
