/* Pure trainer domain logic. No browser access; also tested with Node. */
(function(root){
'use strict';
const PREFIX={0:{'01':[],'02':[['01','check']],'03':[['01','check'],['02','bet']],'04':[['01','check'],['02','bet'],['03','raise']],'05':[['01','donk']]},2:{'01':[],'02':[['01','check']],'03':[['01','bet']],'04':[['01','check'],['02','bet']]}};
const NEXT={0:{'01':{check:'02',donk:'05'},'02':{bet:'03'},'03':{raise:'04'}},2:{'01':{check:'02',bet:'03'},'02':{bet:'04'}}};
const NAMES={0:{'01':'BB: донк или чек','02':'BTN: c-bet','03':'BB против c-bet BTN','04':'BTN против чек-рейза','05':'BTN против донка'},1:{'01':'BB: донк против UTG','02':'UTG: c-bet против BB','03':'BB против c-bet UTG','04':'UTG против чек-рейза','05':'UTG против донка'},2:{'01':'UTG: c-bet против BTN','02':'BTN: ставка после чека','03':'BTN против c-bet UTG','04':'UTG против ставки BTN'}};
function ranks(board){return board.match(/[2-9TJQKA]/g).map(r=>'23456789TJQKA'.indexOf(r)+2).sort((a,b)=>b-a)}
function nine(board){const [a,b,c]=ranks(board);return c>=10?0:a===14&&b<=5?8:a===14?7:a-b>=4&&b-c>=4?1:a-c<=4?(a>=11?5:6):b>=10?2:a>=10?3:4}
function row(meta,legacy=false){return legacy&&meta[1]>=0?meta[1]:meta[0]<8?meta[0]:meta[1]>=0?meta[1]:meta[0]}
function spec(D,s,n,board,m){
 const g=nine(board),[top,mid]=ranks(board),legacy=s===2&&n==='01',r=row(m,legacy);let key,col;
 if(s<2){
  if(n==='02'||n==='03'){key=(n==='02'?'cb_':'df_')+(s===0?'btn':'utg');col=g}
  else if(n==='01'){key='donk';col=s===0?0:top>=10?1:top>=8?2:3}
  else if(n==='04'||n==='05'){key=n==='04'?'vsxr':'vsdonk';col=s}
  else return null;
 }else if(n==='01'){key='oopcb';col=top===13||top===14&&mid===13?0:top<=10?2:1}
 else if(n==='04'){key='stabdef';col=g===0?0:top===14?1:top>=10?2:3}
 else return null;
 const t=D.tables[key];let label=t.rows[r][col];
 if(label.includes(';'))label=g===0?'F':label.split(';')[0].trim();
 return {key,col,row:r,label,legacy};
}
function policy(D,s,n,board,m,cid){
 const sp=spec(D,s,n,board,m);if(!sp||sp.label==='—')return null;
 const a=sp.label,bet=n==='01'||n==='02'&&s<2,bd=!!m[2],dr=m[1]>=0;let o;
 if(a==='БД')o=bet?(bd?{bet:1}:{check:.5,bet:.5}):(bd?{call:1}:{fold:1});
 else if(a==='ДРО')o=dr?{call:1}:{fold:1};
 else if(a==='BDFD')o=bd?{call:1}:{fold:1};
 else if(a==='PAIR'||a==='PAIR/BDFD')o=m[0]<8||(a==='PAIR/BDFD'&&bd)?{call:1}:{fold:1};
 else if(a==='Ax')o=D.combos[cid].some(c=>D.deck[c][0]==='A')?{call:1}:{fold:1};
 else o=({'B':{bet:1},'X':{check:1},'B/X':{check:.5,bet:.5},'X/B':{check:.5,bet:.5},'B15/X85':{check:.85,bet:.15},'F':{fold:1},'C':{call:1},'R':{raise:1},'R/C':{call:.5,raise:.5},'C/R':{call:.5,raise:.5}})[a];
 if(!o)throw Error('Unknown policy '+a);
 if(s<2&&n==='01'&&o.bet){o={...o,donk:o.bet};delete o.bet}
 return o;
}
function branch(D,s,n){return D.studies[s].branches.find(b=>b.id.startsWith(n))}
function prefix(s,n){return PREFIX[s===2?2:0][n]}
function next(s,n,a){return (NEXT[s===2?2:0][n]||{})[a]||null}
function legal(D,board,cid){const cs=board.replaceAll(' ','');return D.combos[cid].every(c=>!cs.includes(D.deck[c]))}
function compatible(D,a,b){return D.combos[a].every(c=>!D.combos[b].includes(c))}
function decodeBlock(block){for(const st of block.studies){for(const n of Object.keys(st))st[n]=new Map(st[n].map(a=>[a[0],a.slice(1)]))}return block}
function solver(D,block,s,n,cid){const p=block.studies[s][n]?.get(cid);if(!p||p.reduce((a,b)=>a+b,0)<=0)return null;return Object.fromEntries(branch(D,s,n).actions.map((a,i)=>[a,p[i]]))}
function reached(D,block,s,board,history,actor,hero,opponentOnly=false){
 return D.studies[s].weights[actor].map((w,cid)=>{
  if(!w||!legal(D,board,cid)||!block.meta[cid])return 0;
  for(const [n,a,deviation] of history){
   if(branch(D,s,n).actor!==actor)continue;
   // The approved deviation is an explicitly forced donk, not a solver frequency.
   if(deviation&&n==='01'&&a==='donk')continue;
   const p=actor===hero&&!opponentOnly?policy(D,s,n,board,block.meta[cid],cid):solver(D,block,s,n,cid);
   w*=p?.[a]||0;if(!w)return 0;
  }
  return w;
 });
}
function weighted(items,weights,rng=Math.random){let total=weights.reduce((a,b)=>a+b,0);if(!(total>0))return null;let k=rng()*total;for(let i=0;i<items.length;i++){k-=weights[i];if(k<0)return items[i]}return items.at(-1)}
function sample(p,rng=Math.random){const entries=Object.entries(p||{});return weighted(entries.map(x=>x[0]),entries.map(x=>x[1]),rng)}
function cellKey(s,n,g,r){return[s,n,g,r].join(':')}
function chooseCell(cells,counts,rng=Math.random){if(!cells.length)return null;let min=Infinity,list=[];for(const c of cells){const n=counts[c.key]||0;if(n<min){min=n;list=[c]}else if(n===min)list.push(c)}return list[Math.floor(rng()*list.length)]}
function explanations(D,g){return Object.entries(D.explanations).filter(([,item])=>item.flops.includes(g));}
const api={NAMES,ranks,nine,row,spec,policy,branch,prefix,next,legal,compatible,decodeBlock,solver,reached,weighted,sample,cellKey,chooseCell,explanations};
if(typeof module!=='undefined')module.exports=api;else root.TrainerCore=api;
})(typeof window==='undefined'?{}:window);
