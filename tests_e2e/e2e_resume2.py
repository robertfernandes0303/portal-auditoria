import random
from playwright.sync_api import sync_playwright
exec(open('e2e_resume.py').read().split('with sync_playwright')[0].split('def go_form')[0])
RUN=str(random.randint(100,999))
def overflow(pg): return pg.frames[-1].evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1")
def start(pg,f,key,unit=None):
    pg.frames[-1].evaluate("location.hash='#nova'"); pg.wait_for_timeout(600)
    f.locator('#nv-f').tap(); f.locator(f'[data-act=nvmod][data-v={key}]').tap(); pg.wait_for_timeout(300)
    if unit: f.locator('#nv-unit').select_option(unit); pg.wait_for_timeout(300)
    f.locator('[data-fa=start]').tap(); pg.wait_for_timeout(3000)
def vt_new(pg,f,key,h):
    start(pg,f,key); f.locator('#vh-h').fill(h); f.locator('#vh-r').fill('Aud'); f.locator('[data-va=begin]').tap(); pg.wait_for_timeout(2500)
    f.locator('[data-va=open][data-i="0"]').tap(); pg.wait_for_timeout(500)
def vt_fill(f,key):
    if key=='upa':
        for i in range(3):
            c=f.locator('.fit').nth(i); c.locator('[data-vi=resp]').fill('v'+str(i)); c.locator('[data-va=fonte][data-k="0"]').tap()
    else:
        for i in range(3): f.locator('.fit').nth(i).locator('[data-va=ans]').nth(i%3).tap()
def vt_meas(f,key):
    if key=='upa': return sum(1 for i in range(f.locator('.fit').count()) if f.locator('.fit').nth(i).locator('[data-vi=resp]').input_value())
    return f.locator('.fit .ans [aria-checked=true]').count()
def vt_resume(pg,f,key,h):
    start(pg,f,key); L=f.locator('.srow',has_text=h).locator('[data-va=load]'); n=L.count()
    if n: L.first.tap(); pg.wait_for_timeout(2500)
    return n
def exits(pg,how):
    if how=='sair': pg.frames[-1].evaluate("document.querySelector('[data-act=logout]').click()"); pg.wait_for_timeout(2500)
    elif how=='reload': pg.reload(); pg.wait_for_timeout(1500)
with sync_playwright() as p:
    b=p.chromium.launch()
    for dev,kw in DEV.items():
        errs=[]
        def newctx():
            c=b.new_context(**kw); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); return c,pg
        for key in ('v03','upa'):
            for how in ('sair','reload','bg'):
                tag=f'{dev}_{key}_{how}'; h=f'{dev} {key} {how} {RUN}'
                c,pg=newctx(); f=login(pg); vt_new(pg,f,key,h); vt_fill(f,key); a=vt_meas(f,key)
                if how=='bg': pg.frames[-1].evaluate("Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(800)
                else: exits(pg,how)
                if how=='reload': f=login(pg)
                else: c.close(); c,pg=newctx(); f=login(pg)
                n=vt_resume(pg,f,key,h); m=vt_meas(f,key) if n else -1
                ok(tag+' retomou com tudo',n==1 and m==a and a==3,(n,a,m)); ok(tag+' sem overflow',not overflow(pg)); c.close()
        # Institucional
        for how in ('sair','reload'):
            tag=f'{dev}_aud_{how}'
            import glob,os
            [os.remove(x) for x in glob.glob('portal_app/forms/institucional/dados_locais/Rascunho*')]
            c,pg=newctx(); f=login(pg); start(pg,f,'aud','Juína')
            f.locator('[data-fa=begin]').tap(); pg.wait_for_timeout(500); f.locator('#fh-resp').fill('Juliana Costa'); f.locator('[data-fa=begin]').tap(); pg.wait_for_timeout(800)
            f.locator('[data-fa=open][data-i="1"]').tap(); pg.wait_for_timeout(400)
            f.locator('[data-fa=ans][data-n="11"][data-k="0"]').tap(); f.locator('[data-fa=ans][data-n="12"][data-k="1"]').tap()
            f.locator('[data-fi=obs][data-n="12"]').fill('sem sinalização')
            a=f.locator('[aria-checked=true]').count(); exits(pg,how)
            if how=='reload': f=login(pg)
            else: c.close(); c,pg=newctx(); f=login(pg)
            start(pg,f,'aud','Juína'); r=f.locator('[data-fa=resume]').count()
            if r: f.locator('[data-fa=resume]').tap(); pg.wait_for_timeout(1500)
            f.locator('[data-fa=open][data-i="1"]').tap(); pg.wait_for_timeout(500)
            m=f.locator('[aria-checked=true]').count(); o=f.locator('[data-fi=obs][data-n="12"]').input_value() if f.locator('[data-fi=obs][data-n="12"]').count() else None
            ok(tag+' retomou com tudo',r==1 and m==a and a>=2 and o=='sem sinalização',(r,a,m,o)); ok(tag+' sem overflow',not overflow(pg)); c.close()
        ok(dev+' sem erro de JS',not errs,errs[:3])
    b.close()
print('RESUMO',sum(1 for _,x in res if x),'/',len(res)); [print('  FALHOU:',n) for n,x in res if not x]
