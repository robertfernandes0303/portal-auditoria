"""Ajustes de 10/11: unidade com cidade/UF automáticos e visitas em aberto só para o Responsável pela visita."""
from playwright.sync_api import sync_playwright
exec(open('e2e_resume2.py').read().split('\nwith sync_playwright')[0])
PWT='MinhaSenha#2026'
def entrar(b,mail,kw):
    c=b.new_context(**kw); pg=c.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8599'); pg.wait_for_timeout(4500); f=F(pg)
    f.locator('#lg-user').fill(mail); f.locator('#lg-pass').fill(PWT); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(4500)
    return c,pg,f,errs
with sync_playwright() as p:
    b=p.chromium.launch(); kw=DEV['phone']
    c,pg,f,errs=entrar(b,'beatriz.auditora@isssl.com.br',kw)
    ok('Beatriz (responsável) entra',f.locator('#lg-user').count()==0)
    for key in ('enf','v03','upa'):
        start(pg,f,key)
        lab=f.locator('label[for=vh-h]').inner_text().strip().lower()
        esperado={'enf':'unidade *','v03':'nome do hospital *','upa':'nome da unidade (upa / pam) *'}[key]
        ok(f'{key}: rótulo "{esperado}"',lab==esperado,lab)
        f.locator('#vh-h').fill('Pedro de Toledo'); pg.wait_for_timeout(300)
        ok(f'{key}: Pedro de Toledo -> cidade e UF automáticas',f.locator('#vh-c').input_value()=='Pedro de Toledo' and f.locator('#vh-uf').input_value()=='SP')
        ok(f'{key}: cidade somente leitura e UF travada',f.locator('#vh-c').get_attribute('readonly') is not None and f.locator('#vh-uf').is_disabled())
        f.locator('#vh-h').fill('Sumaré - Matão'); pg.wait_for_timeout(300)
        ok(f'{key}: Sumaré - Matão -> Sumaré/SP',f.locator('#vh-c').input_value()=='Sumaré' and f.locator('#vh-uf').input_value()=='SP')
        f.locator('#vh-h').fill('Hospital Novo Teste'); pg.wait_for_timeout(300)
        ok(f'{key}: nome fora do cadastro libera cidade/UF',f.locator('#vh-c').input_value()=='' and f.locator('#vh-c').get_attribute('readonly') is None and not f.locator('#vh-uf').is_disabled())
        ok(f'{key}: sem overflow no celular',not overflow(pg))
    # cria uma visita em aberto em Juína (enfermagem)
    start(pg,f,'enf'); f.locator('#vh-h').fill('Juína'); f.locator('#vh-r').fill('Beatriz '+RUN); f.locator('[data-va=begin]').tap(); pg.wait_for_timeout(2500)
    if f.locator('[data-va=startnew]').count(): f.locator('[data-va=startnew]').tap(); pg.wait_for_timeout(2000)
    ok('Beatriz abriu a visita de Juína',f.locator('[data-va=open]').count()>=1)
    f.locator('[data-va=open][data-i="0"]').tap(); pg.wait_for_timeout(500); vt_fill(f,'enf'); pg.wait_for_timeout(2500)
    pg.frames[-1].evaluate("location.hash='#inicio'"); pg.wait_for_timeout(1500); pg.frames[-1].evaluate("loadOngoing(true)"); pg.wait_for_timeout(4000)
    ok('Beatriz vê Continuar na visita em andamento',f.locator('[data-act=ongo]').count()>=1)
    ok('Beatriz sem erros JS',not errs,errs); c.close()
    for mail in ('carlos.gestor@isssl.com.br','diego.integrante@isssl.com.br'):
        c,pg,f,errs=entrar(b,mail,kw); ok(f'{mail} entra',f.locator('#lg-user').count()==0)
        pg.frames[-1].evaluate("location.hash='#inicio'"); pg.wait_for_timeout(1500); pg.frames[-1].evaluate("loadOngoing(true)"); pg.wait_for_timeout(4000)
        t=pg.frames[-1].evaluate("document.body.innerText")
        ok(f'{mail}: vê visitas em andamento',('Visitas em andamento' in t),t[:200])
        ok(f'{mail}: sem botão Continuar',f.locator('[data-act=ongo]').count()==0)
        ok(f'{mail}: "Somente consulta" no lugar',('Somente consulta' in t))
        r=pg.frames[-1].evaluate("""async()=>{rpc('form_open',{form:'enf'});await new Promise(r=>setTimeout(r,3500));return JSON.stringify(S.fm||'sem fm')}""")
        ok(f'{mail}: servidor recusa form_open','estado' not in r,r[:120])
        ok(f'{mail}: sem erros JS',not errs,errs); pg.screenshot(path=f'ajustes_{mail[:6]}.png'); c.close()
    b.close()
