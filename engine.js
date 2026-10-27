(function(root){
'use strict';
function validate(c){
 const fail=m=>{throw Error(m)};const str=(v,n)=>{if(typeof v!=='string'||!v.trim()||v.length>3000)fail(n+'须为非空短文本')};
 if(!c||c.version!==1)fail('version 必须为 1'); str(c.title,'标题');str(c.subtitle,'副标题');
 for(const k of ['accent','background'])if(!/^#[0-9a-f]{6}$/i.test(c[k]))fail('颜色须为六位十六进制');
 if(!Array.isArray(c.dimensions)||c.dimensions.length<2||c.dimensions.length>8)fail('需 2–8 个维度');c.dimensions.forEach(v=>str(v,'维度'));if(new Set(c.dimensions).size!==c.dimensions.length)fail('维度不能重名');
 if(!Array.isArray(c.questions)||c.questions.length<4||c.questions.length>40)fail('需 4–40 道题');
 if(!Array.isArray(c.results)||c.results.length<2||c.results.length>24)fail('需 2–24 个结果');
 const ids=new Set();const id=v=>{str(v,'ID');if(ids.has(v))fail('ID 重复');ids.add(v)};
 const vec=(v,b)=>{if(!Array.isArray(v)||v.length!==c.dimensions.length||v.some(x=>typeof x!=='number'||!Number.isFinite(x)||Math.abs(x)>b))fail('分值向量非法')};
 c.questions.forEach(q=>{id(q.id);str(q.text,'题目');if(!Array.isArray(q.options)||q.options.length<2||q.options.length>6)fail('每题需 2–6 选项');q.options.forEach(o=>{str(o.text,'选项');vec(o.scores,2)})});
 c.results.forEach(r=>{id(r.id);['name','tag','summary','tension','action','context'].forEach(k=>str(r[k],k));vec(r.target,1)});
 c.dimensions.forEach((_,d)=>{if(c.questions.every(q=>new Set(q.options.map(o=>o.scores[d])).size===1))fail('维度没有区分度：'+c.dimensions[d])});return c;
}
function score(c,answers){validate(c);if(!Array.isArray(answers)||answers.length!==c.questions.length)throw Error('请完成全部题目');
 const totals=c.dimensions.map(()=>0), lo=totals.slice(),hi=totals.slice();
 c.questions.forEach((q,i)=>{const a=answers[i];if(!Number.isInteger(a)||a<0||a>=q.options.length)throw Error('答案非法');totals.forEach((_,d)=>{totals[d]+=q.options[a].scores[d];lo[d]+=Math.min(...q.options.map(o=>o.scores[d]));hi[d]+=Math.max(...q.options.map(o=>o.scores[d]))})});
 const vector=totals.map((x,d)=>hi[d]===lo[d]?0:2*(x-lo[d])/(hi[d]-lo[d])-1);
 const ranked=c.results.map((r,i)=>({result:r,index:i,distance:vector.reduce((s,x,d)=>s+(x-r.target[d])**2,0)})).sort((a,b)=>a.distance-b.distance||a.index-b.index);
 const evidence=c.questions.map((q,i)=>({question:q.text,answer:q.options[answers[i]].text,strength:q.options[answers[i]].scores.reduce((s,x)=>s+Math.abs(x),0)})).sort((a,b)=>b.strength-a.strength).slice(0,3);
 return {winner:ranked[0].result,runner:ranked[1].result,close:ranked[1].distance-ranked[0].distance<.15,vector,evidence};
}
root.QuizEngine={validate,score};if(typeof module!=='undefined')module.exports=root.QuizEngine;
})(typeof globalThis!=='undefined'?globalThis:this);
