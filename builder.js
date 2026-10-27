let config;let engineSource,runtimeSource;
const $=id=>document.getElementById(id),status=m=>$('status').textContent=m;
const colors={green:['#315e56','#f5f0e4'],rose:['#804650','#fbf0ed'],blue:['#34476b','#eef0f7']};
function fill(){ $('title').value=config.title;$('subtitle').value=config.subtitle;$('json').value=JSON.stringify(config,null,2);mountQuiz(config,$('quiz')) }
function read(){config.title=$('title').value;config.subtitle=$('subtitle').value;QuizEngine.validate(config);$('json').value=JSON.stringify(config,null,2)}
function download(name,text,type){const u=URL.createObjectURL(new Blob([text],{type})),a=document.createElement('a');a.href=u;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(u),1000)}
function guard(fn){return async()=>{try{await fn()}catch(e){status('未应用：'+e.message)}}}
$('theme').onchange=guard(()=>{[config.accent,config.background]=colors[$('theme').value];read();mountQuiz(config,$('quiz'))});
$('preview').onclick=guard(()=>{read();mountQuiz(config,$('quiz'));status('已更新。预览会重新开始。')});
$('apply').onclick=guard(()=>{let next=JSON.parse($('json').value);QuizEngine.validate(next);config=next;fill();status('题库结构校验通过；内容质量仍需人工试测。')});
$('file').onchange=guard(async()=>{let f=$('file').files[0];if(!f)return;if(f.size>500000)throw Error('文件不得超过 500 KB');let next=JSON.parse(await f.text());QuizEngine.validate(next);config=next;fill();status('导入成功')});
$('save').onclick=guard(()=>{read();download('quiz-config.json',JSON.stringify(config,null,2),'application/json')});
$('download').onclick=guard(()=>{read();if(!engineSource||!runtimeSource)throw Error('请通过本地服务器打开生成器');const data=JSON.stringify(config).replace(/</g,'\\u003c').replace(/\u2028/g,'\\u2028').replace(/\u2029/g,'\\u2029');const title=config.title.replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));let html='<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+title+'</title><body style="margin:0;background:'+config.background+'"><div id="quiz"></div><script>'+engineSource+'\n'+runtimeSource+'\nmountQuiz('+data+',document.getElementById("quiz"));<\/script></body></html>';download('quiz.html',html,'text/html');status('已导出 quiz.html。双击即可打开；付费上线另见交付指南。')});
Promise.all(['examples/city.json','engine.js','runtime.js'].map(async u=>{let r=await fetch(u);if(!r.ok)throw Error('读取失败 '+u);return r.text()})).then(([c,e,r])=>{config=QuizEngine.validate(JSON.parse(c));engineSource=e;runtimeSource=r;fill();status('内置 12 题 / 8 种城市意象已就绪')}).catch(e=>status('启动失败：'+e.message+'。请按 README 用本地 HTTP 服务打开，不能直接双击生成器。'));
