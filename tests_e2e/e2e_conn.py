from playwright.sync_api import sync_playwright
exec(open('e2e_resume2.py').read().split('\nwith sync_playwright')[0])
with sync_playwright() as p:
    b=p.chromium.launch(); errs=[]
    for tag,kw in (('phone',DEV['phone']),('desk',dict(viewport={'width':1360,'height':860}))):
        c=b.new_context(**kw); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e)))
        f=login(pg); pg.frames[-1].evaluate("location.hash='#permissoes'"); pg.wait_for_timeout(1500)
        pg.frames[-1].evaluate("S.ct='conn';render()"); pg.wait_for_timeout(1200)
        ok(tag+' linhas de conexão',f.locator('.cnr').count()>=1)
        ok(tag+' botões testar',f.locator('[data-act=ctest1]').count()>=1)
        pg.frames[-1].evaluate("S.cf='aud';render()"); pg.wait_for_timeout(500)
        f.locator('.cnr input[data-f=planilha]').first.fill('https://docs.google.com/spreadsheets/d/1k6c7s33yJwOdw43v671D07jeJpSPiNwlO9aTxSF1678/edit'); f.locator('.cnr input[data-f=planilha]').first.press('Tab'); pg.wait_for_timeout(500)
        ok(tag+' remover pede confirmação',(f.locator('[data-act=crm]').first.click() or True) and f.locator('[data-act=crm2]').count()==1)
        f.locator('[data-act=crm2]').first.click(); pg.wait_for_timeout(300)
        ok(tag+' conexão removida',f.locator('.cnr input[data-f=planilha]').first.input_value()=='')
        ok(tag+' sem overflow',not overflow(pg)); pg.screenshot(path=f'conn_{tag}.png'); c.close()
    ok('sem erros JS',not errs,errs); b.close()
