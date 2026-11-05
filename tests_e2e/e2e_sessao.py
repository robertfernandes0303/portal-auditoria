"""Atualizar a página mantém o login; Sair apaga; token adulterado cai no login."""
from playwright.sync_api import sync_playwright
cred=open('/tmp/cred.txt').read().split('Senha:')[1].strip()
ok_=True
def ok(n,c):
    global ok_; ok_&=bool(c); print('PASS' if c else 'FAIL',n)
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp in (('desk',{'width':1360,'height':860}),('phone',{'width':390,'height':800})):
        ctx=b.new_context(viewport=vp); pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        fr=lambda: pg.frames[-1]; f=pg.frame_locator('iframe')
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000)
        ok(tag+' começa na tela de login',f.locator('#lg-user').count()==1)
        f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(cred); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(3500)
        ok(tag+' logou',fr().evaluate("!!S.me"))
        ok(tag+' token guardado',fr().evaluate("!!localStorage.getItem('portal_tok')"))
        fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(500)
        pg.reload(); pg.wait_for_timeout(6500)
        ok(tag+' F5 mantém logado (sem tela de login)',fr().evaluate("!!S.me")  and f.locator('#lg-user').count()==0)
        pg.reload(); pg.wait_for_timeout(6500); ok(tag+' segundo F5 também mantém',fr().evaluate("!!S.me"))
        fr().evaluate("location.hash='#conta'"); pg.wait_for_timeout(700); fr().evaluate("document.querySelector('[data-act=logout]').click()"); pg.wait_for_timeout(2500)
        ok(tag+' sair mostra login e apaga token',f.locator('#lg-user').count()==1 and fr().evaluate("!localStorage.getItem('portal_tok')"))
        pg.reload(); pg.wait_for_timeout(6000); ok(tag+' após sair, F5 continua no login',f.locator('#lg-user').count()==1)
        # token adulterado
        fr().evaluate("localStorage.setItem('portal_tok','abc.def')"); pg.reload(); pg.wait_for_timeout(7000)
        ok(tag+' token inválido cai no login e é apagado',f.locator('#lg-user').count()==1 and fr().evaluate("!localStorage.getItem('portal_tok')"))
        ok(tag+' sem erros JS',not errs); ctx.close()
    b.close()
print('RESULT','OK' if ok_ else 'FALHOU')
