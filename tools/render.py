"""Render the story page to per-scene MP4 files by stepping the page's clock."""
import sys, asyncio, pathlib, subprocess, os, time
from playwright.async_api import async_playwright

SITE = pathlib.Path('/home/claude/site/index.html').as_uri() + '?video=1'
OUT = pathlib.Path('/home/claude/video/scenes'); OUT.mkdir(parents=True, exist_ok=True)
CAP_FPS = 30

async def render_scene(pg, tl, idxs, name):
    tmp = OUT / f'{name}.tmp.mp4'
    ff = subprocess.Popen(['ffmpeg', '-loglevel', 'error', '-y', '-f', 'image2pipe', '-framerate', str(CAP_FPS),
                           '-c:v', 'mjpeg', '-i', '-', '-vf', 'fps=30,format=yuv420p', '-c:v', 'libx264',
                           '-crf', '20', '-preset', 'veryfast', '-pix_fmt', 'yuv420p', '-r', '30', str(tmp)],
                          stdin=subprocess.PIPE)
    tscene = 0.0
    for i in idxs:
        await pg.evaluate(f'__show({i})')
        n = round(tl[i]['dur'] * CAP_FPS)
        for f in range(n):
            t = f / CAP_FPS
            await pg.evaluate(f'__tick({t},{tscene + t})')
            ff.stdin.write(await pg.screenshot(type='jpeg', quality=90))
        tscene += n / CAP_FPS
    ff.stdin.close(); ff.wait()
    if ff.returncode == 0:
        os.replace(tmp, OUT / f'{name}.mp4')
    print('done', name, flush=True)

async def worker(groups):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(viewport={'width': 1280, 'height': 720})
        await pg.goto(SITE); await pg.wait_for_timeout(500)
        tl = await pg.evaluate('__TL()')
        for name, idxs in groups:
            # reset state so each scene starts clean
            await pg.goto(SITE); await pg.wait_for_timeout(300)
            await render_scene(pg, tl, idxs, name)
        await b.close()

async def main(only):
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
        pg = await b.new_page(); await pg.goto(SITE); await pg.wait_for_timeout(300)
        tl = await pg.evaluate('__TL()'); await b.close()
    groups = {}
    for i, it in enumerate(tl):
        key = f"s{it['si']:02d}" + ('r' if it['type'] == 'recap' else '')
        groups.setdefault(key, []).append(i)
    items = [(k, v) for k, v in groups.items() if not only or k in only]
    t0 = time.time()
    await asyncio.gather(worker(items[0::2]), worker(items[1::2]))
    print('total', round(time.time() - t0), 's')

asyncio.run(main(sys.argv[1:]))
