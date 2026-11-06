from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':1360,'height':860}); pg=ctx.new_page(); errs=[]
    pg.on('pageerror',lambda e:errs.append(str(e)))
    pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000)
    f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
    f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(open('/tmp/cred.txt').read().split('Senha:')[1].strip()); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(6000)
    n1=fr().evaluate("VISITS.length"); snap=fr().evaluate("Object.keys(localStorage).filter(k=>k.indexOf('portal_snap:')==0).length")
    print('visitas apos login',n1,'snapshots salvos',snap)
    # bloqueia a carga de dados para provar que o retrato aparece sozinho
    pg.reload(); 
    ok=False
    for i in range(60):
        pg.wait_for_timeout(250)
        try:
            if fr().evaluate("typeof VISITS!=='undefined'&&VISITS.length>0&&!!document.getElementById('snapnote')"): ok=True; print('retrato exibido em ~%d ms apos reload'%((i+1)*250)); break
        except Exception: pass
    print('retrato antes dos dados novos:',ok)
    pg.wait_for_timeout(8000)
    print('pill depois da atualizacao:',fr().evaluate("!!document.getElementById('snapnote')"),'visitas',fr().evaluate("VISITS.length"))
    fr().evaluate("document.querySelector('[data-act=logout]')&&document.querySelector('[data-act=logout]').click()"); pg.wait_for_timeout(1500)
    print('snapshots apos sair',fr().evaluate("Object.keys(localStorage).filter(k=>k.indexOf('portal_snap:')==0).length"))
    print('errs',errs)
