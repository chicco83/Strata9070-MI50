# Start a Strata server with a config, wait for ready, send one fixed request, print the answer and speeds, stop the server
import subprocess, sys, time, json, urllib.request, os
cfg, port, extra_path = sys.argv[1], sys.argv[2], (sys.argv[3] if len(sys.argv) > 3 else '')
ctl = r'C:\Users\chicco\AppData\Local\Programs\Strata\control'
env = dict(os.environ)
if extra_path: env['PATH'] = extra_path + ';' + env['PATH']
log = open(cfg + '.server.out', 'w', encoding='utf-8', errors='replace')
p = subprocess.Popen([ctl + r'\python\python.exe', ctl + r'\serve\server.py', '--engine', 'strata', '--config', cfg, '--port', port],
                     cwd=ctl, env=env, stdout=log, stderr=subprocess.STDOUT)
t0 = time.time()
try:
    while time.time() - t0 < 900:
        txt = open(cfg + '.server.out', encoding='utf-8', errors='replace').read()
        if 'ready:' in txt: break
        if p.poll() is not None: print('server exited', p.returncode); sys.exit(1)
        time.sleep(2)
    print('ready after %.0f s' % (time.time() - t0), flush=True)
    qs = ["Rispondi in italiano, in tre frasi: perché il cielo è blu?",
          "Write a Python function that merges two sorted lists, with a short docstring and two tests.",
          "Spiega in cinque punti come funziona una pompa di calore domestica.",
          "Rispondi in italiano, in tre frasi: perché il cielo è blu?"]
    for q in qs:
        req = {"model": "x", "messages": [{"role": "user", "content": q}], "max_tokens": 300, "temperature": 0}
        r = urllib.request.Request('http://127.0.0.1:%s/v1/chat/completions' % port, data=json.dumps(req).encode(), headers={'Content-Type': 'application/json'})
        t1 = time.time(); d = json.load(urllib.request.urlopen(r, timeout=900)); dt = time.time() - t1
        if 'error' in d: print('ERROR', d['error'])
        else: print('wall %.1f s' % dt, 'ANSWER:', (d['choices'][0]['message'].get('content') or '')[:160].replace(chr(10), ' '), flush=True)
    time.sleep(1)
    lg = json.load(open(cfg, encoding='utf-8'))['log']
    lines = [l for l in open(lg, encoding='utf-8', errors='replace') if 'generated in' in l or 'swapped' in l or 'CUDA1:' in l or 'VRAM free with everything' in l or 'expert cache' in l and 'slots' in l]
    print(''.join(lines[-12:]))
finally:
    p.terminate()
    try: p.wait(30)
    except Exception: p.kill()
    subprocess.run(['taskkill', '/F', '/IM', 'strata.exe'], capture_output=True)
