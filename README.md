# Capitán de Yate · Test de teoría (PWA offline)

App móvil de tipo test para memorizar las preguntas de teoría del examen de
**Capitán de Yate** con los exámenes oficiales de la **Región de Murcia (CARM)
de 2018 a 2026**. Funciona 100 % sin conexión una vez cargada (PWA instalable).

## Banco de preguntas

- **23 exámenes** (2018-03 … 2026-03) descargados del
  [histórico oficial de la CARM](https://www.carm.es/web/pagina?IDCONTENIDO=74737&IDTIPO=100&RASTRO=c394%24m8859%2C12137%2C9503).
- **690 preguntas** = 23 exámenes × 30 preguntas de teoría:
  - 1–10 · Teoría de Navegación
  - 21–30 · Meteorología
  - 31–40 · Inglés
- Las preguntas **11–20 (cálculos de navegación) se excluyen** por diseño.
- La respuesta correcta viene **subrayada** en los PDF oficiales ("con
  respuestas"); el extractor detecta el subrayado (gráfico del PDF) y lo casa
  por posición con el texto.

## Estructura

```
index.html, styles.css, app.js   # app (vanilla JS, sin build)
data.js                          # banco de preguntas embebido (generado)
sw.js, manifest.webmanifest      # PWA: precache cache-first + instalable
icons/                           # iconos generados
data/pdfs/                       # exámenes originales descargados
data/questions.json              # base de datos canónica
data/extraction_report.txt       # informe de extracción
scripts/extract_questions.py     # PDF -> questions.json (requiere pymupdf)
scripts/validate_db.py           # validación de la base de datos
scripts/build_data.py            # questions.json -> data.js
scripts/build_icons.py           # genera iconos (requiere pillow)
```

## Uso

La app es estática; cualquier servidor vale (el service worker requiere HTTPS
o localhost):

```bash
python3 -m http.server 8000
```

Abrir `http://localhost:8000`, o publicar la carpeta en GitHub Pages / Netlify
y en el móvil usar "Añadir a pantalla de inicio". Tras la primera carga
funciona sin internet.

## Regenerar la base de datos

```bash
pip install pymupdf pillow
python3 scripts/extract_questions.py   # extrae de data/pdfs/ -> data/questions.json
python3 scripts/validate_db.py         # valida (sale con error si algo falla)
python3 scripts/build_data.py          # genera data.js para la app
```

Para añadir un examen nuevo: descargar el PDF "con respuestas" del histórico
de la CARM como `data/pdfs/cy-AAAA-MM.pdf` y ejecutar los tres pasos. Al
publicar cambios, incrementar `CACHE_VERSION` en `sw.js` para que los clientes
instalados se actualicen.

## Validación

`validate_db.py` comprueba: 30 preguntas por examen (10 por módulo), 4
opciones y exactamente 1 correcta por pregunta, exclusión de las 11–20,
coherencia número↔módulo y artefactos de extracción. Estado actual:
**0 errores**. Además se verificaron 24 respuestas a mano contra los PDF
renderizados (24/24 coinciden).

## Notas

- Las opciones **no se barajan** dentro de cada pregunta porque muchas se
  referencian entre sí ("a) y b) son correctas"); se baraja el orden de las
  preguntas.
- Las preguntas falladas se guardan en `localStorage` y se pueden repasar
  desde la pantalla de inicio ("Repasar falladas").
- 2020 solo tiene una convocatoria de CY (julio); la de octubre fue solo PER
  por COVID. La convocatoria de junio 2026 aún no estaba publicada.
