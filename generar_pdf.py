"""Genera LISTADO_EXTINTORES_GRUPO_KFC.pdf (sin precios) desde BASE_DATOS_KFC.xlsx, hoja DETALLE.
Lo deja en Previfuego\\ y en Descargas. Uso: python generar_pdf.py
"""
import os, shutil, subprocess, tempfile
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.worksheet.properties import PageSetupProperties

AQUI = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(AQUI), 'BASE_DATOS_KFC.xlsx')
DESTINOS = [os.path.join(os.path.dirname(AQUI), 'LISTADO_EXTINTORES_GRUPO_KFC.pdf'),
            os.path.join(os.path.expanduser('~'), 'Downloads', 'LISTADO_EXTINTORES_GRUPO_KFC.pdf')]
SOFFICE = r'C:\Program Files\LibreOffice\program\soffice.exe'

wb = openpyxl.load_workbook(SRC)
d = wb['DETALLE']
rows = []
for r in range(2, d.max_row + 1):
    a, b = d.cell(row=r, column=1).value, d.cell(row=r, column=2).value
    tipo = d.cell(row=r, column=5).value
    if not b or not a or str(a).startswith('TOTAL'):
        continue
    if str(tipo or '').startswith('MOVILIZ'):
        continue
    rows.append([d.cell(row=r, column=c).value for c in (1, 2, 3, 4, 5, 6, 9, 10, 11, 12)])

order = sorted(range(len(rows)), key=lambda i: ((0 if rows[i][0] == 'KFC' else 1, rows[i][0], rows[i][1]), i))
rows = [rows[i] for i in order]

out = openpyxl.Workbook()
ws = out.active
ws.title = 'Listado'
HEAD = ['MARCA', 'NOMBRE DEL LOCAL', 'MES DE SERVICIO', 'UBICACIÓN', 'TIPO', 'CAPACIDAD',
        'AÑO ÚLTIMA RECARGA', 'AÑO MANTENIMIENTO 1', 'AÑO MANTENIMIENTO 2', 'AÑO PRÓXIMA RECARGA']
thin = Side(style='thin', color='FFBFBFBF')
B = Border(left=thin, right=thin, top=thin, bottom=thin)
hdr_fill = PatternFill('solid', fgColor='FF922B21')
zeb = PatternFill('solid', fgColor='FFF4F8FB')
for c, h in enumerate(HEAD, 1):
    x = ws.cell(row=1, column=c, value=h)
    x.fill = hdr_fill; x.border = B
    x.font = Font(name='Calibri', size=10, bold=True, color='FFFFFFFF')
    x.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
ws.row_dimensions[1].height = 40
blk = -1; prev = None
for i, row in enumerate(rows, start=2):
    if row[1] != prev:
        blk += 1; prev = row[1]
    for c, v in enumerate(row, 1):
        x = ws.cell(row=i, column=c, value=v)
        x.border = B
        x.font = Font(name='Calibri', size=9)
        x.alignment = Alignment(horizontal='left' if c in (1, 2, 4) else 'center', vertical='center')
        if blk % 2 == 0:
            x.fill = zeb
    ws.row_dimensions[i].height = 15
for col, w in zip('ABCDEFGHIJ', (24, 44, 15, 34, 9, 12, 14, 17, 17, 14)):
    ws.column_dimensions[col].width = w
ws.freeze_panes = 'A2'
ws.print_title_rows = '1:1'
ws.page_setup.orientation = 'landscape'
ws.page_setup.paperSize = ws.PAPERSIZE_A4
ws.page_setup.fitToWidth = 1
ws.page_setup.fitToHeight = 0
ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
ws.page_margins.left = ws.page_margins.right = 0.4
ws.page_margins.top = 0.9; ws.page_margins.bottom = 0.7; ws.page_margins.header = 0.4; ws.page_margins.footer = 0.3
ws.oddHeader.center.text = 'Listado de extintores por local - Grupo KFC'
ws.oddHeader.center.size = 10
ws.oddFooter.center.text = 'Página &P de &N'
ws.oddFooter.center.size = 8

tmp = tempfile.mkdtemp(prefix='kfcpdf_')
xl = os.path.join(tmp, 'LISTADO_EXTINTORES_GRUPO_KFC.xlsx')
out.save(xl)
subprocess.run([SOFFICE, '--headless', '--convert-to', 'pdf', '--outdir', tmp, xl], capture_output=True, check=True, timeout=300)
pdf = os.path.join(tmp, 'LISTADO_EXTINTORES_GRUPO_KFC.pdf')
if not os.path.exists(pdf) or os.path.getsize(pdf) < 10000:
    raise SystemExit('PDF no generado')
for dst in DESTINOS:
    try:
        shutil.copyfile(pdf, dst)
    except Exception as e:
        print('No se pudo copiar a', dst, e)
shutil.rmtree(tmp, ignore_errors=True)
print('PDF listo:', len(rows), 'filas,', len({r[1] for r in rows}), 'locales')
