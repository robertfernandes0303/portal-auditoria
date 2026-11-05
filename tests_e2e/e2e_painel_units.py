"""Painel: filtro de unidades com caixas de marcação (marcar/desmarcar/limpar) e tempo de carga."""
from playwright.sync_api import sync_playwright
import time
cred=open('/tmp/cred.txt').read().split('Senha:')[1].strip()
ok=True
def chk(n,c):
    global ok; ok&=bool(c); print('PASS' if c else 'FAIL',n)
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp in (('desk',{'width':1360,'height':860}),('phone',{'width':390,'height':800})):
        pg=b.new_page(viewport=vp); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000)
        f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
        f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(cred); f.locator('#lg-pass').press('Enter')
        t=time.time(); pg.wait_for_timeout(2500)
        fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(1500)
        if tag=='phone' and f.locator('details.fbar').count(): f.locator('details.fbar > summary').click(); pg.wait_for_timeout(300)
        fr().evaluate("""()=>{['Juína','Pontes e Lacerda','Aripuanã'].forEach(function(u,i){var v=JSON.parse(JSON.stringify(VISITS.filter(function(x){return x.mod==='aud'})[0]||VISITS[0]));v.id='T'+i;v.mod='aud';v.unit=u;VISITS.push(v)});render()}""")
        pg.wait_for_timeout(500)
        if f.locator('details.fbar').count() and f.locator('details.fbar').get_attribute('open') is None: f.locator('details.fbar > summary').click(); pg.wait_for_timeout(300)
        n=f.locator('#f-units').count()
        chk(tag+' seletor múltiplo existe',n==1)
        if n:
            f.locator('#f-units > summary').click(); pg.wait_for_timeout(300)
            cbs=f.locator('input[data-bind=f-unitc]'); tot=cbs.count(); print(tag,'unidades',tot)
            chk(tag+' sem marcação = todas',f.locator('#f-units > summary').inner_text().startswith('Todas'))
            cbs.nth(0).check(); pg.wait_for_timeout(500)
            chk(tag+' marcar 1 mantém lista aberta',f.locator('#f-units').get_attribute('open') is not None)
            u1=f.locator('#f-units > summary').inner_text()
            if tot>1:
                f.locator('input[data-bind=f-unitc]').nth(1).check(); pg.wait_for_timeout(500)
                chk(tag+' 2 unidades no resumo','2 unidades' in f.locator('#f-units > summary').inner_text())
                f.locator('input[data-bind=f-unitc]').nth(1).uncheck(); pg.wait_for_timeout(500)
                chk(tag+' desmarcar volta a 1',f.locator('#f-units > summary').inner_text()==u1)
            f.locator('[data-act=fu-all]').click(); pg.wait_for_timeout(500)
            chk(tag+' marcar todas',f.locator('input[data-bind=f-unitc]:checked').count()==tot)
            f.locator('[data-act=fu-none]').click(); pg.wait_for_timeout(500)
            chk(tag+' limpar = todas',f.locator('#f-units > summary').inner_text().startswith('Todas') and f.locator('input[data-bind=f-unitc]:checked').count()==0)
            ov=fr().evaluate("document.documentElement.scrollWidth>window.innerWidth+1")
            chk(tag+' sem overflow horizontal',not ov)
        chk(tag+' sem erros JS',not errs)
    b.close()
print('RESULT','OK' if ok else 'FALHOU')
