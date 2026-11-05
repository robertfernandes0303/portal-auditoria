"""Hospital e UPA (unidades em licitação) são visitas de escopo: aparecem em Visitas, mas ficam fora de Painel, ranking, evolução e plano."""
from playwright.sync_api import sync_playwright
cred=open('/tmp/cred.txt').read().split('Senha:')[1].strip()
ok_=True
def ok(n,c,x=''):
    global ok_; ok_&=bool(c); print('PASS' if c else 'FAIL',n,'' if c else x)
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp in (('desk',{'width':1360,'height':860}),('phone',{'width':390,'height':800})):
        pg=b.new_page(viewport=vp); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000); f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
        f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(cred); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(4500)
        fr().evaluate("loadData(true)"); pg.wait_for_timeout(3000)
        mods=fr().evaluate("JSON.stringify(VISITS.reduce((a,v)=>{a[v.mod]=(a[v.mod]||0)+1;return a},{}))"); print(tag,'visitas',mods)
        sc=fr().evaluate("JSON.stringify(scopedVisits().map(v=>v.mod))")
        ok(tag+' v03/upa fora do cálculo',('v03' not in sc) and ('upa' not in sc),sc)
        ok(tag+' enf continua medida','enf' in sc or 'enf' not in mods,sc)
        fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(900)
        txt=f.locator('body').inner_text()
        ok(tag+' painel sem Hospital/UPA nos módulos',fr().evaluate("modsWithData().every(m=>m!=='v03'&&m!=='upa')"))
        fr().evaluate("location.hash='#visitas'"); pg.wait_for_timeout(900)
        ok(tag+' Visitas lista visita de escopo',f.locator('text=Visita de escopo').count()>=1)
        ok(tag+' ongoing separado chegou',fr().evaluate("typeof loadOngoing==='function'"))
        fr().evaluate("location.hash='#plano'"); pg.wait_for_timeout(700)
        ok(tag+' plano sem hospital/UPA',fr().evaluate("plansFor(scopedVisits()).every(x=>x.mod!=='v03'&&x.mod!=='upa')"))
        vid=fr().evaluate("(VISITS.filter(v=>MODS[v.mod].nm)[0]||{}).id")
        if vid:
            fr().evaluate(f"location.hash='#visita-{vid}'"); pg.wait_for_timeout(900)
            ok(tag+' detalhe de escopo abre',f.locator('text=Não entra em cálculos').count()==1)
        ok(tag+' sem erros JS',not errs,errs)
    b.close()
print('RESULT','OK' if ok_ else 'FALHOU')
