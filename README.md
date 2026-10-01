# pabloguerrerocr.github.io

Página personal de presentación profesional. Una sola página, sin dependencias
ni build: `index.html` se sirve tal cual.

Para editarla, se toca `index.html` y se hace push a `main`. GitHub Pages
republica solo en menos de un minuto.

Los datos que aparecen son públicos y verificables; cada hallazgo enlaza al
repositorio que lo produce.

## Tableros interactivos

`atlas/`, `brecha/`, `comercio/` y `nowcast/` son tableros autocontenidos (D3,
sin build en el navegador). Los arma `tableros/construir.py` a partir de los CSV
publicados en cada repositorio, con las plantillas de `tableros/plantillas/`.
El flujo `Tableros` de GitHub Actions los rearma el día 6 de cada mes, así siguen
a los datos sin copiar nada a mano.

```bash
pip install pandas requests
python tableros/construir.py                       # baja de GitHub
FUENTE_LOCAL=.. python tableros/construir.py       # o de clones locales
```
