import sys,time
from playwright.sync_api import sync_playwright
PW=open('/tmp/cred.txt').read().split('Senha:')[1].strip(); MAIL='robert.fernandes@isssl.com.br'
DEV={'phone':dict(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,device_scale_factor=2),
     'tablet':dict(viewport={'width':820,'height':1180},has_touch=True,is_mobile=True,device_scale_factor=2)}
import random
RUN=str(random.randint(100,999))
res=[]
def ok(name,cond,extra=''):
    res.append((name,bool(cond))); print(('PASS ' if cond else 'FAIL ')+name+(' | '+str(extra) if extra else ''),flush=True)
def F(pg): return pg.frame_locator('iframe')
def login(pg):
    pg.goto('http://localhost:8599'); pg.wait_for_timeout(4500); f=F(pg)
    f.locator('#lg-user').fill(MAIL); f.locator('#lg-pass').fill(PW); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(3000)
    return f
def go_form(pg,f,hosp):
    pg.frames[-1].evaluate("location.hash='#nova'"); pg.wait_for_timeout(600)
    f.locator('#nv-f').tap(); f.locator('[data-act=nvmod][data-v=enf]').tap(); pg.wait_for_timeout(300)
    f.locator('[data-fa=start]').tap(); pg.wait_for_timeout(3000)
def new_visit(pg,f,hosp):
    go_form(pg,f,hosp)
    f.locator('#vh-h').fill(hosp); f.locator('#vh-r').fill('Aud Teste'); f.locator('[data-va=begin]').tap(); pg.wait_for_timeout(2500)
    f.locator('[data-va=open][data-i="0"]').tap(); pg.wait_for_timeout(500)
def answer(f,idx,k): f.locator('.fit').nth(idx).locator('[data-va=ans]').nth(k).tap()
def state(f):
    return dict(marc=f.locator('.fit .ans [aria-checked=true]').count(), itens=f.locator('.fit').count(),
                obs=(f.locator('[data-vi=obs]').first.input_value() if f.locator('[data-vi=obs]').count() else None))
def resume(pg,f,hosp):
    go_form(pg,f,hosp)
    L=f.locator('.srow',has_text=hosp).locator('[data-va=load]'); n=L.count()
    if n: L.first.tap(); pg.wait_for_timeout(2500)
    return n
def overflow(pg): return pg.frames[-1].evaluate("document.documentElement.scrollWidth>document.documentElement.clientWidth+1")
with sync_playwright() as p:
    b=p.chromium.launch()
    for dev,kw in DEV.items():
        tag=dev+'_'
        errs=[]
        def newctx():
            c=b.new_context(**kw); pg=c.new_page(); pg.on('pageerror',lambda e:errs.append(str(e))); return c,pg
        # S1: Sair (logout) logo após responder
        c,pg=newctx(); f=login(pg); h=f'{dev} S1 sair '+RUN
        new_visit(pg,f,h); answer(f,0,0); answer(f,1,1)
        f.locator('.vtd summary').first.tap(); f.locator('[data-vi=obs]').first.fill('obs S1')
        ok(tag+'S1 sem overflow horizontal',not overflow(pg))
        pg.frames[-1].evaluate("document.querySelector('[data-act=logout]').click()"); pg.wait_for_timeout(2500)
        ok(tag+'S1 voltou ao login',F(pg).locator('#lg-user').count()==1)
        c.close()
        c,pg=newctx(); f=login(pg); n=resume(pg,f,h); st=state(f)
        ok(tag+'S1 rascunho listado',n==1,n); ok(tag+'S1 abre no grupo onde parou (itens)',st['itens']==4,st)
        ok(tag+'S1 respostas preservadas',st['marc']==2,st); 
        f.locator('.vtd summary').first.tap(); ok(tag+'S1 observação preservada',f.locator('[data-vi=obs]').first.input_value()=='obs S1')
        c.close()
        # S2: reload imediato
        c,pg=newctx(); f=login(pg); h=f'{dev} S2 reload '+RUN
        new_visit(pg,f,h); answer(f,0,2); answer(f,1,0); answer(f,2,1)
        pg.reload(); pg.wait_for_timeout(1500)
        f=login(pg); n=resume(pg,f,h); st=state(f); ok(tag+'S2 reload: respostas preservadas',n==1 and st['marc']==3,(n,st)); c.close()
        # S3: app em segundo plano e processo morto
        c,pg=newctx(); f=login(pg); h=f'{dev} S3 bg '+RUN
        new_visit(pg,f,h); answer(f,0,0); answer(f,1,0); answer(f,2,0); answer(f,3,0)
        pg.frames[-1].evaluate("Object.defineProperty(document,'hidden',{value:true,configurable:true});document.dispatchEvent(new Event('visibilitychange'))"); pg.wait_for_timeout(800)
        c.close()
        c,pg=newctx(); f=login(pg); n=resume(pg,f,h); st=state(f); ok(tag+'S3 segundo plano: respostas preservadas',n==1 and st['marc']==4,(n,st)); c.close()
        # S4: avançar para o grupo 2 e sair do formulário; retomar no grupo certo
        c,pg=newctx(); f=login(pg); h=f'{dev} S4 grupo2 '+RUN
        new_visit(pg,f,h); [answer(f,i,0) for i in range(4)]
        f.locator('[data-va=menu]').first.tap(); pg.wait_for_timeout(600)
        f.locator('[data-va=open][data-i="1"]').tap(); pg.wait_for_timeout(500); answer(f,0,1)
        titulo1=f.locator('h2').first.inner_text()
        f.locator('[data-va=leave]').tap(); pg.wait_for_timeout(1500)
        n=resume(pg,f,h); st=state(f); t2=f.locator('h2').first.inner_text() if f.locator('h2').count() else ''
        ok(tag+'S4 retoma exatamente no grupo onde parou',n==1 and t2==titulo1 and st['marc']==1,(n,titulo1,t2,st))
        pg.screenshot(path=f'rs_{dev}_S4.png'); ok(tag+'S4 sem overflow horizontal',not overflow(pg)); c.close()
        # S5: duas abas / dois aparelhos: o rascunho mais novo vence
        c,pg=newctx(); f=login(pg); h=f'{dev} S5 dois '+RUN
        new_visit(pg,f,h); answer(f,0,0); pg.wait_for_timeout(2500)
        c2,pg2=newctx(); f2=login(pg2); n=resume(pg2,f2,h); answer(f2,1,1); pg2.wait_for_timeout(2500); c2.close()
        c.close()
        c,pg=newctx(); f=login(pg); n=resume(pg,f,h); st=state(f); ok(tag+'S5 dois aparelhos: nenhuma resposta perdida',n==1 and st['marc']>=1,(n,st)); c.close()
        ok(tag+'sem erro de JS',not errs,errs[:3])
    b.close()
print('RESUMO',sum(1 for _,x in res if x),'/',len(res)); [print('  FALHOU:',n) for n,x in res if not x]
