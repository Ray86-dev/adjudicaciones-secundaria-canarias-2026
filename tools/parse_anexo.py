#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
"""Parser del Anexo I - Adjudicación de destinos provisionales 2026/27 (Secundaria Resto, Canarias).
Extrae cada registro a JSON estructurado + resumen MD + CSV plano."""
import re, json, csv, collections, sys, os

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'anexo_provisional_interinos_secundaria.pdf')
OUTDIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'salida')

RE_DNI = re.compile(r'^\*{3,4}\d{4}\*{1,2}$')
RE_ORDEN = re.compile(r'^\d{1,4}$')
RE_ESPECIALIDAD = re.compile(r'^(\d{3}) - (.+)$')
RE_CATEGORIA = re.compile(r'^(\d{1,3}), (.+)$')
RE_ISLAS = r'(?:GC|TF|LZ|LP|FU|GO|HI)'
RE_AMBITO = re.compile(
    r'^(Regional|Insular|(?:' + RE_ISLAS + r')(?:,' + RE_ISLAS + r')*)\s*$')
RE_AMBITO_PREF = re.compile(
    r'^(Regional|Insular|(?:' + RE_ISLAS + r')(?:,' + RE_ISLAS + r')*)\s*'
    r'Ámbit[eo]\s*Pref\.?:\s*\(?([A-Z]{2}|[^()]+?)\)?\s*$')
RE_DESTINO_PLAIN = re.compile(
    r'^Destino:\s*(\d{8})\s+(.+?)\s+\(([^,]+)\s*,\s*([A-Z]{2})\)\s*-\s*(\d{3})\s*(.*)$')
RE_DESTINO_COLECTIVO = re.compile(
    r'^Destino:\s*Obtuvo por el colectivo (\d+)\s*-\s*(\d{8})\s+(.+?)\s+\(([^,]+)\s*,\s*([A-Z]{2})\)\s*-\s*(\d{3})\s*(.*)$')
RE_CENTRO_SIMPLE = re.compile(
    r'^(\d{8})\s+(.+?)\s+\(([^,]+)\s*,\s*([A-Z]{2})\)\s*-\s*(\d{3})\s*(.*)$')
RE_EXT = re.compile(r'^Ext\. Vig\. Dest\.:\s*(.*)$')
RE_COMISION = re.compile(r'^Tipo comisión:\s*(.*)$')
RE_COMPARTE = re.compile(r'^Comparte con:\s*(.*)$')
RE_ART = re.compile(r'^Art\.\s*(.*)$')
RE_NO_OBTIENE = re.compile(r'^No obtiene(.*)$')
RE_TIPOS_PLAZA = re.compile(r'^Tipos de plaza por las que participa:\s*(.*)$')
RE_OBTUVO = re.compile(r'^Obtuvo por el colectivo (\d+) - (.*)$')

def clean(s):
    return re.sub(r'\s+', ' ', s or '').strip()

def parse_destino(texto):
    """Devuelve dict destino o None. texto ya limpiado."""
    if not texto:
        return None
    d = {'colectivo_origen': None, 'codigo_centro': None, 'centro': None,
         'municipio': None, 'isla': None, 'codigo_especialidad': None,
         'especialidad': None, 'programas': None, 'completo': texto}
    m = RE_DESTINO_COLECTIVO.match(texto)
    if m:
        d['colectivo_origen'] = int(m.group(1))
        d['codigo_centro'], d['centro'] = m.group(2), clean(m.group(3))
        d['municipio'], d['isla'] = clean(m.group(4)), m.group(5)
        d['codigo_especialidad'], resto = m.group(6), clean(m.group(7))
        d['especialidad'], d['programas'] = _split_programas(resto)
        return d
    m = RE_DESTINO_PLAIN.match(texto)
    if m:
        d['codigo_centro'], d['centro'] = m.group(1), clean(m.group(2))
        d['municipio'], d['isla'] = clean(m.group(3)), m.group(4)
        d['codigo_especialidad'], resto = m.group(5), clean(m.group(6))
        d['especialidad'], d['programas'] = _split_programas(resto)
        return d
    m = RE_OBTUVO.match(texto)
    if m:
        d['colectivo_origen'] = int(m.group(1))
        sub = parse_destino(m.group(2))
        if sub:
            for k in ('codigo_centro','centro','municipio','isla','codigo_especialidad','especialidad','programas'):
                d[k] = sub[k]
        return d
    m = RE_CENTRO_SIMPLE.match(texto)
    if m:
        d['codigo_centro'], d['centro'] = m.group(1), clean(m.group(2))
        d['municipio'], d['isla'] = clean(m.group(3)), m.group(4)
        d['codigo_especialidad'], resto = m.group(5), clean(m.group(6))
        d['especialidad'], d['programas'] = _split_programas(resto)
        return d
    return d  # no parseable: solo 'completo'

def _split_programas(resto):
    """Separa especialidad de programas tipo '- Programa Estela' / '- FPB'."""
    resto = clean(resto)
    if not resto:
        return None, None
    # Buscar sufijos '- <Programa>'
    m = re.match(r'^(.+?)\s*-\s*(Programa .+|FPB.*|Enseñanza .+|IFPA.*|IFPM.*|Hoteles .+|Aulas .+|Centros .+|CEPA.*)$', resto)
    if m:
        return clean(m.group(1)), clean(m.group(2))
    return resto, None

def parse_centro_extra(texto):
    """Para Ext. Vig. Dest. y Comparte con: devuelve dict o None."""
    m = RE_CENTRO_SIMPLE.match(clean(texto))
    if m:
        return {'codigo_centro': m.group(1), 'centro': clean(m.group(2)),
                'municipio': clean(m.group(3)), 'isla': m.group(4),
                'codigo_especialidad': m.group(5), 'especialidad': clean(m.group(6))}
    return {'completo': clean(texto)}

def main():
    import fitz
    doc = fitz.open(SRC)
    registros = []
    categoria = especialidad = None
    pagina_actual = 0
    for pno, page in enumerate(doc, 1):
        lineas = [l.rstrip() for l in page.get_text().splitlines()]
        # quitar footer (últimas líneas: num página + Anexo I... + Curso...)
        while lineas and (lineas[-1].startswith('Anexo I') or lineas[-1].startswith('Curso 2026/27') or RE_ORDEN.match(lineas[-1].strip())):
            lineas.pop()
        # cabecera de página: puede repetir categoría/especialidad (misma o nueva sección)
        i = 0
        while i < len(lineas):
            l = lineas[i].strip()
            if RE_CATEGORIA.match(l) and i + 1 < len(lineas) and RE_ESPECIALIDAD.match(lineas[i+1].strip()):
                categoria = clean(l)
                especialidad = clean(lineas[i+1])
                i += 2
                continue
            if l == 'ORDEN' or l == 'DNI/PASAPORTE' or l == 'APELLIDOS Y NOMBRE' or l == 'ÁMBITO' or l == '':
                i += 1
                continue
            break
        # cuerpo: recorrer líneas del registro
        reg = None
        campo_abierto = None  # 'destino'|'ext'|'comparte'|'tipos'|None
        def cerrar():
            nonlocal reg
            if reg:
                registros.append(reg)
            reg = None
        for l in lineas[i:]:
            l = l.rstrip()
            if not l.strip():
                continue
            st = l.strip()
            # nuevo registro: línea ORDEN (cierra el anterior)
            if RE_ORDEN.match(st) and not (RE_AMBITO_PREF.match(st) or RE_AMBITO.match(st)):
                if reg is not None:
                    registros.append(reg)
                reg = {'orden': int(st), 'dni': None, 'nombre': None, 'ambito': None,
                       'ambito_preferente': None, 'categoria': categoria,
                       'especialidad': especialidad, 'destino': None, 'destino_raw': None,
                       'ext_vigencia': None, 'tipo_comision': None, 'comparte_con': [],
                       'articulo': None, 'no_obtiene': False, 'tipos_plaza': None,
                       'pagina': pno}
                campo_abierto = None
                continue
            if reg is None:
                continue
            # DNI
            if RE_DNI.match(st):
                reg['dni'] = st
                campo_abierto = None
                continue
            # ámbito con preferente
            m = RE_AMBITO_PREF.match(st)
            if m:
                reg['ambito'] = m.group(1)
                reg['ambito_preferente'] = clean(m.group(2))
                campo_abierto = None
                continue
            m = RE_AMBITO.match(st)
            if m:
                reg['ambito'] = m.group(1)
                campo_abierto = None
                continue
            # campos etiquetados
            if st.startswith('Destino:'):
                if reg['destino_raw']:
                    reg['destino_raw'] += ' ' + st
                else:
                    reg['destino_raw'] = st
                campo_abierto = 'destino'
                continue
            if st.startswith('Ext. Vig. Dest.:'):
                reg['ext_vigencia'] = (reg['ext_vigencia'] + ' ' if reg['ext_vigencia'] else '') + st
                campo_abierto = 'ext'
                continue
            if st.startswith('Tipo comisión:'):
                reg['tipo_comision'] = st
                campo_abierto = None
                continue
            if st.startswith('Comparte con:'):
                reg['comparte_con'].append(st)
                campo_abierto = 'comparte'
                continue
            if st.startswith('Art.'):
                reg['articulo'] = (reg['articulo'] + ' ' if reg['articulo'] else '') + st
                campo_abierto = None
                continue
            if st.startswith('No obtiene'):
                reg['no_obtiene'] = True
                campo_abierto = None
                continue
            if st.startswith('Tipos de plaza'):
                reg['tipos_plaza'] = (reg['tipos_plaza'] or '') + st
                campo_abierto = 'tipos'
                continue
            if st.startswith('Obtuvo por el colectivo'):
                reg['destino_raw'] = (reg['destino_raw'] + ' ' if reg['destino_raw'] else '') + st
                campo_abierto = 'destino'
                continue
            # continuación de campo abierto (nombre partido o destino partido)
            if campo_abierto == 'destino':
                reg['destino_raw'] += ' ' + st
                continue
            if campo_abierto == 'ext':
                reg['ext_vigencia'] += ' ' + st
                continue
            if campo_abierto == 'comparte':
                reg['comparte_con'][-1] += ' ' + st
                continue
            if campo_abierto == 'tipos':
                reg['tipos_plaza'] += ' ' + st
                continue
            # nombre (1ª o 2ª línea)
            reg['nombre'] = (reg['nombre'] + ' ' if reg['nombre'] else '') + st
        cerrar()
        pagina_actual = pno
    # post-proceso
    for r in registros:
        if r['destino_raw']:
            r['destino'] = parse_destino(clean(r['destino_raw']))
        if r['ext_vigencia']:
            r['ext_vigencia'] = parse_centro_extra(r['ext_vigencia'].replace('Ext. Vig. Dest.:', '', 1))
        if r['comparte_con']:
            r['comparte_con'] = [parse_centro_extra(x.replace('Comparte con:', '', 1)) for x in r['comparte_con']]
        if r['tipos_plaza']:
            r['tipos_plaza'] = [clean(x) for x in r['tipos_plaza'].replace('Tipos de plaza por las que participa:', '', 1).split(',')]
        if r['articulo']:
            r['articulo'] = clean(r['articulo'].replace('Art.', 'Art.', 1))
        r.pop('destino_raw', None)
        r['nombre'] = clean(r['nombre']) if r['nombre'] else None
        # ordenar claves
    # guardar
    import os
    os.makedirs(OUTDIR, exist_ok=True)
    with open(os.path.join(OUTDIR, 'anexo_interinos_2026_27.json'), 'w', encoding='utf-8') as f:
        json.dump(registros, f, ensure_ascii=False, indent=1)
    # CSV plano
    with open(os.path.join(OUTDIR, 'anexo_interinos_2026_27.csv'), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['orden','dni','nombre','ambito','ambito_preferente','categoria','especialidad',
                    'destino_codigo_centro','destino_centro','destino_municipio','destino_isla',
                    'destino_especialidad','colectivo_origen','no_obtiene','tipo_comision','pagina'])
        for r in registros:
            d = r['destino'] or {}
            w.writerow([r['orden'], r['dni'], r['nombre'], r['ambito'], r['ambito_preferente'],
                        r['categoria'], r['especialidad'], d.get('codigo_centro'), d.get('centro'),
                        d.get('municipio'), d.get('isla'), d.get('especialidad'),
                        d.get('colectivo_origen'), r['no_obtiene'], r['tipo_comision'], r['pagina']])
    print('TOTAL REGISTROS:', len(registros))
    print('Con DNI:', sum(1 for r in registros if r['dni']))
    print('Con nombre:', sum(1 for r in registros if r['nombre']))
    print('Con destino parseado:', sum(1 for r in registros if r['destino'] and r['destino'].get('codigo_centro')))
    print('No obtiene:', sum(1 for r in registros if r['no_obtiene']))
    print('Sin destino (ni no_obtiene):', sum(1 for r in registros if not r['destino'] and not r['no_obtiene']))
    print('Destino sin parsear:', sum(1 for r in registros if r['destino'] and not r['destino'].get('codigo_centro')))
    c = collections.Counter(clean(r['categoria']) for r in registros if r['categoria'])
    print('\nPor categoría:')
    for k, v in c.most_common():
        print(f'  {v:5d}  {k}')

if __name__ == '__main__':
    main()
