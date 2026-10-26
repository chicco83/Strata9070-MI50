# Big prompt reads with a warm engine: after ready, wait WARM_S (the RAM copy of the experts is built in the background), then two
# different big prompts (no reuse), max_tokens 16; prints each prompt line and the helper-source evidence lines.
#   python -I prefill_bench.py CONFIG.json PORT [WARM_S]
import json, os, subprocess, sys, time, urllib.request

cfg, port = sys.argv[1], sys.argv[2]
warm = float(sys.argv[3]) if len(sys.argv) > 3 else 120
ctl = os.path.expandvars(r'%LOCALAPPDATA%\Strata\components\control\0.1.51')
py = r'C:\Users\chicco\AppData\Local\Programs\Strata\control\python\python.exe'
log_path = json.load(open(cfg, encoding='utf-8-sig'))['log']
out = open(cfg + '.server.out', 'w', encoding='utf-8', errors='replace')
p = subprocess.Popen([py, os.path.join(ctl, 'serve', 'server.py'), '--engine', 'strata', '--config', cfg, '--port', port],
                     cwd=ctl, stdout=out, stderr=subprocess.STDOUT)
docs = [r'C:\src\strata-mi50\docs\MULTI_GPU.md', r'C:\src\strata-mi50\docs\SECOND_GPU.md', r'C:\src\strata-mi50\docs\DETAILS.md']
text = [open(d, encoding='utf-8').read() for d in docs]
prompts = ["Riassumi in tre punti:\n\n" + text[0] + text[1], "Riassumi in tre punti:\n\n" + text[2][:42000]]
try:
    t0 = time.time()
    while time.time() - t0 < 900:
        if 'ready:' in open(cfg + '.server.out', encoding='utf-8', errors='replace').read():
            break
        if p.poll() is not None:
            print('server exited', p.returncode); sys.exit(1)
        time.sleep(2)
    print('ready after %.0f s; warming %.0f s' % (time.time() - t0, warm), flush=True)
    time.sleep(warm)
    pos = os.path.getsize(log_path)
    for q in prompts:
        req = {"model": "x", "messages": [{"role": "user", "content": q}], "max_tokens": 16, "temperature": 0}
        r = urllib.request.Request('http://127.0.0.1:%s/v1/chat/completions' % port, data=json.dumps(req).encode(),
                                   headers={'Content-Type': 'application/json'})
        t1 = time.time(); d = json.load(urllib.request.urlopen(r, timeout=900)); wall = time.time() - t1
        time.sleep(1.5)
        with open(log_path, encoding='utf-8', errors='replace') as f:
            f.seek(pos); new = f.read(); pos = f.tell()
        print('== wall %.1f s, prompt tokens %s' % (wall, d.get('usage', {}).get('prompt_tokens')), flush=True)
        for line in new.splitlines():
            if line.startswith('strata serve: prompt') or 'helper' in line.lower() or 'prefill timing' in line or 'STRATA_PREFILL_HELPER' in line:
                print('   ', line[:320])
finally:
    p.terminate()
    try: p.wait(30)
    except Exception: p.kill()
    subprocess.run(['taskkill', '/F', '/IM', 'strata.exe'], capture_output=True)
