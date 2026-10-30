from playwright.sync_api import sync_playwright
exec(open('e2e_resume2.py').read().split('\nwith sync_playwright')[0])
JS="""()=>{const out={small:[],font:[],over:document.documentElement.scrollWidth>document.documentElement.clientWidth+1};
document.querySelectorAll('button,a.btn,[role=radio],summary,select,input[type=checkbox],label.chk').forEach(e=>{const r=e.getBoundingClientRect();if(r.width&&r.height&&(r.height<40||r.width<40)&&getComputedStyle(e).visibility!=='hidden'&&e.offsetParent!==null){out.small.push((e.dataset.va||e.dataset.fa||e.dataset.act||e.tagName)+':'+Math.round(r.width)+'x'+Math.round(r.height)+':'+(e.innerText||'').slice(0,18))}});
document.querySelectorAll('input:not([type=checkbox]):not([type=radio]):not([type=file]),textarea,select').forEach(e=>{if(e.offsetParent!==null&&parseFloat(getComputedStyle(e).fontSize)<16)out.font.push((e.id||e.dataset.vi||e.dataset.fi||e.tagName)+':'+getComputedStyle(e).fontSize)});return out}"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for dev,kw in DEV.items():
        c=b.new_context(**kw); pg=c.new_page(); f=login(pg)
        telas=[]
        for h in ('inicio','painel','evolucao','visitas','plano','nova'):
            pg.frames[-1].evaluate(f"location.hash='#{h}'"); pg.wait_for_timeout(1200); telas.append((h,pg.frames[-1].evaluate(JS)))
        for key in ('enf','v03','upa'):
            vt_new(pg,f,key,f'{dev} touch {key} '+RUN); telas.append((key+' grupo',pg.frames[-1].evaluate(JS)))
            f.locator('[data-va=menu]').first.tap(); pg.wait_for_timeout(600); telas.append((key+' menu',pg.frames[-1].evaluate(JS)))
            f.locator('[data-va=leave]').tap(); pg.wait_for_timeout(800)
        start(pg,f,'aud','Juína'); telas.append(('aud início',pg.frames[-1].evaluate(JS)))
        for n,r in telas:
            print(dev,n,'OVERFLOW' if r['over'] else '', 'pequenos:',sorted(set(r['small']))[:6],'fonte<16:',sorted(set(r['font']))[:4])
        c.close()
    b.close()
