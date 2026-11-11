"""Genera index.html (app Base de Datos KFC) a partir de BASE_DATOS_KFC.xlsx, hoja DETALLE.
Sin precios, sin correos y sin datos de personas. Uso: python build.py
"""
import json, os, re, datetime, sys
import openpyxl

AQUI = os.path.dirname(os.path.abspath(__file__))
XLSX = os.path.join(os.path.dirname(AQUI), 'BASE_DATOS_KFC.xlsx')
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

filas_orden = sorted(range(len(filas)), key=lambda i: (0 if filas[i][0] == 'KFC' else 1, filas[i][0], filas[i][2], i))
filas = [filas[i] for i in filas_orden]

rs = wb['RESUMEN_LOCALES']
acc = {}
for r in range(2, rs.max_row + 1):
    nom = rs.cell(row=r, column=3).value
    if nom:
        v = str(rs.cell(row=r, column=14).value or '?').strip().upper().replace('Í', 'I')
        acc[str(nom)] = v if v in ('SI', 'NO') else '?'

mtime = datetime.datetime.fromtimestamp(os.path.getmtime(XLSX))
datos = {'actualizado': mtime.strftime('%d/%m/%Y %H:%M'), 'acc': acc, 'extintores': filas}
js = json.dumps(datos, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')

html = open(PLANTILLA, encoding='utf-8').read().replace('__DATOS__', js)
open(SALIDA, 'w', encoding='utf-8').write(html)
print('OK', len(filas), 'extintores,', len({f[2] for f in filas}), 'locales ->', SALIDA)
