# Adjudicaciones Secundaria Canarias 2026/27

> **In English:** Search for 31,828 provisional teaching posts in the Canary Islands (2026/27), extracted from the official PDF with Python. One JSON file and plain JavaScript: it runs entirely in the browser, with no server. [Live site](https://ray86-dev.github.io/adjudicaciones-secundaria-canarias-2026/).

Buscador web de la **adjudicación de destinos provisionales** del curso 2026/27 para el cuerpo de **Secundaria Resto** en Canarias (Anexo I de la resolución de la Consejería de Educación del Gobierno de Canarias).

Web: <https://ray86-dev.github.io/adjudicaciones-secundaria-canarias-2026/>

## Qué incluye

- **31.828 registros** de adjudicación de destinos, con los datos de cada persona:
  - Nombre y DNI (enmascarado)
  - Categoría (lista de empleo, interino por necesidades, salud, PROMECI, funcionarios en prácticas, etc.)
  - Especialidad (110 especialidades de Secundaria, E.O.I. y enseñanzas artísticas)
  - Destino asignado: centro, municipio e isla, con código de centro
  - Extras: extensión de vigencia, comisión, destinos compartidos, tipos de plaza por los que participa, programas (AICLE, Estela, BACHIBAC…), artículos aplicados
- **Búsqueda** instantánea por nombre, DNI, centro, municipio o especialidad (sin tildes, insensible a mayúsculas)
- **Filtros** por especialidad, isla, categoría, solo con destino y solo sin vacante
- **Paginación** de 50 resultados
- Funciona 100 % en el navegador, sin servidor: un único JSON de datos y JavaScript plano (sin frameworks)

## Estructura

```
├── index.html          # Página principal
├── app.js              # Lógica de búsqueda, filtros y render
├── styles.css          # Estilos
├── data/
│   └── registros.json  # Datos extraídos (22 MB)
└── tools/
    └── parse_anexo.py  # Parser del PDF original → JSON completo
```

## Reproducir la extracción

El dataset proviene de `anexo_provisional_interinos_secundaria.pdf` (2.879 páginas), publicado por la Consejería de Educación.

1. Descarga el PDF del Anexo I (adjudicación de destinos provisionales, Secundaria Resto, curso 2026/27).
2. Ejecuta el parser (requiere `pymupdf`):

   ```bash
   pip install pymupdf
   python tools/parse_anexo.py
   ```

   Genera `anexo_interinos_2026_27.json` (registros completos), `.csv` y un resumen `.md`.
3. Genera el JSON optimizado para la web:

   ```bash
   python tools/build_web_data.py
   ```

   Escribe `data/registros.json`, el que consume la web.

## Aviso legal

Los datos provienen de una resolución administrativa pública y se ofrecen **con carácter orientativo**. Para cualquier trámite o recurso, consulte siempre la resolución oficial publicada por la Consejería de Educación del Gobierno de Canarias. Los DNIs aparecen enmascarados en la fuente original.

## Licencia

Los datos proceden de una fuente pública (Gobierno de Canarias). El código de este repositorio se distribuye bajo licencia MIT.
