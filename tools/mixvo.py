"""Mix voice clips + background music aligned to the video timeline."""
import json, sys, numpy as np, soundfile as sf
SR = 44100; FPS = 30
tl = json.load(open(sys.argv[1])); S = json.load(open('/home/claude/tts/S.json'))
bgm, sr = sf.read(sys.argv[2]); assert sr == SR
bgm = bgm.mean(axis=1) if bgm.ndim > 1 else bgm
keys = []; li = {}
for it in tl:
    si = it['si']
    if it['type'] == 'line':
        n = li.get(si, 0); keys.append(f'{si}_l{n}'); li[si] = n + 1
    elif it['type'] == 'recap': keys.append('recap')
    else: keys.append(f"{si}_{it['type']}")
t = 0.0; total = sum(round(i['dur'] * FPS) / FPS for i in tl) + 0.5
N = int(total * SR); voice = np.zeros(N)
for it, k in zip(tl, keys):
    lead = 0.6 if it['type'] == 'title' else 0.25
    x, r = sf.read(f'/home/claude/tts/wav/{k}.wav')
    if x.ndim > 1: x = x.mean(axis=1)
    x = np.interp(np.arange(0, len(x), r / SR), np.arange(len(x)), x)  # resample to 44.1k
    s = int((t + lead) * SR); e = min(N, s + len(x)); voice[s:e] += x[:e - s]
    t += round(it['dur'] * FPS) / FPS
voice = voice / (np.max(np.abs(voice)) + 1e-9) * 0.85
b = np.zeros(N); b[:min(N, len(bgm))] = bgm[:N]
# duck music under voice
env = np.convolve(np.abs(voice), np.ones(4410) / 4410, mode='same')
duck = np.where(env > 0.01, 0.35, 0.7)
duck = np.convolve(duck, np.ones(8820) / 8820, mode='same')
mix = voice + b * duck
mix = mix / np.max(np.abs(mix)) * 0.92
sf.write(sys.argv[3], np.stack([mix, mix], 1), SR, subtype='PCM_16')
print('mixed', round(total, 1), 's')
