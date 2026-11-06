"""Senha: temporária obriga troca; troca própria real; sessão antiga cai; recuperar acesso honesto."""
from playwright.sync_api import sync_playwright
ok_=True
def ok(n,c):
    global ok_; ok_&=bool(c); print('PASS' if c else 'FAIL',n)
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp in (('desk',{'width':1360,'height':860}),('phone',{'width':390,'height':800})):
        ctx=b.new_context(viewport=vp); pg=ctx.new_page(); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        fr=lambda: pg.frames[-1]; f=pg.frame_locator('iframe')
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000)
        # recuperar acesso honesto
        f.locator('[data-act=lgreset]').click(); pg.wait_for_timeout(500)
        t=fr().evaluate("document.body.innerText")
        ok(tag+' recuperar acesso não promete e-mail',('Enviar link' not in t) and ('enviamos um link' not in t) and ('senha temporária' in t))
        f.locator('[data-act=lgback]').click(); pg.wait_for_timeout(400)
        senha='Temporaria1'; mail='temp@teste.local' if tag=='desk' else 'temp2@teste.local'
        f.locator('#lg-user').fill(mail); f.locator('#lg-pass').fill(senha); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(4000)
        ok(tag+' entra e é levado a Minha conta',fr().evaluate("location.hash")=='#conta' and fr().evaluate("document.body.innerText.includes('Defina a sua senha para continuar')"))
        fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(700)
        ok(tag+' não consegue sair da Minha conta antes de trocar',fr().evaluate("location.hash")=='#conta')
        # erros
        def trocar(atual,nova,conf):
            fr().evaluate(f"document.getElementById('pw0').value='{atual}';document.getElementById('pw1').value='{nova}';document.getElementById('pw2').value='{conf}';document.getElementById('pwForm').requestSubmit()"); pg.wait_for_timeout(2500)
            return fr().evaluate("(document.getElementById('pwMsg')||{}).textContent+' | '+document.body.innerText")
        r=trocar('errada-999','NovaSenha123','NovaSenha123'); ok(tag+' senha atual errada recusada','não confere' in r)
        r=trocar(senha,'curta','curta'); ok(tag+' senha curta recusada','pelo menos 8' in r)
        r=trocar(senha,'NovaSenha123','Diferente999'); ok(tag+' confirmação diferente recusada','não conferem' in r)
        nova='NovaSenha123' if tag=='desk' else 'NovaSenha456'
        r=trocar(senha,nova,nova); ok(tag+' troca válida aceita','alterada com sucesso' in r.lower() or fr().evaluate("!S.mustChange"))
        pg.wait_for_timeout(4000)
        ok(tag+' portal liberado e dados carregam',fr().evaluate("!S.mustChange")and fr().evaluate("location.hash")=='#inicio' and fr().evaluate("VISITS.length>=0 && !!S.me"))
        fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(800); ok(tag+' navega livremente após trocar',fr().evaluate("location.hash")=='#painel')
        pg.reload(); pg.wait_for_timeout(7000); ok(tag+' F5 mantém login após a troca',fr().evaluate("!!S.me")==True)
        # sair e testar senha antiga x nova
        fr().evaluate("location.hash='#conta'"); pg.wait_for_timeout(600); fr().evaluate("document.querySelector('[data-act=logout]').click()"); pg.wait_for_timeout(2500)
        f.locator('#lg-user').fill(mail); f.locator('#lg-pass').fill(senha); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(2500)
        ok(tag+' senha temporária antiga não entra mais',fr().evaluate("!S.me"))
        f.locator('#lg-pass').fill(nova); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(4000)
        ok(tag+' senha nova entra direto, sem exigir troca',fr().evaluate("!!S.me && !S.mustChange"))
        ok(tag+' sem erros JS',not errs); ctx.close()
    b.close()
print('RESULT','OK' if ok_ else 'FALHOU')
