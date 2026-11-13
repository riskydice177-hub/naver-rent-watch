"""거래 목록을 브라우저에서 바로 열 수 있는 HTML 리포트로 만든다."""
import html
import json

TEMPLATE = r"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>전월세 리포트 __DATE__</title>
<style>
:root{--bg:#f7f7f5;--card:#fff;--fg:#1d1d1b;--mute:#6b6b66;--line:#e4e4df;--acc:#2f6f4f;--new:#c2410c;--newbg:#fff1e6}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--card:#20201e;--fg:#ececea;--mute:#9a9a94;--line:#33332f;--acc:#7cc4a0;--new:#fb923c;--newbg:#3a2516}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 system-ui,-apple-system,"Malgun Gothic",sans-serif}
.wrap{max-width:1200px;margin:0 auto;padding:24px 16px 64px}
h1{font-size:22px;margin:0 0 4px}.sub{color:var(--mute);margin:0 0 20px}
.cards{display:flex;flex-wrap:wrap;gap:12px;margin-bottom:20px}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px 16px;min-width:150px;flex:1}
.card b{display:block;font-size:22px}.card span{color:var(--mute);font-size:12px}
.bar{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:0 0 12px}
select,input{font:inherit;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--card);color:var(--fg)}
label{display:flex;gap:4px;align-items:center;color:var(--mute)}
h2{font-size:16px;margin:28px 0 8px}
.tw{overflow-x:auto;background:var(--card);border:1px solid var(--line);border-radius:10px}
table{border-collapse:collapse;width:100%;white-space:nowrap}
th,td{padding:7px 10px;border-bottom:1px solid var(--line);text-align:left}
th{position:sticky;top:0;background:var(--card);color:var(--mute);font-weight:600;font-size:12px;cursor:pointer}
td.n{text-align:right;font-variant-numeric:tabular-nums}
tr.new td{background:var(--newbg)}
.badge{color:var(--new);font-weight:700;font-size:11px;margin-right:4px}
.muted{color:var(--mute)}
</style></head><body><div class="wrap">
<h1>서울 아파트 전월세 실거래</h1>
<p class="sub">__DATE__ 기준 · 국토교통부 실거래가 · 최근 __MONTHS__개월 · 금액 단위 만원</p>
<div class="cards" id="cards"></div>
<div class="bar">
 <select id="gu"><option value="">전체 구</option></select>
 <select id="dong"><option value="">전체 동</option></select>
 <select id="trade"><option value="">전세+월세</option><option>전세</option><option>월세</option></select>
 <input id="q" placeholder="단지명 검색" size="12">
 <label><input type="checkbox" id="onlyNew"> 새로 등록된 거래만</label>
</div>
<h2>동별 시세 요약 <span class="muted" style="font-size:12px;font-weight:400">(전용면적 구간별 보증금 중앙값)</span></h2>
<div class="tw"><table id="sum"></table></div>
<h2>거래 목록 <span class="muted" id="cnt" style="font-size:12px;font-weight:400"></span></h2>
<div class="tw"><table id="list"></table></div>
</div>
<script>
const D=__DATA__;
const $=id=>document.getElementById(id);
const fmt=n=>n==null||n===''?'':Number(n).toLocaleString('ko-KR');
const pyeong=a=>a?Math.round(a/3.3058):'';
const band=a=>a<40?'~40㎡':a<60?'40~60㎡':a<85?'60~85㎡':a<102?'85~102㎡':'102㎡~';
const median=xs=>{if(!xs.length)return null;const s=[...xs].sort((a,b)=>a-b),m=s.length>>1;return s.length%2?s[m]:Math.round((s[m-1]+s[m])/2)};
const gus=[...new Set(D.map(d=>d.gu))].sort();
gus.forEach(g=>$('gu').add(new Option(g,g)));
function fillDong(){const g=$('gu').value;$('dong').length=1;[...new Set(D.filter(d=>!g||d.gu===g).map(d=>d.dong))].sort().forEach(x=>$('dong').add(new Option(x,x)))}
let sortKey='date',sortDir=-1;
const cols=[['','new'],['계약일','date'],['구','gu'],['동','dong'],['단지','apt'],['전용㎡','area',1],['평','py',1],['층','floor',1],['구분','trade'],['보증금','deposit',1],['월세','monthly_rent',1],['신규/갱신','contract_type'],['종전보증금','pre_deposit',1],['건축','build_year',1]];
function rows(){const g=$('gu').value,dn=$('dong').value,t=$('trade').value,q=$('q').value.trim(),on=$('onlyNew').checked;
 return D.filter(d=>(!g||d.gu===g)&&(!dn||d.dong===dn)&&(!t||d.trade===t)&&(!q||d.apt.includes(q))&&(!on||d.is_new))}
function render(){const R=rows();
 const nNew=R.filter(d=>d.is_new).length,j=R.filter(d=>d.trade==='전세').map(d=>d.deposit);
 $('cards').innerHTML=[[R.length,'거래 건수'],[nNew,'새로 등록된 거래'],[fmt(median(j)),'전세 보증금 중앙값'],[R.filter(d=>d.trade==='월세').length,'월세 건수']].map(([v,l])=>`<div class="card"><b>${v??'-'}</b><span>${l}</span></div>`).join('');
 const S={};R.filter(d=>d.trade==='전세').forEach(d=>{const k=d.gu+' '+d.dong;(S[k]??={})[band(d.area)]??=[];S[k][band(d.area)].push(d.deposit)});
 const bands=['~40㎡','40~60㎡','60~85㎡','85~102㎡','102㎡~'];
 $('sum').innerHTML='<tr><th>지역</th>'+bands.map(b=>`<th>${b}</th>`).join('')+'</tr>'+Object.keys(S).sort().map(k=>'<tr><td>'+k+'</td>'+bands.map(b=>{const v=S[k][b]||[];return `<td class="n">${v.length?fmt(median(v))+' <span class="muted">('+v.length+')</span>':''}</td>`}).join('')+'</tr>').join('');
 R.forEach(d=>d.py=pyeong(d.area));
 R.sort((a,b)=>{const x=a[sortKey],y=b[sortKey];return (x>y?1:x<y?-1:0)*sortDir});
 $('cnt').textContent=`${R.length}건`+(R.length>2000?' (상위 2000건 표시)':'');
 $('list').innerHTML='<tr>'+cols.map(([h,k])=>`<th data-k="${k}">${h}${sortKey===k?(sortDir>0?' ▲':' ▼'):''}</th>`).join('')+'</tr>'+
  R.slice(0,2000).map(d=>`<tr class="${d.is_new?'new':''}">`+cols.map(([h,k,n])=>k==='new'?`<td>${d.is_new?'<span class="badge">NEW</span>':''}</td>`:`<td class="${n?'n':''}">${n?fmt(d[k]):(d[k]??'')}</td>`).join('')+'</tr>').join('');
 document.querySelectorAll('#list th').forEach(th=>th.onclick=()=>{const k=th.dataset.k;sortDir=sortKey===k?-sortDir:-1;sortKey=k;render()})}
$('gu').onchange=()=>{fillDong();render()};['dong','trade','onlyNew'].forEach(i=>$(i).onchange=render);$('q').oninput=render;
fillDong();render();
</script></body></html>"""


def build(deals, date_str, months):
    data = json.dumps(deals, ensure_ascii=False).replace("</", "<\\/")
    return (TEMPLATE.replace("__DATA__", data)
            .replace("__DATE__", html.escape(date_str))
            .replace("__MONTHS__", str(months)))
