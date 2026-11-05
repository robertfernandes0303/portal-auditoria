"""Lista de unidades do filtro: fecha ao clicar fora, Esc, trocar de tela, Marcar todas/Limpar; abre ao tocar."""
from playwright.sync_api import sync_playwright
cred=open('/tmp/cred.txt').read().split('Senha:')[1].strip()
ok_=True
def ok(n,c):
    global ok_; ok_&=bool(c); print('PASS' if c else 'FAIL',n)
INJ="()=>{['Juína','Pontes e Lacerda','Aripuanã'].forEach(function(u,i){var v=JSON.parse(JSON.stringify(VISITS.filter(function(x){return x.mod==='aud'})[0]||VISITS[0]));v.id='T'+i;v.mod='aud';v.unit=u;VISITS.push(v)});render()}"
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp,mob in (('desk',{'width':1360,'height':860},False),('phone',{'width':390,'height':800},True)):
        pg=b.new_page(viewport=vp,has_touch=mob); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000); f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
        f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(cred); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(2500)
        fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(1200); fr().evaluate(INJ); pg.wait_for_timeout(500)
        def abrir():
            if f.locator('details.fbar').count() and f.locator('details.fbar').get_attribute('open') is None: f.locator('details.fbar > summary').click(); pg.wait_for_timeout(300)
            if f.locator('#f-units').get_attribute('open') is None: f.locator('#f-units > summary').click(); pg.wait_for_timeout(300)
        isopen=lambda: fr().evaluate("document.getElementById('f-units')&&document.getElementById('f-units').open")
        abrir(); ok(tag+' abre ao tocar',isopen())
        f.locator('input[data-bind=f-unitc]').first.check(); pg.wait_for_timeout(500); ok(tag+' marcar 1 mantém aberta',isopen())
        fr().evaluate("document.querySelector('h1').dispatchEvent(new PointerEvent('pointerdown',{bubbles:true}))"); pg.wait_for_timeout(300); ok(tag+' toque fora fecha',not isopen())
        abrir(); fr().evaluate("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))"); pg.wait_for_timeout(300); ok(tag+' Esc fecha',not isopen())
        abrir(); fr().evaluate("location.hash='#visitas'"); pg.wait_for_timeout(600); fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(600)
        ok(tag+' trocar de tela fecha e não reaparece aberta',not isopen())
        abrir(); f.locator('[data-act=fu-all]').click(); pg.wait_for_timeout(500); ok(tag+' Marcar todas fecha',not isopen())
        abrir(); f.locator('[data-act=fu-none]').click(); pg.wait_for_timeout(500); ok(tag+' Limpar fecha',not isopen())
        ok(tag+' sem erros JS',not errs)
    b.close()
print('RESULT','OK' if ok_ else 'FALHOU')
