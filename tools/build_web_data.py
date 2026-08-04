#!/usr/bin/env python3.14
# -*- coding: utf-8 -*-
"""Genera data/registros.json (compacto, optimizado para web) a partir del JSON completo."""
import json, re, os, unicodedata

SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'salida', 'anexo_interinos_2026_27.json')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'registros.json')

def norm(s):
    if not s:
        return ''
    s = unicodedata.normalize('NFD', str(s))
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return re.sub(r'\s+', ' ', s).strip().lower()

def main():
    regs = json.load(open(SRC, encoding='utf-8'))
    web = []
    for r in regs:
        d = r.get('destino') or {}
        d.pop('completo', None)
        partes = [r.get('nombre'), r.get('dni'), d.get('centro'), d.get('municipio'),
                  d.get('especialidad'), d.get('isla'), r.get('categoria'),
                  r.get('especialidad'), r.get('ambito'), r.get('ambito_preferente'),
                  r.get('tipo_comision'), r.get('articulo')]
        if r.get('tipos_plaza'):
            partes += r['tipos_plaza']
        w = {
            'orden': r['orden'],
            'dni': r['dni'],
            'nombre': r['nombre'],
            'ambito': r['ambito'],
            'ambito_preferente': r['ambito_preferente'],
            'categoria': r['categoria'],
            'especialidad': r['especialidad'],
            'destino': d,
            'ext_vigencia': r.get('ext_vigencia'),
            'tipo_comision': r.get('tipo_comision'),
            'comparte_con': r.get('comparte_con') or [],
            'articulo': r.get('articulo'),
            'no_obtiene': bool(r.get('no_obtiene')),
            'tipos_plaza': r.get('tipos_plaza'),
            'pagina': r['pagina'],
            '_q': norm(' '.join(p for p in partes if p)),
        }
        web.append(w)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        json.dump(web, f, ensure_ascii=False, separators=(',', ':'))
    print('registros web:', len(web))
    print('tamaño:', round(os.path.getsize(OUT) / 1024 / 1024, 2), 'MB')

if __name__ == '__main__':
    main()
