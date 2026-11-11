# Base de Datos KFC · Extintores

App web de una sola página (sin build, sin framework) para consultar el inventario de extintores de todos los locales
del Grupo KFC. **No incluye precios, correos ni datos de personas.**

- `plantilla.html` – la app (HTML + CSS + JS) con el marcador `__DATOS__`.
- `build.py` – lee `../BASE_DATOS_KFC.xlsx` (hoja `DETALLE`) y genera `index.html` con los datos incrustados.
- `index.html` – lo que se publica (generado; no editar a mano).

## Actualizar
Cada vez que cambie el Excel: `python build.py` y luego `git add -A && git commit -m "actualización" && git push`.
