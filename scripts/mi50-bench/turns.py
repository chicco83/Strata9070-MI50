# A chat like the app's: one long first turn, then short follow-ups that reuse the conversation; prints each turn's prompt line
# and the engine's STRATA_TRACE lines (lend / refill / read / checkpoints) for it.
#   python -I turns.py CONFIG.json PORT [EXTRA_PATH]
import json, os, subprocess, sys, time, urllib.request

cfg, port = sys.argv[1], sys.argv[2]
extra_path = sys.argv[3] if len(sys.argv) > 3 else ''
ctl = os.path.expandvars(r'%LOCALAPPDATA%\Strata\components\control\0.1.51')
if not os.path.isdir(ctl):
    ctl = r'C:\Users\chicco\AppData\Local\Programs\Strata\control'
py = r'C:\Users\chicco\AppData\Local\Programs\Strata\control\python\python.exe'
env = dict(os.environ)
if extra_path:
    env['PATH'] = extra_path + ';' + env['PATH']
log_path = json.load(open(cfg, encoding='utf-8-sig'))['log']
out = open(cfg + '.server.out', 'w', encoding='utf-8', errors='replace')
p = subprocess.Popen([py, os.path.join(ctl, 'serve', 'server.py'), '--engine', 'strata', '--config', cfg, '--port', port],
                     cwd=ctl, env=env, stdout=out, stderr=subprocess.STDOUT)

def tail_from(pos):
    with open(log_path, encoding='utf-8', errors='replace') as f:
        f.seek(pos)
        return f.read(), f.tell()

doc = open(r'C:\src\strata-mi50\docs\MULTI_GPU.md', encoding='utf-8').read() + open(r'C:\src\strata-mi50\docs\SECOND_GPU.md', encoding='utf-8').read()
turns = [
    "Ecco un documento. Riassumilo in cinque punti, in italiano.\n\n" + doc,
    "Quale opzione serve per dare a una seconda scheda il ruolo di Helper?",
    "E se le schede sono tre?",
    "Grazie. Rispondi solo con una parola: sì o no, la funzione è sperimentale?",
]
try:
    t0 = time.time()
    while time.time() - t0 < 900:
        if 'ready:' in open(cfg + '.server.out', encoding='utf-8', errors='replace').read():
            break
        if p.poll() is not None:
            print('server exited', p.returncode); sys.exit(1)
        time.sleep(2)
    print('ready after %.0f s' % (time.time() - t0), flush=True)
    messages = []
    pos = os.path.getsize(log_path)
    for i, q in enumerate(turns):
        messages.append({"role": "user", "content": q})
        req = {"model": "x", "messages": messages, "max_tokens": 250 if i == 0 else 120, "temperature": 0}
        r = urllib.request.Request('http://127.0.0.1:%s/v1/chat/completions' % port, data=json.dumps(req).encode(),
                                   headers={'Content-Type': 'application/json'})
        t1 = time.time(); d = json.load(urllib.request.urlopen(r, timeout=900)); wall = time.time() - t1
        answer = d['choices'][0]['message'].get('content') or ''
        messages.append({"role": "assistant", "content": answer})
        time.sleep(1.5)
        text, pos = tail_from(pos)
        print('== turn %d, wall %.1f s, usage %s' % (i + 1, wall, d.get('usage')), flush=True)
        for line in text.splitlines():
            if line.startswith(('strata trace:', 'strata serve: prompt', 'strata serve: conversation cache', 'strata prefill', 'prefill:')) \
               or 'PREFILL' in line or 'phase' in line.lower() and 'ms' in line:
                print('   ', line[:300])
        print('    answer:', answer[:120].replace('\n', ' '), flush=True)
finally:
    p.terminate()
    try: p.wait(30)
    except Exception: p.kill()
    subprocess.run(['taskkill', '/F', '/IM', 'strata.exe'], capture_output=True)
