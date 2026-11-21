"""Synthesize background music + cues aligned to the video timeline."""
import json, sys, wave
import numpy as np

SR = 44100
tl = json.load(open(sys.argv[1]))
FPS = 30
# timeline start times (frame-rounded, same as renderer)
t = 0.0; starts = []
for it in tl:
    starts.append(t); t += round(it['dur'] * FPS) / FPS
total = t + 0.5
N = int(total * SR)
out = np.zeros(N)

def pluck(f, t0, vol, length=1.6):
    n = int(length * SR); s = int(t0 * SR)
    if s >= N: return
    n = min(n, N - s)
    tt = np.arange(n) / SR
    env = np.exp(-tt * 3.2) * np.minimum(1, tt / 0.008)
    w = (np.sin(2*np.pi*f*tt) + 0.45*np.sin(2*np.pi*2*f*tt)*np.exp(-tt*5) + 0.2*np.sin(2*np.pi*3*f*tt)*np.exp(-tt*8))
    out[s:s+n] += vol * env * w

PENTA = [293.66, 329.63, 369.99, 440, 493.88, 587.33, 659.25, 739.99]
SEQS = [[0,2,4,5,4,2,3,1, 0,2,4,7,5,4,2,0], [5,4,2,4,5,7,5,4, 2,1,0,1,2,4,2,0]]
step = 0.52; n = 0; x = 0.0
while x < total - 1:
    seq = SEQS[(n // 32) % 2]
    pluck(PENTA[seq[n % 16]], x, 0.055)
    if n % 4 == 0: pluck(PENTA[0] / 2, x, 0.05, 2.4)
    if n % 8 == 4: pluck(PENTA[4] / 2, x, 0.03, 2.0)
    n += 1; x += step

for it, s in zip(tl, starts):
    if it['type'] == 'title':
        for k, f in enumerate([146.83, 220.0, 293.66]):
            pluck(f, s + 0.2 + k * 0.12, 0.12, 2.5)
    if it['type'] == 'reveal':
        pluck(659.25, s + 0.05, 0.16, 0.7); pluck(987.77, s + 0.17, 0.16, 0.9)
    if it['type'] == 'card':
        pluck(880, s + 0.1, 0.08, 0.6)

# simple reverb
d = int(0.23 * SR); rev = out.copy()
for k in range(1, 5):
    rev[d*k:] += out[:-d*k] * (0.35 ** k)
# fades
fade = int(2 * SR); rev[-fade:] *= np.linspace(1, 0, fade); rev[:int(.5*SR)] *= np.linspace(0, 1, int(.5*SR))
rev = rev / np.max(np.abs(rev)) * 0.6
pcm = (rev * 32767).astype(np.int16)
st = np.repeat(pcm[:, None], 2, axis=1)
with wave.open(sys.argv[2], 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes())
print('audio sec', round(total, 2))
