"""產生《銀兩君的時空帳本》台灣腔配音。
用法（在 Mac 終端機）：
    cd "/Users/august/AI/Claude/歷史動畫故事教學"
    pip3 install edge-tts
    python3 make_voices.py
完成後，配音會存在同一個資料夾裡的 voices_tw/。
"""
import asyncio, json, os, sys

try:
    import edge_tts
except ImportError:
    sys.exit('請先執行：pip3 install edge-tts')

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'voices_tw')
os.makedirs(OUT, exist_ok=True)
jobs = json.load(open(os.path.join(HERE, 'voice_jobs.json'), encoding='utf-8'))

async def one(j, sem):
    path = os.path.join(OUT, j['key'] + '.mp3')
    if os.path.exists(path) and os.path.getsize(path) > 1000:
        return 'skip'
    async with sem:
        for attempt in range(6):
            try:
                c = edge_tts.Communicate(j['text'], j['voice'], rate=j['rate'], pitch=j['pitch'])
                await c.save(path)
                return 'ok'
            except Exception as e:
                err = e
                await asyncio.sleep(2 + attempt * 2)
        return f'失敗：{err}'

async def main():
    sem = asyncio.Semaphore(2)
    tasks = [one(j, sem) for j in jobs]
    done = 0
    for j, coro in zip(jobs, asyncio.as_completed(tasks)):
        await coro
        done += 1
        print(f'\r進度 {done}/{len(jobs)}', end='', flush=True)
    bad = [j['key'] for j in jobs if not os.path.exists(os.path.join(OUT, j['key'] + '.mp3'))]
    print('\n完成！' if not bad else f'\n有 {len(bad)} 句失敗，請再執行一次：{bad}')

asyncio.run(main())
