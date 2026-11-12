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
    lst, h1, tel_por_correo = {}, {}, {}
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
        for row in lw['TD VAL RES'].iter_rows(min_row=3, values_only=True):
            if row[4] and row[5]:
                tel_por_correo.setdefault(str(row[4]).strip().lower(), str(row[5]).strip())
    for f in filas:
        nombre, codigo = f[2], f[1]
        lid = codigo if codigo != 'PENDIENTE' else nombre
        if lid in out:
            continue
        k = kcode(codigo)
        rec = {}
        if nombre in correo_local:
            rec['c'] = correo_local[nombre]
        row = lst.get(k)
        hr = h1.get(k)
        if k in gerentes and (gerentes[k][0] or gerentes[k][1]):
            n, e = gerentes[k]
            rec['g'] = {'n': n, 'e': e}
        else:
            ja = tit((hr[7] if hr else None) or (row[20] if row else None))
            if ja:
                rec['g'] = {'n': ja, 'e': ''}
        if row and str(row[11] or '').strip():
            rec['tl'] = str(row[11]).strip()
        if row:
            if row[6]:
                rec['rg'] = tit(row[6])
            if row[7]:
                rec['z'] = str(row[7]).strip()
        if rec:
            out[lid] = rec
    return out




import unicodedata


def _n(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s).upper()) if unicodedata.category(c) != 'Mn')


REGLAS = [
    ('GRAN PIAZZA', 'Machala · Gran Piazza'), ('MACHALA', 'Machala'),
    ('SALINAS', 'Salinas / Santa Elena'), ('SANTA ELENA', 'Salinas / Santa Elena'), ('PENINSULA', 'Salinas / Santa Elena'),
    ('PLAYAS', 'Playas'), ('VINCES', 'Vinces'), ('VENTANAS', 'Ventanas'), ('BABAHOYO', 'Babahoyo'),
    ('QUEVEDO', 'Quevedo'), ('MILAGRO', 'Milagro'), ('SAMBORONDON', 'Samborondón'),
    ('VIA DAULE', 'Guayaquil · Vía a Daule'), ('KM 9', 'Guayaquil · Vía a Daule'),
    ('PLAZA PACIFICO DAULE', 'Daule'), ('SHOPPING DAULE', 'Daule'), ('DAULE', 'Daule'),
    ('VIA A LA COSTA', 'Guayaquil · Vía a la Costa'),
    ('EL DORADO', 'Guayaquil · Riocentro El Dorado'), ('DORADO', 'Guayaquil · Riocentro El Dorado'),
    ('RIO CENTRO NORTE', 'Guayaquil · Riocentro Norte'), ('RIOCENTRO NORTE', 'Guayaquil · Riocentro Norte'),
    ('RIO CENTRO SUR', 'Guayaquil · Riocentro Sur'), ('RIOCENTRO SUR', 'Guayaquil · Riocentro Sur'),
    ('CEIBOS', 'Guayaquil · Ceibos'),
    ('MALL DEL SOL', 'Guayaquil · Mall del Sol'), ('MALL EL SOL', 'Guayaquil · Mall del Sol'),
    ('MALL DEL SUR', 'Guayaquil · Mall del Sur'), ('CITY MALL', 'Guayaquil · City Mall'),
    ('SAN MARINO', 'Guayaquil · San Marino'), ('POLICENTRO', 'Guayaquil · Policentro'),
    ('ALBORADA', 'Guayaquil · Alborada'), ('BUIJO', 'Guayaquil · Buijo / Ciudad Celeste'),
    ('AEROPUERTO', 'Guayaquil · Aeropuerto'), ('PREEMB', 'Guayaquil · Aeropuerto'), ('ISLA EXP', 'Guayaquil · Aeropuerto'),
    ('CAFE ASTORIA', 'Guayaquil · Aeropuerto'), ('INTERNACIONAL', 'Guayaquil · Aeropuerto'),
    ('TERMINAL', 'Guayaquil · Terminal Terrestre'), ('PUNTILLA', 'Guayaquil · Puntilla'),
    ('MALECON', 'Guayaquil · Malecón 2000'), ('MALL DEL RIO', 'Guayaquil · Mall del Río'),
    ('MALL SUR', 'Guayaquil · Mall del Sur'), ('MALL DEL NORTE', 'Guayaquil · Mall del Norte'),
    ('URDESA', 'Guayaquil · Urdesa'), ('KENNEDY', 'Guayaquil · Kennedy'), ('FORTIN', 'Guayaquil · El Fortín'),
    ('PORTETE', 'Guayaquil · Portete'), ('DOMINGO COMIN', 'Guayaquil · Domingo Comín'), ('9 DE OCTUBRE', 'Guayaquil · Centro'),
    ('BOYACA', 'Guayaquil · Centro'), ('CENTENARIO', 'Guayaquil · Centro'),
    ('PENAS', 'Guayaquil · Las Peñas'), ('VILLAGE', 'Guayaquil · Village Plaza'),
    ('DURAN', 'Durán'),
]


def sector(nombre, region):
    t = _n(nombre)
    for k, v in REGLAS:
        if k in t:
            return v
    r = _n(region or '')
    if not r or r.startswith('GUAYAQUIL'):
        return 'Guayaquil · Otros' if r else 'Otros'
    return re.sub(r'\s*\(.*\)', '', region).title()


sec = {}
_lst = {}
if os.path.exists(LISTADO):
    _lw = openpyxl.load_workbook(LISTADO, data_only=True)
    for _row in _lw['LOCALES GKFC 2022'].iter_rows(min_row=2, values_only=True):
        _k = kcode(_row[1])
        if _k and _row[6]:
            _lst[_k] = _row[6]
for _f in filas:
    sec[_f[2]] = sector(_f[2], _lst.get(kcode(_f[1])))

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
abiertos = bool(cfg.pop('contactos_abiertos', False))
if abiertos:
    cc = ''

mtime = datetime.datetime.fromtimestamp(os.path.getmtime(XLSX))
datos = {'actualizado': mtime.strftime('%d/%m/%Y %H:%M'), 'acc': acc, 'sec': sec, 'cfg': cfg, 'extintores': filas}
if abiertos:
    datos['cont'] = cont
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
open(os.path.join(AQUI, 'v.txt'), 'w').write(str(ver['n']))
print('Version', ver['n'], '| OK', len(filas), 'extintores,', len({f[2] for f in filas}), 'locales ->', SALIDA)
