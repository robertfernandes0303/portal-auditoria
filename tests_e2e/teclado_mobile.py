import sys
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b=p.chromium.launch(); ctx=b.new_context(viewport={'width':390,'height':844},has_touch=True,is_mobile=True,device_scale_factor=2); pg=ctx.new_page()
    pg.goto('http://localhost:8599'); pg.wait_for_timeout(5000)
    f=pg.frame_locator('iframe'); fr=lambda: pg.frames[-1]
    f.locator('#lg-user').fill('t@teste.local'); f.locator('#lg-pass').fill('TesteLocal1'); f.locator('#lg-pass').press('Enter'); pg.wait_for_timeout(3500)
    fr().evaluate("location.hash='#nova'"); pg.wait_for_timeout(700)
    f.locator('#nv-f').click(); f.locator('[data-act=nvmod][data-v=enf]').click(); pg.wait_for_timeout(300)
    f.locator('[data-fa=start]').click(); pg.wait_for_timeout(3500)
    f.locator('#vh-h').fill('Hospital Teste'); f.locator('#vh-r').fill('Auditor X')
    f.locator('[data-va=begin]').click(); pg.wait_for_timeout(2500)
    if f.locator('[data-va=startnew]').count(): f.locator('[data-va=startnew]').click(); pg.wait_for_timeout(2500)
    f.locator('[data-va=open][data-i="0"]').click(); pg.wait_for_timeout(500)
    it=f.locator('.fit').nth(0); it.locator('[data-va=ans]').nth(2).click(); pg.wait_for_timeout(300)
    sm=it.locator('.vtd summary')
    if sm.count(): sm.first.click(); pg.wait_for_timeout(300)
    o=it.locator('[data-vi=obs]'); o.first.tap(); pg.wait_for_timeout(200)
    pg.keyboard.type('abc',delay=80)
    res=[]
    for t in range(3):
        pg.wait_for_timeout(5000)
        act=fr().evaluate("(function(){var a=document.activeElement;return a?a.tagName+'#'+a.id:''})()")
        pg.keyboard.type('x',delay=50)
        res.append((act, o.first.input_value()))
    print(res)
    b.close()
