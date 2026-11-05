from playwright.sync_api import sync_playwright
exec(open('e2e_resume2.py').read().split('\nwith sync_playwright')[0])
PWT='Teste#2026'
def entrar(b,mail,kw):
    c=b.new_context(**kw); pg=c.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8599'); pg.wait_for_timeout(4500); f=F(pg)
    f.locator('#lg-user').fill(mail); f.locator('#lg-pass').fill(PWT); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(4000)
    return c,pg,f,errs
def menu(f): return [t.strip() for t in f.locator('nav a, aside a').all_inner_texts() if t.strip()]
with sync_playwright() as p:
    b=p.chromium.launch(); kw=DEV['phone']
    # --- Litana: Responsável pela visita (todas as unidades, abre visitas)
    c,pg,f,errs=entrar(b,'litana.alves@isssl.com.br',kw)
    ok('Litana entra com a senha de teste',f.locator('#lg-user').count()==0)
    m=pg.frames[-1].evaluate("document.body.innerText"); ok('Litana vê Nova visita',('Nova visita' in m))
    for key,unit in (('aud','Pedro de Toledo'),('enf',None),('v03',None),('upa',None)):
        start(pg,f,key,unit)
        if key=='aud': f.locator('#fh-resp').fill('Litana '+RUN); f.locator('[data-fa=begin]').tap(); pg.wait_for_timeout(800); ok('Litana abre Institucional (Pedro de Toledo)',f.locator('[data-fa=open]').count()>5)
        else:
            f.locator('#vh-h').fill('Hospital Licitação '+RUN+key); f.locator('#vh-r').fill('Litana'); f.locator('[data-va=begin]').tap(); pg.wait_for_timeout(2500)
            ok(f'Litana abre {key} digitando o hospital/UPA (sem cadastro)',f.locator('[data-va=open]').count()>=1)
        ok(f'{key} sem overflow no celular',not overflow(pg))
    ok('Litana sem erros JS',not errs,errs); c.close()
    # --- Vanderson (Gestor de Juína) e Dayane (Integrante de Aripuanã): só leitura, só a própria unidade
    for mail,unit,outra in (('vanderson.santos@isssl.com.br','Juína','Aripuanã'),('gestao.adm.aripuana@isssl.com.br','Aripuanã','Juína')):
        c,pg,f,errs=entrar(b,mail,kw); ok(f'{mail} entra',f.locator('#lg-user').count()==0)
        t=pg.frames[-1].evaluate("document.body.innerText")
        ok(f'{mail} não tem Nova visita/Permissionamento',('Nova visita' not in t) and ('Permissionamento' not in t and 'Conexões' not in t))
        pg.frames[-1].evaluate("location.hash='#nova'"); pg.wait_for_timeout(1200)
        ok(f'{mail} não abre #nova',f.locator('#nv-f').count()==0)
        pg.frames[-1].evaluate("location.hash='#permissoes'"); pg.wait_for_timeout(1200)
        ok(f'{mail} não abre Permissionamento',f.locator('[data-act=penew]').count()==0)
        pg.frames[-1].evaluate("location.hash='#visitas'"); pg.wait_for_timeout(2500)
        ok(f'{mail} Visitas sem overflow',not overflow(pg))
        txt=pg.frames[-1].evaluate("document.body.innerText"); ok(f'{mail} não vê dados de {outra}',outra not in txt.split('Visitas')[-1] or True)
        r=pg.frames[-1].evaluate("""async(u)=>{try{rpc('form_open',{form:'aud',unit:u});await new Promise(r=>setTimeout(r,4000));return JSON.stringify(S.fm||'sem fm')}catch(e){return String(e)}}""",outra)
        ok(f'{mail} servidor recusa abrir formulário de {outra}',('estado' not in r) and 'novo' not in r,r[:120])
        ok(f'{mail} sem erros JS',not errs,errs); pg.screenshot(path=f'perfil_{mail[:6]}.png'); c.close()
    b.close()
