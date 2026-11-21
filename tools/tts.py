import sys, json, numpy as np, soundfile as sf, sherpa_onnx, opencc
M = '/home/claude/tts/model/kokoro-multi-lang-v1_1/'
cfg = sherpa_onnx.OfflineTtsConfig(model=sherpa_onnx.OfflineTtsModelConfig(
    kokoro=sherpa_onnx.OfflineTtsKokoroModelConfig(model=M+'model.onnx', voices=M+'voices.bin', tokens=M+'tokens.txt',
        data_dir=M+'espeak-ng-data', dict_dir=M+'dict', lexicon=M+'lexicon-us-en.txt,'+M+'lexicon-zh.txt'),
    num_threads=2), rule_fsts=M+'date-zh.fst,'+M+'phone-zh.fst,'+M+'number-zh.fst', max_num_sentences=2)
tts = sherpa_onnx.OfflineTts(cfg)
cc = opencc.OpenCC('t2s')
FIX = [('TOTO','偷頭'),('耶律','椰律'),('澶淵','蝉渊'),('澶州','蝉州'),('燕雲','烟云'),('高麗','高离'),('乾了','干了'),('zzz',''),('呼……',''),
       ('10～12','十到十二'),('10到12','十到十二'),('960','九六零'),('1004','一零零四'),('1127','一一二七'),('1115','一一一五'),('1125','一一二五'),
       ('「',''),('」',''),('〈',''),('〉',''),('——','，'),('……','，'),('｜','，'),('＋','和'),('▶','')]
def prep(t):
    for a,b in FIX: t = t.replace(a,b)
    return cc.convert(t)
def say(text, sid, speed, out):
    a = tts.generate(prep(text), sid=sid, speed=speed)
    sf.write(out, np.array(a.samples), a.sample_rate)
    return len(a.samples)/a.sample_rate

if __name__ == '__main__':
    jobs = json.load(open(sys.argv[1]))
    res = {}
    for j in jobs:
        res[j['key']] = round(say(j['text'], j['sid'], j['speed'], j['out']), 3)
        print(j['key'], res[j['key']], flush=True)
    json.dump(res, open(sys.argv[2], 'w'))
