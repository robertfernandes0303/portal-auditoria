from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp in (('d',{'width':1360,'height':860}),('m',{'width':390,'height':800})):
        pg=b.new_page(viewport=vp); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000)
        f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
        f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(open('/tmp/cred.txt').read().split('Senha:')[1].strip()); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(3000)
        for mod in ('upa','v03','enf'):
            fr().evaluate("location.hash='#nova'"); pg.wait_for_timeout(700)
            f.locator('#nv-f').click(); f.locator('[data-act=nvmod][data-v=%s]'%mod).click(); pg.wait_for_timeout(300)
            f.locator('[data-fa=start]').click(); pg.wait_for_timeout(3500)
            n=f.locator('#vh-e').count()
            if mod=='enf': print(tag,mod,'campo edital presente:',n,'(esperado 0)'); continue
            f.locator('#vh-h').fill('Hospital Novo Licitacao'); pg.wait_for_timeout(200)
            a=f.locator('#vh-e').is_visible(); f.locator('#vh-e').fill('Edital 9/2026')
            f.locator('#vh-h').fill('Juína'); pg.wait_for_timeout(200)
            b2=f.locator('#vh-e').is_visible(); v=f.locator('#vh-e').input_value()
            f.locator('#vh-h').fill('Unidade X'); pg.wait_for_timeout(200)
            c=f.locator('#vh-e').is_visible()
            print(tag,mod,'novo:',a,'(True) cadastrada:',b2,'(False) limpou:',repr(v),"(''), volta novo:",c,'(True)')
        print(tag,'errs',errs)
