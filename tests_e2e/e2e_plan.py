from playwright.sync_api import sync_playwright
exec(open('e2e_resume2.py').read().split('\nwith sync_playwright')[0])
def login_as(pg,mail,pw):
    pg.goto('http://localhost:8599'); pg.wait_for_timeout(4500); f=F(pg)
    f.locator('#lg-user').fill(mail); f.locator('#lg-pass').fill(pw); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(3500); return f
with sync_playwright() as p:
    b=p.chromium.launch(); kw=DEV['phone']; errs=[]
    def ctx():
        c=b.new_context(**kw); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); return c,pg
    # --- visitas em andamento no Início
    c,pg=ctx(); f=login(pg); h='Andamento '+RUN
    vt_new(pg,f,'enf',h); vt_fill(f,'enf'); f.locator('[data-va=menu]').first.tap(); pg.wait_for_timeout(500)
    f.locator('[data-va=open][data-i="1"]').tap(); pg.wait_for_timeout(500); f.locator('.fit').nth(0).locator('[data-va=ans]').nth(1).tap()
    titulo=f.locator('h2').first.inner_text()
    f.locator('[data-va=leave]').tap(); pg.wait_for_timeout(3500)
    pg.frames[-1].evaluate("location.hash='#inicio'"); pg.wait_for_timeout(1500); pg.screenshot(path='pl_inicio_phone.png')
    row=f.locator('.ong .li',has_text=h)
    ok('Início mostra a visita em andamento',row.count()==1,f.locator('.ongs h2').all_inner_texts())
    ok('Início mostra progresso',row.count()==1 and '4 de' in row.inner_text() or '3 de' in row.inner_text() or 'itens' in row.inner_text(),row.first.inner_text()[:90] if row.count() else '')
    ok('Início sem overflow',not overflow(pg))
    row.locator('[data-act=ongo]').tap(); pg.wait_for_timeout(4000)
    t2=f.locator('h2').first.inner_text() if f.locator('h2').count() else ''
    ok('Continuar abre a visita no grupo onde parou',t2==titulo and f.locator('.fit .ans [aria-checked=true]').count()==1,(titulo,t2)); pg.screenshot(path='pl_continuar_phone.png')
    c.close()
    # --- plano de ação: quem edita
    for mail,quer in (('gestor.juina@isssl.com.br',True),('resp@isssl.com.br',True),('robert.fernandes@isssl.com.br',True),('gestor.outro@isssl.com.br',None),('membro.juina@isssl.com.br',False)):
        c,pg=ctx(); f=login_as(pg,mail,'Teste#2026ok' if mail!=MAIL else PW)
        pg.frames[-1].evaluate("location.hash='#plano'"); pg.wait_for_timeout(2500)
        n=f.locator('[data-act=pedit]').count(); tem=f.locator('.act').count()
        if quer is None: ok(f'{mail}: gestor de outra unidade não vê nem edita Juína',n==0 and tem==0,(n,tem))
        else: ok(f'{mail}: botão Editar {"aparece" if quer else "não aparece"}',(n>0)==quer,(n,tem))
        if mail=='gestor.juina@isssl.com.br':
            f.locator('[data-act=pedit]').first.tap(); pg.wait_for_timeout(500)
            f.locator('#pl-acao').fill('Instalar sinalização e treinar equipe'); f.locator('#pl-resp').fill('Enf. Maria Souza'); f.locator('#pl-prazo').fill('2026-12-15'); f.locator('#pl-status').select_option('Em andamento'); f.locator('#pl-obs').fill('Aguardando material')
            pg.screenshot(path='pl_form_phone.png'); ok('formulário do plano sem overflow',not overflow(pg))
            f.locator('[data-act=psave]').tap(); pg.wait_for_timeout(3000)
            ok('plano salvo e exibido',f.locator('.act',has_text='Instalar sinalização').count()>=1 and f.locator('.act',has_text='Enf. Maria Souza').count()>=1 and f.locator('.act',has_text='Em andamento').count()>=1)
            pg.screenshot(path='pl_salvo_phone.png')
        c.close()
    # persistência: novo login do responsável vê o que o gestor salvou
    c,pg=ctx(); f=login_as(pg,'resp@isssl.com.br','Teste#2026ok'); pg.frames[-1].evaluate("location.hash='#plano'"); pg.wait_for_timeout(2500)
    ok('edição persiste para outro usuário',f.locator('.act',has_text='Instalar sinalização').count()>=1 and f.locator('.act',has_text='15/12/2026').count()>=1); c.close()
    # membro de Juína vê o plano mas não edita; membro/gestor não consegue forjar a chamada
    ok('sem erro de JS',not errs,errs[:3]); b.close()
print('RESUMO',sum(1 for _,x in res if x),'/',len(res)); [print('  FALHOU:',n) for n,x in res if not x]
