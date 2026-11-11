"""Genera index.html (app Base de Datos KFC) a partir de BASE_DATOS_KFC.xlsx.
- Inventario (hoja DETALLE): sin precios, a la vista.
- Contactos (correo, gerente, responsable, celular): se cifran con fuentes/clave.txt y solo se abren con esa clave.
Uso: python build.py
"""
import json, os, re, datetime, subprocess, hashlib
import openpyxl

AQUI = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(os.path.dirname(AQUI), 'BASE_DATOS_KFC.xlsx')
LISTADO = os.path.join(AQUI, 'fuentes', 'LISTADO_DE_LOCALES.xlsx')
CLAVE = os.path.join(AQUI, 'fuentes', 'clave.txt')
PLANTILLA = os.path.join(AQUI, 'plantilla.html')
SALIDA = os.path.join(AQUI, 'index.html')

wb = openpyxl.load_workbook(XLSX, data_only=False)
d = wb['DETALLE']
filas = []
for r in range(2, d.max_row + 1):
    a, b, tipo = (d.cell(row=r, column=c).value for c in (1, 2, 5))
    if not a or not b or str(a).startswith('TOTAL'):
        continue
    if str(tipo or '').startswith('MOVILIZ'):
        continue
    g = lambda c: d.cell(row=r, column=c).value
    m = re.match(r'^([A-Z]{1,3}\d{1,3})\s*-', str(b))
    codigo = m.group(1) if m else 'PENDIENTE'
    filas.append([str(a), codigo, str(b), str(g(3)), str(g(4) or ''), str(g(5)), str(g(6)),
                  int(g(9)), int(g(10)), int(g(11)), int(g(12))])

orden = sorted(range(len(filas)), key=lambda i: (0 if filas[i][0] == 'KFC' else 1, filas[i][0], filas[i][2], i))
filas = [filas[i] for i in orden]

rs = wb['RESUMEN_LOCALES']
acc, correo_local = {}, {}
for r in range(2, rs.max_row + 1):
    nom = rs.cell(row=r, column=3).value
    if nom:
        v = str(rs.cell(row=r, column=14).value or '?').strip().upper().replace('Í', 'I')
        acc[str(nom)] = v if v in ('SI', 'NO') else '?'
        co = str(rs.cell(row=r, column=12).value or '').strip()
        if co and co.upper() != 'PENDIENTE':
            correo_local[str(nom)] = co


def kcode(code):
    m = re.match(r'^([A-Z]+)0*(\d+)', str(code or '').upper().strip())
    return (m.group(1), int(m.group(2))) if m else None


def tit(s):
    s = str(s or '').strip()
    return s.title() if s and (s.isupper() or s.islower()) else s


def contactos():
    """id de local -> datos de contacto (se cifran)."""
    out = {}
    gerentes = {}
    gs = wb['GERENTES_OPERACIONES']
    for r in range(8, gs.max_row + 1):
        k = kcode(gs.cell(row=r, column=1).value)
        if k:
            gerentes[k] = (tit(gs.cell(row=r, column=2).value), str(gs.cell(row=r, column=3).value or '').strip())
    lst, h1 = {}, {}
    if os.path.exists(LISTADO):
        lw = openpyxl.load_workbook(LISTADO, data_only=True)
        for row in lw['LOCALES GKFC 2022'].iter_rows(min_row=2, values_only=True):
            k = kcode(row[1])
            if not k:
                continue
            abierto = str(row[13] or '').strip().upper() == 'ABIERTO'
            if k not in lst or abierto:
                lst[k] = row
        for row in lw['Hoja1'].iter_rows(min_row=2, values_only=True):
            k = kcode(row[0])
            if k:
                h1[k] = row
    for f in filas:
        nombre, codigo = f[2], f[1]
        lid = codigo if codigo != 'PENDIENTE' else nombre
        if lid in out:
            continue
        k = kcode(codigo)
        rec = {}
        if nombre in correo_local:
            rec['c'] = correo_local[nombre]
        if k in gerentes and (gerentes[k][0] or gerentes[k][1]):
            rec['g'] = {'n': gerentes[k][0], 'e': gerentes[k][1]}
        row = lst.get(k)
        if row:
            if row[9] or row[10] or row[11]:
                rec['r'] = {'n': tit(row[9]), 'e': str(row[10] or '').strip(), 't': str(row[11] or '').strip()}
            if row[6]:
                rec['rg'] = tit(row[6])
            if row[7]:
                rec['z'] = str(row[7]).strip()
        hr = h1.get(k)
        ja = tit((hr[7] if hr else None) or (row[20] if row else None))
        go = tit((hr[8] if hr else None) or (row[21] if row else None))
        if ja:
            rec['ja'] = ja
        if go:
            rec['go'] = go
        if rec:
            out[lid] = rec
    return out


cc = ''
cont = {}
if os.path.exists(CLAVE):
    tmp = os.path.join(AQUI, 'fuentes', '_contactos.json')
    cont = contactos()
    json.dump(cont, open(tmp, 'w', encoding='utf-8'), ensure_ascii=False)
    cc = subprocess.run(['node', os.path.join(AQUI, 'cifrar.js'), tmp, CLAVE], capture_output=True, text=True, check=True).stdout.strip()
    os.remove(tmp)
    print('Contactos cifrados:', len(cont), 'locales')

cfg_path = os.path.join(AQUI, 'config.json')
cfg = json.load(open(cfg_path)) if os.path.exists(cfg_path) else {'obs_url': '', 'app_key': ''}

mtime = datetime.datetime.fromtimestamp(os.path.getmtime(XLSX))
datos = {'actualizado': mtime.strftime('%d/%m/%Y %H:%M'), 'acc': acc, 'cfg': cfg, 'extintores': filas}
js = json.dumps(datos, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

plantilla = open(PLANTILLA, encoding='utf-8').read()
vf = os.path.join(AQUI, 'version.json')
ver = json.load(open(vf)) if os.path.exists(vf) else {'n': 0, 'hash': ''}
# el cifrado usa sal/iv aleatorios; la version se calcula con el contenido sin cifrar
h = hashlib.sha256((plantilla + js + json.dumps(cont, sort_keys=True, ensure_ascii=False)).encode('utf-8')).hexdigest()
if h != ver['hash']:
    ver = {'n': ver['n'] + 1, 'hash': h, 'fecha': datetime.datetime.now().strftime('%d/%m/%Y %H:%M')}
    json.dump(ver, open(vf, 'w'))
html = (plantilla.replace('__DATOS__', js).replace('__CIFRADO__', cc)
        .replace('__VERSION__', str(ver['n'])).replace('__FECHAV__', ver.get('fecha', '')))
open(SALIDA, 'w', encoding='utf-8').write(html)
print('Version', ver['n'], '| OK', len(filas), 'extintores,', len({f[2] for f in filas}), 'locales ->', SALIDA)
