'use strict';
const D=JSON.parse(document.getElementById('trainer-data').textContent),C=TrainerCore,$=id=>document.getElementById(id);
const ACTION={fold:'Фолд',check:'Чек',call:'Колл',bet:'Бет ½',donk:'Донк ½',raise:'Рейз'},ORDER=['raise','bet','donk','call','check','fold'];
const KEY='flop-lab-progress-v1',cache=new Map();let state=null,busy=false,tab='decisions',unlocked=false,serial=0;
let review=null;
let progress={version:D.version,counts:{},encounters:{},decisions:0,correct:0,mixCorrect:0,hands:0};
try{const p=JSON.parse(localStorage.getItem(KEY)||'null');if(p&&p.version===D.version)progress=p;$('storageStatus').textContent='Прогресс сохраняется в этом браузере. Для переноса используй экспорт в настройках.'}catch{$('storageStatus').textContent='Браузер не разрешил сохранение. Используй экспорт прогресса; до закрытия страницы счётчики работают.'}
function persist(){try{localStorage.setItem(KEY,JSON.stringify(progress))}catch{$('storageStatus').textContent='Автосохранение недоступно. Сохрани прогресс через настройки.'}}
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const pct=x=>(100*x).toFixed(1).replace('.',',')+'%';
const bb=x=>x.toFixed(1).replace('.',',')+' bb';
function card(c){const text=D.deck[c],s=text[1];return `<span class="card ${s}">${text[0]}<small>${{c:'♣',d:'♦',h:'♥',s:'♠'}[s]}</small></span>`}
async function load(bi){if(cache.has(bi))return cache.get(bi);const raw=Uint8Array.from(atob(D.blocks[bi]),c=>c.charCodeAt(0));const stream=new Blob([raw]).stream().pipeThrough(new DecompressionStream('gzip'));const block=C.decodeBlock(JSON.parse(await new Response(stream).text()));cache.set(bi,block);if(cache.size>6)cache.delete(cache.keys().next().value);return block}
function eligible(){return D.cells.filter(c=>($('filter').value==='all'||`${c.s}:${c.n}`===$('filter').value)&&($('flopFilter').value==='all'||c.g===Number($('flopFilter').value)))}
function updateCoverage(){
 const cells=eligible(),ns=cells.map(c=>progress.counts[c.key]||0),covered=ns.filter(x=>x>0).length;
 $('covered').textContent=covered;$('cellTotal').textContent=`из ${cells.length} ячеек`;$('progress').max=cells.length||1;$('progress').value=covered;
 $('spread').textContent=cells.length?`Целевые показы: ${Math.min(...ns)}–${Math.max(...ns)}. Следующая — из наименее показанных.`:'В этом фильтре нет достижимых учебных ячеек.';
 $('score').textContent=`${progress.decisions} решений · ${progress.decisions?Math.round(100*progress.correct/progress.decisions):0}% допустимых`;
 const groups=new Map();for(const c of cells){let k=c.s+':'+c.n;if(!groups.has(k))groups.set(k,[0,0,C.NAMES[c.s][c.n]]);const v=groups.get(k);v[1]++;if(progress.counts[c.key])v[0]++}
 $('coverageSummary').innerHTML=[...groups.values()].map(v=>`<div><span>${v[2]}</span><span>${v[0]}/${v[1]}</span></div>`).join('');
 $('coverageGrid').innerHTML='<table><thead><tr><th>Ячейка</th><th>Показы</th></tr></thead><tbody>'+cells.map(c=>`<tr><td>${C.NAMES[c.s][c.n]} · ${D.nine[c.g]} · ${D.rows[c.r]}</td><td>${progress.counts[c.key]||0}</td></tr>`).join('')+'</tbody></table>';
}
function sampleCombo(weights,allowed){const ids=[],ws=[];weights.forEach((w,id)=>{if(w>0&&(!allowed||allowed(id))){ids.push(id);ws.push(w)}});return C.weighted(ids,ws)}
async function newHand(){
 if(busy)return;busy=true;review=null;const token=++serial;$('next').disabled=true;$('continue').hidden=true;$('actions').replaceChildren();$('feedback').textContent='Раздаём карты…';$('feedback').className='';$('reveal').disabled=true;unlocked=false;renderTabs();
 try{
  const cells=eligible();if(!cells.length)throw Error('Нет доступных ячеек. Измени фильтр.');
  let cell=C.chooseCell(cells,progress.counts),s=cell.s,n=cell.n,hero=C.branch(D,s,n).actor,bi,history;
  if($('mode').value==='free'){
   const options=[...new Set(cells.map(c=>c.s+':'+C.branch(D,c.s,c.n).actor))];const selection=options[Math.floor(Math.random()*options.length)].split(':').map(Number);[s,hero]=selection;
   const boards=D.boards.map((b,i)=>i).filter(i=>$('flopFilter').value==='all'||C.nine(D.boards[i])===Number($('flopFilter').value));bi=boards[Math.floor(Math.random()*boards.length)];n='01';history=[];cell=null;
  }else{bi=cell.boards[Math.floor(Math.random()*cell.boards.length)];history=C.prefix(s,n).map(x=>[...x,s===0&&['05','06'].includes(n)&&x[0]==='01'])}
  const block=await load(bi),board=D.boards[bi];if(token!==serial)return;
  const hw=C.reached(D,block,s,board,history,hero,hero),vw=C.reached(D,block,s,board,history,1-hero,hero);
  const vid=vw.map((v,i)=>v>0?i:-1).filter(i=>i>=0),vtotal=vw.reduce((a,b)=>a+b,0);
  const valid=id=>{if(!block.meta[id])return false;if(cell){const sp=C.spec(D,s,n,board,block.meta[id]);if(sp?.row!==cell.r||!C.policy(D,s,n,board,block.meta[id],id))return false}return vid.some(v=>C.compatible(D,id,v))};
  // Conditional card removal: hero weight includes the compatible opponent mass.
  const adjusted=hw.map((w,id)=>w&&valid(id)?w*vid.reduce((a,v)=>a+(C.compatible(D,id,v)?vw[v]:0),0)/vtotal:0);
  const hc=sampleCombo(adjusted),vc=sampleCombo(vw,id=>hc!==null&&C.compatible(D,hc,id));if(hc===null||vc===null)throw Error('Для выбранной ячейки не нашлось совместимой пары рук.');
  state={s,n,hero,bi,block,board,hc,vc,history:[],contrib:[0,0],logs:[],cell,answered:false,target:cell?.key,finished:false};
  progress.hands++;persist();$('handNo').textContent=`Раздача ${progress.hands}`;
  addLog(s===2?'UTG открылся 2,5 bb · BTN колл · остальные фолд':`${D.studies[s].actors[1]} открылся 2,5 bb · BB колл · остальные фолд`);
  $('heroAction').textContent='';$('villainAction').textContent='';renderTable();
  for(const h of history){applyHistory(h[0],h[1],h[2],true);renderTable();await delay(230);if(token!==serial)return}
  if(history.some(h=>h[2]))addLog('Учебное отклонение: BB донкнул против BTN. Это не изменение базового чека BB.');
  busy=false;if(C.branch(D,s,n).actor===hero)ask();else await advanceOpponent();
 }catch(e){busy=false;$('feedback').className='bad';$('feedback').textContent=e.message;$('next').disabled=false;console.error(e)}
}
function delay(ms){return new Promise(r=>setTimeout(r,ms))}
function addLog(text){state.logs.push(text);$('history').innerHTML=state.logs.map(s=>'<li>'+escapeHTML(s)+'</li>').join('')}
function actionText(s,n,a,contrib){const b=C.branch(D,s,n);if(a==='raise')return `${ACTION[a]} до ${bb(b.raiseTo)}`;if(a==='bet'||a==='donk')return `${ACTION[a]} · ${bb(b.bet)}`;if(a==='call'){const actor=b.actor;return `${ACTION[a]} ${bb(Math.max(0,contrib[1-actor]-contrib[actor]))}`}return ACTION[a]}
function applyHistory(n,a,deviation=false,replay=false){const q=state,b=C.branch(D,q.s,n),actor=b.actor,text=actionText(q.s,n,a,q.contrib);if(a==='bet'||a==='donk')q.contrib[actor]+=b.bet;if(a==='raise')q.contrib[actor]=b.raiseTo;if(a==='call')q.contrib[actor]=q.contrib[1-actor];q.history.push([n,a,deviation]);addLog(`${D.studies[q.s].actors[actor]}: ${text}${replay?' · до учебного решения':''}`);$(actor===q.hero?'heroAction':'villainAction').textContent=text}
function renderTable(){if(!state)return;const q=state,st=D.studies[q.s];$('spot').textContent=st.actors.join(' vs ')+' · '+($('mode').value==='balanced'?'равномерная практика':'свободная игра');$('board').innerHTML=q.board.split(' ').map(c=>card(D.deck.indexOf(c))).join('');$('hole').innerHTML=D.combos[q.hc].map(card).join('');$('heroPos').textContent='Вы · '+st.actors[q.hero];$('villainPos').textContent=st.actors[1-q.hero];$('heroStack').textContent=bb(97.5-q.contrib[q.hero]);$('villainStack').textContent=bb(97.5-q.contrib[1-q.hero]);$('pot').textContent='Банк '+bb(st.pot+q.contrib[0]+q.contrib[1]);}
function ask(){
 const q=state,sp=C.spec(D,q.s,q.n,q.board,q.block.meta[q.hc]),p=C.policy(D,q.s,q.n,q.board,q.block.meta[q.hc],q.hc);
 if(!p){finish('Для этой руки в выбранной учебной таблице нет действия. Продолжение не оценивается.');return}
 q.sp=sp;q.p=p;q.answered=false;q.roll=Math.floor(Math.random()*100);q.expected=pickRoll(p,q.roll);unlocked=false;
 review={...q,history:q.history.map(h=>[...h]),contrib:[...q.contrib]};
 const key=C.cellKey(q.s,q.n,C.nine(q.board),sp.row);progress.encounters[key]=(progress.encounters[key]||0)+1;
 if(q.target===key){progress.counts[key]=(progress.counts[key]||0)+1;q.target=null}persist();updateCoverage();
 $('decisionLabel').textContent=C.NAMES[q.s][q.n];$('handClass').textContent='Твоё решение';$('randomizer').textContent=String(q.roll).padStart(2,'0');$('feedback').textContent='';$('feedback').className='';$('continue').hidden=true;$('next').disabled=true;$('reveal').disabled=false;
 const actions=C.branch(D,q.s,q.n).actions;
 $('actions').innerHTML=actions.map(a=>`<button class="${a}" data-action="${a}">${ACTION[a]}<small>${a==='raise'?'до '+bb(C.branch(D,q.s,q.n).raiseTo):['bet','donk'].includes(a)?bb(C.branch(D,q.s,q.n).bet):a==='call'?bb(Math.max(0,q.contrib[1-q.hero]-q.contrib[q.hero])):' '}</small></button>`).join('');
 $('actions').querySelectorAll('button').forEach(b=>b.onclick=()=>answer(b.dataset.action));renderTabs();
}
function pickRoll(p,roll){let total=0;for(const a of ORDER){total+=100*(p[a]||0);if(roll<total-1e-9)return a}return Object.keys(p).at(-1)}
function answer(a){
 if(!state||state.answered||busy)return;const q=state;q.answered=true;q.selected=a;progress.decisions++;const allowed=(q.p[a]||0)>0,matched=a===q.expected;if(allowed)progress.correct++;if(matched)progress.mixCorrect++;persist();
 $('actions').querySelectorAll('button').forEach(b=>b.disabled=true);$('feedback').className=allowed?'good':'bad';
 const dist=ORDER.filter(k=>q.p[k]).map(k=>`${ACTION[k]} ${Math.round(q.p[k]*100)}%`).join(' · ');
 $('feedback').textContent=(allowed?(matched?'Верно. ':'Допустимое действие микса. '):'По нашей стратегии здесь другое действие. ')+dist+($('strict').checked&&!matched?` При числе ${q.roll}: ${ACTION[q.expected]}.`:'');
 unlocked=true;$('continue').hidden=false;$('next').disabled=false;renderTabs();updateCoverage();
}
async function continueHand(){if(!state||busy||!state.answered)return;busy=true;const q=state;$('continue').hidden=true;applyHistory(q.n,q.selected);renderTable();const n=C.next(q.s,q.n,q.selected);if(!n){finish(q.selected==='fold'?'Ты выбросил карты.':'Флоп сыгран. Следующие улицы в эту версию не входят.');busy=false;return}q.n=n;await delay(450);busy=false;await advanceOpponent()}
async function advanceOpponent(){
 const q=state;if(!q||q.finished)return;
 if(C.branch(D,q.s,q.n).actor===q.hero){ask();return}
 busy=true;$('actions').replaceChildren();$('decisionLabel').textContent='Оппонент принимает решение…';$('feedback').textContent='';$('next').disabled=true;
 await delay(650);const p=C.solver(D,q.block,q.s,q.n,q.vc);
 if(!p){finish('Для продолжения этой конкретной руки нет сохранённого ответа. Не подставляем выдуманную стратегию.');busy=false;return}
 const a=C.sample(p);applyHistory(q.n,a);renderTable();const n=C.next(q.s,q.n,a);busy=false;
 if(!n){finish(a==='fold'?'Оппонент выбросил карты.':q.s===2&&a==='raise'?'Оппонент сделал рейз. Ответ на него в этой ветке ещё не разобран.':'Флоп сыгран. Переход к тёрну не моделируется.');return}
 q.n=n;if(C.branch(D,q.s,n).actor===q.hero)ask();else await advanceOpponent();
}
function finish(text){state.finished=true;$('decisionLabel').textContent='Раздача завершена';$('feedback').textContent=text;$('feedback').className='';$('actions').replaceChildren();$('continue').hidden=true;$('next').disabled=false;$('reveal').disabled=!state.sp;addLog(text)}
function renderTabs(){document.querySelectorAll('.tabs button').forEach(b=>b.setAttribute('aria-selected',String(b.dataset.tab===tab)));$('studyLock').hidden=unlocked;for(const k of ['decisions','ranges','explanation'])$(k).hidden=!unlocked||tab!==k;if(!unlocked||!review?.sp)return;$('handClass').textContent=D.nine[C.nine(review.board)]+' · '+D.rows[review.sp.row]+(review.block.meta[review.hc][2]?' · БДФД':'');if(tab==='decisions')renderDecisions();if(tab==='ranges')renderRanges();if(tab==='explanation')renderExplanation()}
function renderDecisions(){const q=review,t=D.tables[q.sp.key];const ptext=ORDER.filter(k=>q.p[k]).map(k=>`${ACTION[k]} ${Math.round(q.p[k]*100)}%`).join(' · ');$('decisions').innerHTML=`<p class="note"><span class="badge">${C.NAMES[q.s][q.n]}</span> · ${q.sp.legacy?'Здесь сохранён приоритет дро старой таблицы.':'Пары с дро остаются парами.'}</p><p class="short-rule">${D.rows[q.sp.row]}: ${escapeHTML(q.sp.label)} → ${ptext}</p><div class="scroll"><table><thead><tr><th>Рука</th>${t.columns.map(h=>'<th>'+escapeHTML(h)+'</th>').join('')}</tr></thead><tbody>${t.rows.map((rr,r)=>`<tr class="${r===q.sp.row?'current-row':''}"><td>${D.rows[r]}</td>${rr.map((v,c)=>`<td class="${r===q.sp.row&&c===q.sp.col?'active-cell':''}">${escapeHTML(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div><p class="fine">БД в c-bet: с БДФД B, без X/B. БД в защите: с БДФД C, без F. ДРО: C с гатшотом или OESD, иначе F. R/C и X/B — 50/50. Нижние числа рандомайзера отданы более агрессивному действию.</p>`;}
function label(cid){const[a,b]=D.combos[cid].map(i=>D.deck[i]),r='AKQJT98765432',rs=[a[0],b[0]].sort((x,y)=>r.indexOf(x)-r.indexOf(y));return rs[0]+rs[1]+(a[0]===b[0]?'':a[1]===b[1]?'s':'o')}
function rangeData(actor){const q=review,w=C.reached(D,q.block,q.s,q.board,q.history,actor,q.hero),tot=w.reduce((a,b)=>a+b,0),groups={},composition=Array(12).fill(0);w.forEach((weight,id)=>{if(!weight)return;const l=label(id);if(!groups[l])groups[l]={w:0,ids:[]};groups[l].w+=weight;groups[l].ids.push([id,weight]);composition[C.row(q.block.meta[id])]+=weight});return{w,tot,groups,composition:composition.map(v=>tot?v/tot:0)}}
function matrixHTML(data,actor){const rr='AKQJT98765432';let h=`<section><div class="range-title">${D.studies[review.s].actors[actor]} · ${data.tot.toFixed(1)} взвешенных комбинаций</div><div class="matrix">`;for(let i=0;i<13;i++)for(let j=0;j<13;j++){const l=i===j?rr[i]+rr[j]:i<j?rr[i]+rr[j]+'s':rr[j]+rr[i]+'o',g=data.groups[l],max=i===j?6:i<j?4:12,v=g?g.w/max:0;h+=`<button data-range="${actor}" data-combo="${l}" class="${g?'':'empty'}" title="${l}: ${g?g.w.toFixed(2):0} комбинаций"><i style="height:${Math.min(100,100*v)}%"></i><span>${l}</span></button>`}return h+`</div><div class="range-detail" id="rangeDetail${actor}">Нажми на руку, чтобы увидеть её вес после пройденных действий.</div></section>`}
function renderRanges(){const q=review,h=rangeData(q.hero),v=rangeData(1-q.hero);let compare='<section class="compare"><div class="range-title">Преимущество по составу</div><table><thead><tr><th>Руки</th><th>Вы</th><th>Соперник</th></tr></thead><tbody>';D.rows.forEach((r,i)=>{compare+=`<tr><td>${r}</td><td class="${h.composition[i]>v.composition[i]?'ahead':''}">${pct(h.composition[i])}</td><td class="${v.composition[i]>h.composition[i]?'ahead':''}">${pct(v.composition[i])}</td></tr>`});compare+='</tbody></table><p class="fine">Подсвечена большая доля категории. Это сравнение состава, не эквити и не автоматический вывод о выгоде ставки. Пары с дро считаются парами.</p></section>';
 $('ranges').innerHTML='<p class="note">Только дошедшие руки: префлоп-вес × собственные действия по истории. У вас — принятая учебная стратегия, у соперника — сохранённые частоты солвера. Диапазоны исключают карты флопа, но не раскрывают конкретные закрытые карты игроков. Это не повторное решение солвера.</p><div class="range-layout">'+matrixHTML(h,q.hero)+compare+matrixHTML(v,1-q.hero)+'</div>';
 $('ranges').querySelectorAll('button[data-range]').forEach(b=>b.onclick=()=>{const actor=Number(b.dataset.range),g=(actor===q.hero?h:v).groups[b.dataset.combo];$('rangeDetail'+actor).textContent=g?`${b.dataset.combo}: ${g.ids.map(([id,w])=>D.combos[id].map(c=>D.deck[c]).join('')+' '+pct(w)).join(' · ')}`:`${b.dataset.combo}: не доходит до этого решения.`});
}
function renderExplanation(){const q=review,key=C.explanation(q.s,q.n,C.nine(q.board),q.sp.row);$('explanation').innerHTML=key?'<p class="note">Зафиксированный разбор из мануала. Числа относятся к указанным в нём группам флопов, а не только к текущему конкретному флопу.</p>'+D.explanations[key]:'<div class="empty-message"><h2>Отдельного разбора пока нет</h2><p>Для этой ситуации есть принятое действие в таблице. Новое обоснование здесь не придумано.</p></div>'}
function saveDownload(name,text){const a=document.createElement('a'),url=URL.createObjectURL(new Blob([text],{type:'application/json'}));a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)}
$('settingsBtn').onclick=()=>$('settings').hidden=!$('settings').hidden;
$('applySettings').onclick=()=>{if(busy)return;$('settings').hidden=true;newHand()};
$('next').onclick=newHand;$('continue').onclick=continueHand;$('reveal').onclick=$('unlock').onclick=()=>{unlocked=true;renderTabs()};
document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{tab=b.dataset.tab;renderTabs()});
for(const id of ['filter','flopFilter'])$(id).onchange=updateCoverage;
$('exportProgress').onclick=()=>saveDownload('flop-lab-progress.json',JSON.stringify(progress,null,2));
$('importProgress').onchange=async e=>{try{const p=JSON.parse(await e.target.files[0].text());if(p.version!==D.version||!p.counts||!p.encounters||!Number.isFinite(p.decisions))throw Error('Файл другой версии или повреждён.');for(const [k,v] of Object.entries(p.counts))if(!D.cells.some(c=>c.key===k)||!Number.isSafeInteger(v)||v<0)throw Error('Некорректные счётчики.');progress=p;persist();updateCoverage()}catch(e){alert(e.message)}};
$('reset').onclick=()=>{if(!confirm('Сбросить прогресс этой версии тренажёра?'))return;progress={version:D.version,counts:{},encounters:{},decisions:0,correct:0,mixCorrect:0,hands:0};persist();updateCoverage()};
for(let s=0;s<3;s++)for(const n of s===2?['01','04']:['01','02','03','04','05','06']){const o=document.createElement('option');o.value=s+':'+n;o.textContent=C.NAMES[s][n];$('filter').append(o)}
D.nine.forEach((g,i)=>{const o=document.createElement('option');o.value=i;o.textContent=g;$('flopFilter').append(o)});
$('provenance').innerHTML=`<p>Версия ${D.version}. 286 флопов, 3 ситуации, 16 исходных узлов, 14 учебных веток. BTN против UTG используется только как соперник. Источник стратегии: strategy_unified_flops.md, SHA-256 <code>${D.manualSHA}</code>.</p><p>Две пары+ в защите взяты из MD, где остаются различия R / R/C. Отдельное упрощение старой HTML-шпаргалки сюда не перенесено. Сам мануал не изменён.</p>`;
if(typeof DecompressionStream==='undefined'){$('feedback').className='error';$('feedback').textContent='Для распаковки встроенных данных нужен современный Chrome, Edge, Firefox или Safari. Сервер не нужен.'}else{updateCoverage();newHand()}
