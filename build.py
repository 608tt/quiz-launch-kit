"""Build an offline generator. No third-party dependencies."""
from pathlib import Path
import json
p=Path(__file__).parent
html=(p/'index.html').read_text()
for name,id_ in [('engine.js','engine-code'),('runtime.js','runtime-code')]:
 html=html.replace('<script src="'+name+'"></script>','<script id="'+id_+'">'+(p/name).read_text()+'</script>')
js=(p/'builder.js').read_text()
start="Promise.all(['examples/city.json','engine.js','runtime.js'].map(async u=>{let r=await fetch(u);if(!r.ok)throw Error('读取失败 '+u);return r.text()}))"
data=json.dumps((p/'examples/city.json').read_text(),ensure_ascii=False).replace('<','\\u003c')
js=js.replace(start,"Promise.resolve(["+data+",document.getElementById('engine-code').textContent,document.getElementById('runtime-code').textContent])")
html=html.replace('<script src="builder.js"></script>','<script>'+js+'</script>')
(p/'studio.html').write_text(html)
print('Built studio.html: double-click to open')
