"""Se ejecuta cada pocos minutos (tarea programada de Windows).
Si BASE_DATOS_KFC.xlsx cambió y lleva >=90 s sin tocarse: regenera la app, la publica y regenera el PDF.
"""
import json, os, subprocess, sys, time, datetime

AQUI = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(os.path.dirname(AQUI), 'BASE_DATOS_KFC.xlsx')
FUENTES = os.path.join(AQUI, 'fuentes')
ESTADO = os.path.join(FUENTES, 'autosync_estado.json')
LOG = os.path.join(FUENTES, 'autosync.log')
LOCK = os.path.join(FUENTES, 'autosync.lock')
GIT = r'C:\Program Files\Git\cmd\git.exe'
PY = sys.executable.replace('pythonw.exe', 'python.exe')
ENV = dict(os.environ)
ENV['PATH'] = r'C:\Program Files\nodejs;' + ENV.get('PATH', '')
ID = ['-c', 'user.name=alejosl0801', '-c', 'user.email=alejosl0801@users.noreply.github.com']
NOWIN = 0x08000000  # CREATE_NO_WINDOW


def log(m):
    with open(LOG, 'a', encoding='utf-8') as f:
        f.write(f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {m}\n")


def run(cmd, timeout=600):
    return subprocess.run(cmd, cwd=AQUI, env=ENV, capture_output=True, text=True, timeout=timeout, creationflags=NOWIN)


def main():
    os.makedirs(FUENTES, exist_ok=True)
    if not os.path.exists(XLSX):
        return
    if os.path.exists(LOCK) and time.time() - os.path.getmtime(LOCK) < 900:
        return
    mt = os.path.getmtime(XLSX)
    ult = json.load(open(ESTADO)).get('mtime') if os.path.exists(ESTADO) else None
    if ult == mt:
        return
    if time.time() - mt < 90:
        return
    open(LOCK, 'w').write(str(os.getpid()))
    try:
        log(f'Excel cambió ({datetime.datetime.fromtimestamp(mt):%H:%M:%S}), actualizando…')
        b = run([PY, 'build.py'])
        if b.returncode != 0:
            log('ERROR build: ' + (b.stderr or b.stdout)[-400:])
            return
        log('build: ' + (b.stdout.strip().splitlines() or [''])[-1])
        st = run([GIT, 'status', '--porcelain'])
        if st.stdout.strip():
            run([GIT, 'add', '-A'])
            c = run([GIT] + ID + ['commit', '-q', '-m', 'Actualización automática desde el Excel'])
            p = run([GIT, 'push', '-q', 'origin', 'main'])
            rem = run([GIT, 'ls-remote', 'origin', 'main']).stdout.split()[:1]
            loc = run([GIT, 'rev-parse', 'HEAD']).stdout.split()[:1]
            if rem != loc:
                log('ERROR push: ' + (p.stderr or '')[-300:])
                return
            log('publicada en GitHub')
        else:
            log('sin cambios en la app')
        g = run([PY, 'generar_pdf.py'], timeout=900)
        log(('PDF: ' + g.stdout.strip()) if g.returncode == 0 else ('ERROR pdf: ' + (g.stderr or g.stdout)[-300:]))
        json.dump({'mtime': mt}, open(ESTADO, 'w'))
        log('listo')
    except Exception as e:
        log('ERROR: ' + repr(e))
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


if __name__ == '__main__':
    main()
