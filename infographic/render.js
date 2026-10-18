const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const G = path.resolve(__dirname, '..');
(async () => {
  fs.mkdirSync(path.join(__dirname,'preview'),{recursive:true});
  const b = await chromium.launch();
  const files = ['infographic/plugfest-infographic.svg','assets/hero.svg','assets/flow.svg','assets/stats.svg','assets/v2g-txprofile.svg','assets/scenarios.svg','assets/as5438.svg'];
  for (const f of files) {
    const svg = fs.readFileSync(path.join(G,f),'utf8');
    const m = svg.match(/viewBox="0 0 (\d+) (\d+)"/); const w=+m[1], h=+m[2];
    const fallback = process.argv[2]==='arial';
    const p = await b.newPage({viewport:{width:w,height:h}, deviceScaleFactor: 1});
    const src = fallback ? svg.replace(/font-family="[^"]*"/,'font-family="Arial, Liberation Sans"') : svg;
    // render as <img> like GitHub does
    await p.setContent(`<html><body style="margin:0;background:${process.argv[3]||'#fff'}"><img src="data:image/svg+xml;base64,${Buffer.from(src).toString('base64')}" width="${w}" height="${h}" style="display:block"></body></html>`);
    await p.waitForTimeout(200);
    const out = f.startsWith('infographic') && !fallback && !process.argv[3] ? path.join(G,'infographic/plugfest-infographic.png') : path.join(__dirname,'preview', path.basename(f,'.svg')+(fallback?'-arial':'')+(process.argv[3]?'-dark':'')+'.png');
    await p.screenshot({path: out});
    if (f.startsWith('infographic') && !fallback && !process.argv[3]) {
      await p.screenshot({path: path.join(__dirname,'preview','plugfest-infographic.png')});
      const pp = await b.newPage();
      await pp.setContent(`<html><head><style>@page{size:${w}px ${h}px;margin:0}html,body{margin:0}</style></head><body>${svg.replace(/^<\?xml[^>]*>/,'')}</body></html>`);
      // A3 portrait-ish: scale SVG to page: 297x420mm; use CSS to fit
      await pp.setContent(`<html><head><style>@page{size:297mm 420mm;margin:0}html,body{margin:0;width:297mm;height:420mm;overflow:hidden}svg{width:297mm;height:420mm;display:block}</style></head><body>${svg.replace(/^<\?xml[^>]*>/,'').replace(/ width="1600" height="2263"/,'')}</body></html>`);
      await pp.pdf({path: path.join(G,'infographic/plugfest-infographic.pdf'), width:'297mm', height:'420mm', printBackground:true, pageRanges:'1'});
    }
    await p.close();
  }
  await b.close();
})();
