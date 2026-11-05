"""Nova visita: Hospital e UPA/PAM não oferecem lista de unidades (sempre unidades novas em licitação); Enfermagem mantém; nome 'Visita Técnica · Enfermagem'."""
from playwright.sync_api import sync_playwright
cred=open('/tmp/cred.txt').read().split('Senha:')[1].strip()
ok_=True
def ok(n,c,x=''):
    global ok_; ok_&=bool(c); print('PASS' if c else 'FAIL',n,'' if c else x)
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp in (('desk',{'width':1360,'height':860}),('phone',{'width':390,'height':800})):
        pg=b.new_page(viewport=vp); errs=[]; pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000); f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
        f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(cred); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(4500)
        ok(tag+' nome Enfermagem',fr().evaluate("MODS.enf.name==='Visita Técnica · Enfermagem'"))
        ok(tag+' sem "Checklist de Visita Técnica"',fr().evaluate("!document.body.innerText.includes('Checklist de Visita Técnica')"))
        for mod,esc in (('v03',True),('upa',True),('enf',False),('aud',False)):
            fr().evaluate(f"S.nv={{mod:'{mod}',unit:'Juína'}};location.hash='#nova';render()"); pg.wait_for_timeout(500)
            has=fr().evaluate("!!document.getElementById('nv-unit')")
            ok(f'{tag} {mod} seletor de unidade {"ausente" if esc else "presente"}',has==(not esc))
            if esc:
                ok(f'{tag} {mod} aviso de unidade nova',fr().evaluate("document.body.innerText.includes('Unidade nova, em licitação')"))
                ok(f'{tag} {mod} botão iniciar liberado',fr().evaluate("!!document.querySelector('[data-fa=start]')"))
        # dentro do formulário: sem sugestões de unidades cadastradas
        fr().evaluate("S.nv={mod:'v03',unit:''};render()"); pg.wait_for_timeout(300)
        fr().evaluate("document.querySelector('[data-fa=start]').click()"); pg.wait_for_timeout(3500)
        ok(tag+' v03 sem datalist de unidades',fr().evaluate("!document.getElementById('vh-dl') && !!document.getElementById('vh-h')"))
        ok(tag+' sem erros JS',not errs,errs)
    b.close()
print('RESULT','OK' if ok_ else 'FALHOU')
