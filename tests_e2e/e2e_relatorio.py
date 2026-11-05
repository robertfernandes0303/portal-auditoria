"""Painel: abertura por unidade > formulário > grupo; relatório da visita com dados reais (sem demo)."""
from playwright.sync_api import sync_playwright
cred=open('/tmp/cred.txt').read().split('Senha:')[1].strip()
ok=True
def chk(n,c):
    global ok; ok&=bool(c); print('PASS' if c else 'FAIL',n)
INJ="""()=>{VISITS.length=0;
 function mk(id,unit,mod,statuses){var its=[];statuses.forEach(function(g,gi){g.forEach(function(s,k){its.push({g:gi,gn:'Grupo '+(gi+1),name:'Item '+gi+'.'+k,s:s,ev:0,obs:s==='NC'?'Obs real '+id+' '+gi+k:'',n:gi*10+k})})});
  VISITS.push({id:id,mod:mod,unit:unit,date:'2026-10-2'+id.length,resp:'Litana',acomp:'Karen e Ghabriella',items:its})}
 mk('A1','Juína','aud',[['C','C','C','NC'],['C','C','NA'],['NC','NC','C']]);
 mk('E1','Juína','enf',[['C','C'],['NC','C']]);
 mk('H1','Hospital X - Cidade/MT','v03',[['C','NC']]);
 MODS.v03.nm=true;
 S.f={unit:'all',mod:'all',per:'all',from:'',to:''};render()}"""
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp in (('desk',{'width':1360,'height':860}),('phone',{'width':390,'height':800})):
        pg=b.new_page(viewport=vp); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000)
        f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
        f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(cred); f.locator('#lg-pass').press('Enter')
        pg.wait_for_timeout(2500)
        fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(1200)
        fr().evaluate(INJ); pg.wait_for_timeout(600)
        chk(tag+' card de abertura existe',f.locator('text=Abertura por unidade e formulário').count()==1)
        chk(tag+' escopo (v03) fora da abertura',f.locator('text=Hospital X').count()==0)
        f.locator('details#dru-0 > summary').click(); pg.wait_for_timeout(300)
        chk(tag+' unidade abre e mostra formulários',f.locator('details#dru-0 details.drl').count()==2)
        f.locator('details#dru-0 details.drl >> nth=0').locator('summary').click(); pg.wait_for_timeout(300)
        chk(tag+' formulário mostra grupos',f.locator('details#dru-0 details.drl >> nth=0').locator('.row').count()>=2)
        fr().evaluate("render()"); pg.wait_for_timeout(300)
        chk(tag+' abertura persiste ao re-renderizar',f.locator('details#dru-0').get_attribute('open') is not None)
        # plano de ação editável no Painel
        fr().evaluate("location.hash='#painel'"); pg.wait_for_timeout(600)
        fr().evaluate("()=>{S.dopen={};render()}")
        f.locator('details#dru-0 > summary').click(); pg.wait_for_timeout(200)
        d0=f.locator('details#dru-0 details.drl >> nth=0'); d0.locator('summary').click(); pg.wait_for_timeout(300)
        chk(tag+' bloco de plano no Painel',d0.locator('text=Plano de ação ·').count()==1)
        d0.locator('[data-act=pedit]').first.click(); pg.wait_for_timeout(300)
        chk(tag+' editor abre',f.locator('#pl-acao').count()==1)
        f.locator('#pl-acao').fill('Trocar mobiliário danificado'); f.locator('#pl-resp').fill('Fulano - Engenharia'); f.locator('#pl-prazo').fill('2026-12-15'); f.locator('#pl-status').select_option('Em andamento'); f.locator('#pl-obs').fill('teste e2e')
        f.locator('[data-act=psave]').click(); pg.wait_for_timeout(2500)
        t2=fr().evaluate('document.body.innerText')
        chk(tag+' plano salvo aparece no Painel','Trocar mobiliário danificado' in t2 and 'Fulano - Engenharia' in t2)
        chk(tag+' plano gravado no cadastro',fr().evaluate("Object.keys(PLANS).length>0"))
        fr().evaluate("location.hash='#visita-A1'"); pg.wait_for_timeout(800)
        t=fr().evaluate('document.body.innerText'); print(errs[:2]); print(t[:300].replace(chr(10),' / '))
        chk(tag+' responsável real',('Litana' in t) and ('Karen e Ghabriella' in t))
        chk(tag+' fotografia 6/9 = 66,7%','66,7%' in t and '9 eram aplicáveis' in t and '1. A fotografia da visita' in t)
        chk(tag+' blocos 2,3,4',all(x in t for x in ('2. Conformidade por seção','3. Frentes com maior concentração','4. O que aparece sólido')))
        chk(tag+' observação real na NC','Obs real A1' in t)
        chk(tag+' sem texto demo',not any(x in t for x in ('Sem evidência formal arquivada','Gestor e coordenação assistencial')))
        chk(tag+' sem overflow horizontal',not fr().evaluate("document.documentElement.scrollWidth>window.innerWidth+1"))
        chk(tag+' sem erros JS',not errs)
    b.close()
print('RESULT','OK' if ok else 'FALHOU')
