from playwright.sync_api import sync_playwright
import io
from PIL import Image
im=Image.new('RGB',(2400,1800),(120,160,200)); im.save('/tmp/foto.jpg')
with sync_playwright() as p:
    b=p.chromium.launch()
    for tag,vp in (('d',{'width':1360,'height':860}),('m',{'width':390,'height':800})):
        pg=b.new_page(viewport=vp); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000)
        f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
        f.locator('#lg-user').fill('robert.fernandes@isssl.com.br'); f.locator('#lg-pass').fill(open('/tmp/cred.txt').read().split('Senha:')[1].strip()); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(3000)
        fr().evaluate("location.hash='#nova'"); pg.wait_for_timeout(700)
        f.locator('#nv-f').click(); f.locator('[data-act=nvmod][data-v=v03]').click(); pg.wait_for_timeout(300)
        pg.screenshot(path=f'w_nova_{tag}.png')
        f.locator('[data-fa=start]').click(); pg.wait_for_timeout(3500)
        pg.screenshot(path=f'w_head_{tag}.png')
        f.locator('#vh-h').fill('Hospital Teste '+tag); f.locator('#vh-r').fill('Juliana Costa')
        f.locator('[data-va=begin]').click(); pg.wait_for_timeout(2500)
        pg.screenshot(path=f'w_menu_{tag}.png')
        f.locator('[data-va=open][data-i="0"]').click(); pg.wait_for_timeout(500)
        its=f.locator('.fit'); n=its.count(); print(tag,'itens grupo0',n)
        f.locator('[data-va=conclude]').click(); pg.wait_for_timeout(300)
        print(tag,'err',f.locator('[role=alert]').all_inner_texts()[:1])
        for i in range(n):
            f.locator('.fit').nth(i).locator('[data-va=ans]').nth(i%4).click()
        f.locator('.vtd summary').first.click(); pg.wait_for_timeout(200)
        f.locator('[data-vi=obs]').first.fill('porta sem sinalização'); print(tag,'campos',f.locator('.fit').first.locator('textarea').count())
        # upload
        with pg.expect_file_chooser() as fc:
            f.locator('[data-va=file]').first.click()
        fc.value.set_files('/tmp/foto.jpg'); pg.wait_for_timeout(4000)
        pg.screenshot(path=f'w_group_{tag}.png')
        print(tag,'anexos',f.locator('.anx').count())
        f.locator('[data-va=conclude]').click(); pg.wait_for_timeout(2500)
        f.locator('[data-va=sint]').click(); pg.wait_for_timeout(400)
        f.locator('#s0setor').fill('UTI'); f.locator('#s0acao').fill('Ampliar equipe'); pg.screenshot(path=f'w_sint_{tag}.png')
        f.locator('[data-va=menu]').last.click(); pg.wait_for_timeout(500)
        f.locator('[data-va=pend]').click(); pg.wait_for_timeout(400)
        f.locator('[data-vi=pend]').first.fill('Alvará sanitário'); f.locator('#obsf').fill('ok'); pg.wait_for_timeout(300)
        f.locator('[data-va=menu]').last.click(); pg.wait_for_timeout(500)
        f.locator('[data-va=send][data-forced="1"]').click(); pg.wait_for_timeout(500)
        pg.screenshot(path=f'w_review_{tag}.png')
        f.locator('[data-va=confirm]').click(); pg.wait_for_timeout(4000)
        pg.screenshot(path=f'w_done_{tag}.png')
        print(tag,errs,f.locator('.okic').count(),f.locator('.list .li b').all_inner_texts()[:7])
    b.close()
