import random,glob,openpyxl
from playwright.sync_api import sync_playwright
exec(open('e2e_resume2.py').read().split('\nwith sync_playwright')[0])
def srv_draft_count(h):
    import json
    n=0
    for x in glob.glob('portal_app/forms/enfermagem/dados_locais/Rascunho_*.json'):
        d=json.load(open(x)); s=json.dumps(d,ensure_ascii=False)
        if h in s: n+=len(json.loads(s).get('dados',d).get('respostas',{}) if isinstance(d,dict) else {})
    return n
with sync_playwright() as p:
    b=p.chromium.launch(); kw=DEV['phone']; errs=[]
    def newctx():
        c=b.new_context(**kw); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); return c,pg
    # T1 queda de rede
    c,pg=newctx(); f=login(pg); h='T1 rede '+RUN; vt_new(pg,f,'enf',h)
    c.set_offline(True); vt_fill(f,'enf'); pg.wait_for_timeout(1500)
    ok('T1 offline: interface continua respondendo',f.locator('.fit .ans [aria-checked=true]').count()==3)
    c.set_offline(False); pg.wait_for_timeout(7000)
    ok('T1 volta a rede: rascunho chegou ao servidor',srv_draft_count(h)==3,srv_draft_count(h))
    ok('T1 segue logado e na tela',f.locator('.fit').count()==4 or f.locator('#lg-user').count()==0, f.locator('#lg-user').count())
    c.close()
    # T2 botão voltar (Android) e girar a tela
    c,pg=newctx(); f=login(pg); h='T2 voltar '+RUN; vt_new(pg,f,'enf',h); vt_fill(f,'enf'); pg.wait_for_timeout(800)
    pg.evaluate("history.back()"); pg.wait_for_timeout(1800)
    st=pg.frames[-1].evaluate("location.hash")
    ok('T2 voltar do navegador não derruba o app',F(pg).locator('#lg-user').count()==0,st)
    pg.set_viewport_size({'width':844,'height':390}); pg.wait_for_timeout(600); ok('T2 paisagem sem overflow',not overflow(pg))
    pg.set_viewport_size({'width':390,'height':844}); pg.wait_for_timeout(600); ok('T2 retrato sem overflow',not overflow(pg)); c.close()
    # T3 duplo toque em Enviar + conteúdo hostil + foto grande + envio
    c,pg=newctx(); f=login(pg); h='T3 envio '+RUN; vt_new(pg,f,'enf',h)
    n=f.locator('.fit').count()
    for i in range(n): f.locator('.fit').nth(i).locator('[data-va=ans]').nth(0).tap()
    f.locator('.vtd summary').first.tap(); f.locator('[data-vi=obs]').first.fill('=HYPERLINK("http://x","clique") 😀 ação "áéí" '+'x'*3000)
    with pg.expect_file_chooser() as fc: f.locator('[data-va=file]').first.tap()
    fc.value.set_files('/tmp/grande.jpg'); pg.wait_for_timeout(7000)
    ok('T3 foto grande (4032x3024) anexada',f.locator('.anx').count()==1,f.locator('.fit .note').all_inner_texts()[:1])
    f.locator('[data-va=conclude]').tap(); pg.wait_for_timeout(2500)
    if f.locator('[data-va=send][data-forced="1"]').count(): f.locator('[data-va=send][data-forced="1"]').tap()
    elif f.locator('[data-va=send]').count(): f.locator('[data-va=send]').first.tap()
    pg.wait_for_timeout(600)
    f.locator('[data-va=confirm]').dblclick(); pg.wait_for_timeout(6000)
    ok('T3 envio concluído',f.locator('.okic').count()==1)
    wb=openpyxl.load_workbook('portal_app/forms/enfermagem/dados_locais/Checklist_visita_tecnica.xlsx')
    ws=wb['Visitas']; hs=[r for r in ws.iter_rows(values_only=True) if r and any(h==str(c) for c in r)]
    ok('T3 duplo toque gravou 1 visita só',len(hs)==1,len(hs))
    wi=wb['Itens']; cells=[c for r in wi.iter_rows() for c in r if c.value and 'HYPERLINK' in str(c.value)]
    ok('T3 texto com = é gravado como texto (não fórmula)',len(cells)>=1 and all(c.data_type=='s' for c in cells),[c.data_type for c in cells])
    ok('T3 sem overflow',not overflow(pg)); c.close()
    ok('sem erro de JS',not errs,errs[:3]); b.close()
print('RESUMO',sum(1 for _,x in res if x),'/',len(res)); [print('  FALHOU:',n) for n,x in res if not x]
