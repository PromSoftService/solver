'use strict';
const D=JSON.parse(document.getElementById('trainer-data').textContent),C=TrainerCore,$=id=>document.getElementById(id);
const ACTION={fold:'Фолд',check:'Чек',call:'Колл',bet:'Бет ½',donk:'Донк ½',raise:'Рейз'},ORDER=['raise','bet','donk','call','check','fold'];
const KEY='flop-lab-progress-v1',cache=new Map();let state=null,busy=false,tab='decisions',serial=0;
let review=null;
// Scheduling history is internal: no scores, progress panels or counters in the UI.
let progress={version:D.version,counts:{}};
try{const p=JSON.parse(localStorage.getItem(KEY)||'null');if(p?.version===D.version&&p.counts)progress.counts=p.counts}catch{}
function persist(){try{localStorage.setItem(KEY,JSON.stringify(progress))}catch{}}
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=x=>(100*x).toFixed(1).replace('.',',')+'%';
const bb=x=>x.toFixed(1).replace('.',',')+' bb';
function card(c){const text=D.deck[c],s=text[1];return `<span class="card ${s}">${text[0]}<small>${{c:'♣',d:'♦',h:'♥',s:'♠'}[s]}</small></span>`}
async function load(bi){if(cache.has(bi))return cache.get(bi);const raw=Uint8Array.from(atob(D.blocks[bi]),c=>c.charCodeAt(0));const stream=new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'));const block=C.decodeBlock(JSON.parse(await new Response(stream).text()));cache.set(bi,block);if(cache.size>6)cache.delete(cache.keys().next().value);return block}
function eligible(){const selected=new Set([...$('branches').querySelectorAll('input[data-branch]:checked')].map(el=>el.value));return D.cells.filter(c=>selected.has(`${c.s}:${c.n}`))}
function branchBusy(value){$('branches').querySelectorAll('input').forEach(el=>el.disabled=value)}
function sampleCombo(weights,allowed){const ids=[],ws=[];weights.forEach((w,id)=>{if(w>0&&(!allowed||allowed(id))){ids.push(id);ws.push(w)}});return C.weighted(ids,ws)}
async function newHand(){
 if(busy)return;busy=true;branchBusy(true);review=null;const token=++serial;$('next').disabled=true;$('continue').hidden=true;$('actions').replaceChildren();$('feedback').textContent='Раздаём карты…';$('feedback').className='';renderTabs();
 try{
  const cells=eligible();if(!cells.length){busy=false;branchBusy(false);$('feedback').textContent='Выбери ветку для тренировки.';return}
  let cell=C.chooseCell(cells,progress.counts),s=cell.s,n=cell.n,hero=C.branch(D,s,n).actor,bi,history;
  bi=cell.boards[Math.floor(Math.random()*cell.boards.length)];history=C.prefix(s,n).map(x=>[...x,s===0&&n==='05'&&x[0]==='01']);
  const block=await load(bi),board=D.boards[bi];if(token!==serial)return;
  const hw=C.reached(D,block,s,board,history,hero,hero),vw=C.reached(D,block,s,board,history,1-hero,hero);
  const vid=vw.map((v,i)=>v>0?i:-1).filter(i=>i>=0),vtotal=vw.reduce((a,b)=>a+b,0);
  const valid=id=>{if(!block.meta[id])return false;if(cell){const sp=C.spec(D,s,n,board,block.meta[id]);if(sp?.row!==cell.r||!C.policy(D,s,n,board,block.meta[id],id))return false}return vid.some(v=>C.compatible(D,id,v))};
  // Conditional card removal: hero weight includes the compatible opponent mass.
  const adjusted=hw.map((w,id)=>w&&valid(id)?w*vid.reduce((a,v)=>a+(C.compatible(D,id,v)?vw[v]:0),0)/vtotal:0);
  const hc=sampleCombo(adjusted),vc=sampleCombo(vw,id=>hc!==null&&C.compatible(D,hc,id));if(hc===null||vc===null)throw Error('Для выбранной ячейки не нашлось совместимой пары рук.');
  state={s,n,hero,bi,block,board,hc,vc,history:[],contrib:[0,0],logs:[],cell,answered:false,target:cell?.key,finished:false};
  addLog(s===2?'UTG открылся 2,5 bb · BTN колл · остальные фолд':`${D.studies[s].actors[1]} открылся 2,5 bb · BB колл · остальные фолд`);
  $('heroAction').textContent='';$('villainAction').textContent='';renderTable();
  for(const h of history){applyHistory(h[0],h[1],h[2],true);renderTable();await delay(230);if(token!==serial)return}
  if(history.some(h=>h[2]))addLog('Учебное отклонение: BB донкнул против BTN. Это не изменение базового чека BB.');
  busy=false;if(C.branch(D,s,n).actor===hero)ask();else await advanceOpponent();
 }catch(e){busy=false;branchBusy(false);$('feedback').className='bad';$('feedback').textContent=e.message;$('next').disabled=false;console.error(e)}
}
function delay(ms){return new Promise(r=>setTimeout(r,ms))}
function addLog(text){state.logs.push(text);$('history').innerHTML=state.logs.map(s=>'<li>'+escapeHTML(s)+'</li>').join('')}
function actionText(s,n,a,contrib){const b=C.branch(D,s,n);if(a==='raise')return `${ACTION[a]} до ${bb(b.raiseTo)}`;if(a==='bet'||a==='donk')return `${ACTION[a]} · ${bb(b.bet)}`;if(a==='call'){const actor=b.actor;return `${ACTION[a]} ${bb(Math.max(0,contrib[1-actor]-contrib[actor]))}`}return ACTION[a]}
function applyHistory(n,a,deviation=false,replay=false){const q=state,b=C.branch(D,q.s,n),actor=b.actor,text=actionText(q.s,n,a,q.contrib);if(a==='bet'||a==='donk')q.contrib[actor]+=b.bet;if(a==='raise')q.contrib[actor]=b.raiseTo;if(a==='call')q.contrib[actor]=q.contrib[1-actor];q.history.push([n,a,deviation]);addLog(`${D.studies[q.s].actors[actor]}: ${text}${replay?' · до учебного решения':''}`);$(actor===q.hero?'heroAction':'villainAction').textContent=text}
function renderTable(){if(!state)return;const q=state,st=D.studies[q.s];$('spot').textContent=st.actors.join(' vs ');$('board').innerHTML=q.board.split(' ').map(c=>card(D.deck.indexOf(c))).join('');$('hole').innerHTML=D.combos[q.hc].map(card).join('');$('heroPos').textContent='Вы · '+st.actors[q.hero];$('villainPos').textContent=st.actors[1-q.hero];$('heroStack').textContent=bb(97.5-q.contrib[q.hero]);$('villainStack').textContent=bb(97.5-q.contrib[1-q.hero]);$('pot').textContent='Банк '+bb(st.pot+q.contrib[0]+q.contrib[1]);}
function ask(){
 const q=state,sp=C.spec(D,q.s,q.n,q.board,q.block.meta[q.hc]),p=C.policy(D,q.s,q.n,q.board,q.block.meta[q.hc],q.hc);
 if(!p){finish('Для этой руки в выбранной учебной таблице нет действия. Продолжение не оценивается.');return}
 q.sp=sp;q.p=p;q.answered=false;q.roll=Math.floor(Math.random()*100);q.expected=pickRoll(p,q.roll);branchBusy(false);
 review={...q,history:q.history.map(h=>[...h]),contrib:[...q.contrib]};
 const key=C.cellKey(q.s,q.n,C.nine(q.board),sp.row);
 if(q.target===key){progress.counts[key]=(progress.counts[key]||0)+1;q.target=null}persist();
 $('decisionLabel').textContent=C.NAMES[q.s][q.n];$('handClass').textContent='Твоё решение';$('randomizer').textContent=String(q.roll).padStart(2,'0');$('feedback').textContent='';$('feedback').className='';$('continue').hidden=true;$('next').disabled=false;
 const actions=C.branch(D,q.s,q.n).actions;
 $('actions').innerHTML=actions.map(a=>`<button class="${a}" data-action="${a}">${ACTION[a]}<small>${a==='raise'?'до '+bb(C.branch(D,q.s,q.n).raiseTo):['bet','donk'].includes(a)?bb(C.branch(D,q.s,q.n).bet):a==='call'?bb(Math.max(0,q.contrib[1-q.hero]-q.contrib[q.hero])):' '}</small></button>`).join('');
 $('actions').querySelectorAll('button').forEach(b=>b.onclick=()=>answer(b.dataset.action));renderTabs();
}
function pickRoll(p,roll){let total=0;for(const a of ORDER){total+=100*(p[a]||0);if(roll<total-1e-9)return a}return Object.keys(p).at(-1)}
function answer(a){
 if(!state||state.answered||busy)return;const q=state;
 if(!(q.p[a]>0))return;
 q.answered=true;q.selected=a;
 $('actions').querySelectorAll('button').forEach(b=>b.disabled=true);$('feedback').className='good';
 $('feedback').textContent='OK';
 $('continue').hidden=false;$('next').disabled=false;renderTabs();
}
async function continueHand(){if(!state||busy||!state.answered)return;busy=true;branchBusy(true);const q=state;$('next').disabled=true;$('continue').hidden=true;applyHistory(q.n,q.selected);renderTable();const n=C.next(q.s,q.n,q.selected);if(!n){finish(q.selected==='fold'?'Фолд.':q.selected==='raise'?'Рейз.':'Флоп сыгран.');busy=false;return}q.n=n;await delay(450);busy=false;await advanceOpponent()}
async function advanceOpponent(){
 const q=state;if(!q||q.finished)return;
 if(C.branch(D,q.s,q.n).actor===q.hero){ask();return}
 busy=true;branchBusy(true);$('actions').replaceChildren();$('decisionLabel').textContent='Оппонент принимает решение…';$('feedback').textContent='';$('next').disabled=true;
 await delay(650);const p=C.solver(D,q.block,q.s,q.n,q.vc);
 if(!p){finish('Продолжение не разобрано.');busy=false;return}
 const a=C.sample(p);applyHistory(q.n,a);renderTable();const n=C.next(q.s,q.n,a);busy=false;
 if(!n){finish(a==='fold'?'Оппонент выбросил карты.':a==='raise'?'Оппонент сделал рейз.':'Флоп сыгран.');return}
 q.n=n;if(C.branch(D,q.s,n).actor===q.hero)ask();else await advanceOpponent();
}
function finish(text){state.finished=true;branchBusy(false);$('decisionLabel').textContent='Раздача завершена';$('feedback').textContent=text;$('feedback').className='';$('actions').replaceChildren();$('continue').hidden=true;$('next').disabled=false;addLog(text)}
function renderTabs(){document.querySelectorAll('.tabs button').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===tab)));for(const k of ['decisions','ranges','explanation'])$(k).hidden=tab!==k;if(!review?.sp){$(tab).innerHTML='<p class="note">Выбери ветки и дождись раздачи.</p>';return}$('handClass').textContent=D.nine[C.nine(review.board)]+' · '+D.rows[review.sp.row]+(review.block.meta[review.hc][2]?' · БДФД':'');if(tab==='decisions')renderDecisions();if(tab==='ranges')renderRanges();if(tab==='explanation')renderExplanation()}
function label(cid){const[a,b]=D.combos[cid].map(i=>D.deck[i]),r='AKQJT98765432',rs=[a[0],b[0]].sort((x,y)=>r.indexOf(x)-r.indexOf(y));return rs[0]+rs[1]+(a[0]===b[0]?'':a[1]===b[1]?'s':'o')}
// Presentation only. Effective actions always come from the approved full table.
const BASES={cb_btn:['B','B','БД','X/B','X/B','X','X/B','X/B','B','БД','X/B','X/B'],cb_utg:['B','B','БД','X/B','X/B','X','X/B','X/B','B','БД','X/B','X/B'],df_btn:['R','R','C','C','C','C','C','F','R/C','R/C','C','F'],df_utg:['R','R/C','C','C','C','F','C','F','R/C','R/C','C','F']};
function standardAt(key,r,g){if(key.startsWith('cb_')){if(r===1&&[4,6].includes(g))return 'X/B';if(r===7&&[3,4,6].includes(g))return 'X'}return BASES[key][r]}
function actionChip(value){const cls=({'X':'check','F':'check','C':'call','B':'bet','R':'bet','X/B':'mix','B/X':'mix','R/C':'mix','C/R':'mix','БД':'bd','ДРО':'bd'}[value])||(value.includes('/')?'mix':'bd');return value==='—'?'<span class="no-hand">—</span>':`<b class="action-chip ${cls}">${escapeHTML(value)}</b>`}
function flopColor(i){return ['vs','dry','partial','partial','partial','connected','connected','ace','ace'][i]}
function standardMarkup(key,r){if(key.startsWith('cb_')&&[1,7].includes(r)){const titles=r===1?['Высокие','Низкие']:['Высокая младшая','Низкая младшая'],values=r===1?['B','X/B']:['X/B','X'];return `<div class="split-standard">${titles.map((t,i)=>`<div><small>${t}</small>${actionChip(values[i])}</div>`).join('')}</div>`}return actionChip(BASES[key][r])}
function decisionColumns(key,s){const columns=D.tables[key].columns.map((_,i)=>i);if(key==='donk')return s===0?[0]:[1,2,3];if(['vsdonk','vsxr'].includes(key))return [s];return columns}
function renderDecisions(){
 const q=review,key=q.sp.key,t=D.tables[key];let body;
 if(BASES[key]){
  const preferred=key.startsWith('cb_')?[0,1,2,5,6,7,8]:[0,2,4,5,6,7,8];
  const columns=[...new Set([...preferred,...t.columns.map((_,i)=>i).filter(g=>t.rows.some((row,r)=>row[g]!=='—'&&row[g]!==standardAt(key,r,g)))])].sort((a,b)=>a-b);
  body=`<table class="reference-table"><thead><tr><th>Рука · стандартное действие</th><th>Уточнения по флопам</th></tr></thead><tbody>`+t.rows.map((row,r)=>{
   const slots=[];for(let j=0;j<columns.length;){const g=columns[j],v=row[g],correction=v==='—'||v===standardAt(key,r,g)?'':v;let end=j+1;
    while(end<columns.length&&columns[end]===columns[end-1]+1&&flopColor(columns[end])===flopColor(g)){const ng=columns[end],nv=row[ng],next=nv==='—'||nv===standardAt(key,r,ng)?'':nv;if(next!==correction)break;end++}
    const gs=columns.slice(j,end),active=r===q.sp.row&&gs.includes(q.sp.col);
    slots.push(`<div class="correction ${flopColor(g)}${active?' selected-correction':''}" data-flops="${gs.join(',')}" data-action="${escapeHTML(correction)}" style="grid-column:${j+1}/span ${end-j}"><span>${gs.map(i=>D.nine[i]).join(' / ')}</span>${correction?actionChip(correction):''}</div>`);j=end;
   }
   return `<tr data-hand-row="${r}" class="${r===q.sp.row?'selected-hand':''}"><th scope="row"><span class="hand-name">${D.rows[r]}</span><div class="standard-action">${standardMarkup(key,r)}</div></th><td><div class="correction-strip" style="--slots:${columns.length}">${slots.join('')}</div></td></tr>`;
  }).join('')+'</tbody></table>';
 }else{
  const columns=decisionColumns(key,q.s);
  body=`<div class="scroll"><table class="reference-table full-reference"><thead><tr><th>Рука</th>${columns.map(c=>`<th class="${flopColor(c)}">${escapeHTML(t.columns[c])}</th>`).join('')}</tr></thead><tbody>`+t.rows.map((row,r)=>`<tr class="${r===q.sp.row?'selected-hand':''}"><th scope="row">${q.sp.legacy&&[8,9].includes(r)?D.rows[r].replace(' без пары',''):D.rows[r]}</th>${columns.map(c=>`<td class="${flopColor(c)}${r===q.sp.row&&c===q.sp.col?' selected-correction':''}">${actionChip(row[c])}</td>`).join('')}</tr>`).join('')+'</tbody></table></div>';
 }
 $('decisions').innerHTML=`<div class="reference-heading">${escapeHTML(C.NAMES[q.s][q.n])}</div><div class="reference-sheet">${body}</div>`;
}
function rangeData(actor){const q=review,w=C.reached(D,q.block,q.s,q.board,q.history,actor,q.hero),tot=w.reduce((a,b)=>a+b,0),groups={},composition=Array(12).fill(0);w.forEach((weight,id)=>{if(!weight)return;const l=label(id);if(!groups[l])groups[l]={w:0,ids:[]};groups[l].w+=weight;groups[l].ids.push([id,weight]);composition[C.row(q.block.meta[id])]+=weight});return{w,tot,groups,composition:composition.map(v=>tot?v/tot:0)}}
function matrixHTML(data,actor){const rr='AKQJT98765432';let h=`<section><div class="range-title">${D.studies[review.s].actors[actor]} · ${data.tot.toFixed(1)} взвешенных комбинаций</div><div class="matrix">`;for(let i=0;i<13;i++)for(let j=0;j<13;j++){const l=i===j?rr[i]+rr[j]:i<j?rr[i]+rr[j]+'s':rr[j]+rr[i]+'o',g=data.groups[l],max=i===j?6:i<j?4:12,v=g?g.w/max:0;h+=`<button data-range="${actor}" data-combo="${l}" class="${g?'':'empty'}" title="${l}: ${g?g.w.toFixed(2):0} комбинаций"><i style="height:${Math.min(100,100*v)}%"></i><span>${l}</span></button>`}return h+`</div><div class="range-detail" id="rangeDetail${actor}">Нажми на руку, чтобы увидеть её вес после пройденных действий.</div></section>`}
function renderRanges(){const q=review,h=rangeData(q.hero),v=rangeData(1-q.hero);let compare='<section class="compare"><div class="range-title">Преимущество по составу</div><table><thead><tr><th>Руки</th><th>Вы</th><th>Соперник</th></tr></thead><tbody>';D.rows.forEach((r,i)=>{compare+=`<tr><td>${r}</td><td class="${h.composition[i]>v.composition[i]?'ahead':''}">${pct(h.composition[i])}</td><td class="${v.composition[i]>h.composition[i]?'ahead':''}">${pct(v.composition[i])}</td></tr>`});compare+='</tbody></table><p class="fine">Подсвечена большая доля категории. Это сравнение состава, не эквити и не автоматический вывод о выгоде ставки. Пары с дро считаются парами.</p></section>';
 $('ranges').innerHTML='<p class="note">Только дошедшие руки: префлоп-вес × собственные действия по истории. У вас — принятая учебная стратегия, у соперника — сохранённые частоты солвера. Диапазоны исключают карты флопа, но не раскрывают конкретные закрытые карты игроков. Это не повторное решение солвера.</p><div class="range-layout">'+matrixHTML(h,q.hero)+compare+matrixHTML(v,1-q.hero)+'</div>';
 $('ranges').querySelectorAll('button[data-range]').forEach(b=>b.onclick=()=>{const actor=Number(b.dataset.range),g=(actor===q.hero?h:v).groups[b.dataset.combo];$('rangeDetail'+actor).textContent=g?`${b.dataset.combo}: ${g.ids.map(([id,w])=>D.combos[id].map(c=>D.deck[c]).join('')+' '+pct(w)).join(' · ')}`:`${b.dataset.combo}: не доходит до этого решения.`});
}
function renderExplanation(){
 const g=C.nine(review.board),items=C.explanations(D,g);
 if(!items.length){$('explanation').innerHTML='';return}
 const summaries=items.map(([key,item])=>`<section class="case-summary"><a href="#case-${key}">${escapeHTML(item.kind)} · ${escapeHTML(item.title)}</a>${item.lead}</section>`).join('');
 const full=items.map(([key,item])=>`<section class="full-case" id="case-${key}"><div class="case-kind">${escapeHTML(item.kind)}</div>${item.html}</section>`).join('');
 $('explanation').innerHTML=`<h2>${escapeHTML(D.nine[g])}</h2><div class="case-summaries">${summaries}</div>${full}`;
}
$('next').onclick=newHand;$('continue').onclick=continueHand;
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;renderTabs()});
const BRANCH_LABELS=['Донк BB','C-bet','BB против c-bet','Против чек-рейза','Против донка'];
$('branches').innerHTML=['BTN vs BB','UTG vs BB','UTG vs BTN'].map((name,s)=>`<fieldset><legend><label><input type="checkbox" data-group="${s}" checked> ${name}</label></legend>${(s===2?['01','04']:['01','02','03','04','05']).map(n=>`<label class="branch-option"><input type="checkbox" data-branch value="${s}:${n}" checked> ${s===2?(n==='01'?'C-bet UTG':'UTG против ставки BTN'):BRANCH_LABELS[Number(n)-1]}</label>`).join('')}</fieldset>`).join('');
$('branches').onchange=e=>{const input=e.target;if(input.dataset.group!==undefined)$('branches').querySelectorAll(`input[data-branch][value^="${input.dataset.group}:"]`).forEach(el=>el.checked=input.checked);$('branches').querySelectorAll('input[data-group]').forEach(el=>{const items=[...$('branches').querySelectorAll(`input[data-branch][value^="${el.dataset.group}:"]`)];el.checked=items.every(i=>i.checked);el.indeterminate=!el.checked&&items.some(i=>i.checked)});newHand()};
if(typeof DecompressionStream==='undefined'){$('feedback').className='error';$('feedback').textContent='Нужен современный Chrome, Edge, Firefox или Safari.'}else newHand();
