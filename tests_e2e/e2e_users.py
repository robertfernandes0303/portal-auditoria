import os,sqlite3
from playwright.sync_api import sync_playwright
exec(open('e2e_plan.py').read().split('\nwith sync_playwright')[0])
NM='Nova Pessoa '+RUN; ML=f'nova{RUN}@isssl.com.br'; PWD='Senha#Manual1'
with sync_playwright() as p:
    b=p.chromium.launch(); kw=DEV['phone']; errs=[]
    c=b.new_context(**kw); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); f=login(pg)
    pg.frames[-1].evaluate("location.hash='#permissoes'"); pg.wait_for_timeout(2000)
    f.locator('[data-act=penew]').tap(); pg.wait_for_timeout(500)
    f.locator('#nu-name').fill(NM); f.locator('#nu-mail').fill(ML); f.locator('#nu-role').select_option('gestor')
    f.locator('[data-act=pscope][data-v=sel]').tap(); pg.wait_for_timeout(300)
    f.locator('#nu-pass').fill('curta'); f.locator('#peForm button[type=submit]').tap(); pg.wait_for_timeout(600)
    ok('senha curta é recusada',f.locator('#peMsg').inner_text().startswith('A senha'),f.locator('#peMsg').inner_text())
    f.locator('#nu-pass').fill(PWD); pg.screenshot(path='us_novo_phone.png'); ok('form novo usuário sem overflow',not overflow(pg))
    # escolher unidade Aripuanã
    f.locator('.uchk,[data-act=pu]').first.count()
    ex=f.locator('label.chk,[data-act=punit]'); 
    pg.frames[-1].evaluate("""()=>{const l=[...document.querySelectorAll('label,button')].find(e=>/^Aripuanã$/.test(e.innerText.trim())||e.innerText.trim().startsWith('Aripuanã'));if(l)l.click()}""")
    pg.wait_for_timeout(300); f.locator('#nu-pass').fill(PWD)
    f.locator('#peForm button[type=submit]').tap(); pg.wait_for_timeout(3000)
    ok('usuário criado com senha',ML in open('/dev/null').read() or f.locator('.urow',has_text=NM).count()==1)
    db=sqlite3.connect('/tmp/seed/portal.db'); n=db.execute("select count(*) from users where mail=?",(ML,)).fetchone()[0]; cr=db.execute("select count(*) from credentials where mail=?",(ML,)).fetchone()[0]
    ok('gravado no SQLite (users + credentials)',n==1 and cr==1,(n,cr)); h=db.execute("select hash from credentials where mail=?",(ML,)).fetchone()[0]; ok('senha guardada só como hash',PWD not in h and h.startswith('scrypt$'))
    c.close()
    c=b.new_context(**kw); pg=c.new_page(); f=login_as(pg,ML,'errada'); ok('senha errada não entra',f.locator('#lg-user').count()==1)
    f.locator('#lg-user').fill(ML); f.locator('#lg-pass').fill(PWD); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(3500)
    ok('novo usuário entra com a senha definida',f.locator('#lg-user').count()==0)
    pg.frames[-1].evaluate("location.hash='#permissoes'"); pg.wait_for_timeout(1500); ok('gestor não acessa Permissionamento',f.locator('[data-act=penew]').count()==0)
    pg.frames[-1].evaluate("location.hash='#plano'"); pg.wait_for_timeout(2000); ok('gestor de Aripuanã não vê o plano de Juína',f.locator('.act').count()==0 and f.locator('[data-act=pedit]').count()==0)
    c.close()
    # admin altera a senha, a antiga deixa de valer
    c=b.new_context(**kw); pg=c.new_page(); f=login(pg); pg.frames[-1].evaluate("location.hash='#permissoes'"); pg.wait_for_timeout(2000)
    f.locator('.urow',has_text=NM).tap(); pg.wait_for_timeout(600); f.locator('#pw-new').fill('Outra#Senha22'); f.locator('[data-act=pwset]').tap(); pg.wait_for_timeout(2500)
    pg.screenshot(path='us_senha_phone.png'); ok('admin vê a confirmação da senha definida','Senha definida' in f.locator('.upanel').inner_text())
    c.close()
    c=b.new_context(**kw); pg=c.new_page(); f=login_as(pg,ML,PWD); ok('senha antiga deixou de valer',f.locator('#lg-user').count()==1); c.close()
    c=b.new_context(**kw); pg=c.new_page(); f=login_as(pg,ML,'Outra#Senha22'); ok('senha nova vale',f.locator('#lg-user').count()==0); c.close()
    ok('sem erro de JS',not errs,errs[:3]); b.close()
print('RESUMO',sum(1 for _,x in res if x),'/',len(res)); [print('  FALHOU:',n) for n,x in res if not x]
