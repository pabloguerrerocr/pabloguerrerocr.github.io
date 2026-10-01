"""Arma los tableros interactivos del sitio a partir de los repositorios.

    python tableros/construir.py

Baja los CSV publicados en cada repositorio (rama main), los reduce a lo que
cada tablero necesita y los incrusta en una página autocontenida:

    nowcast/index.html   portfolio-data-analytics  (nowcasting-pib)
    comercio/index.html  comercio-exterior-cr
    brecha/index.html    brecha-espejo-cr
    atlas/index.html     portfolio-data-analytics  (poblacion-mundial/web)

Con FUENTE_LOCAL=/ruta/a/los/clones lee de copias locales en vez de GitHub.
Un flujo de GitHub Actions lo corre cada mes, así los tableros siguen a los
datos sin que nadie copie nada a mano.
"""

import io
import json
import os
from pathlib import Path

import pandas as pd
import requests

RAIZ = Path(__file__).resolve().parent.parent
PLANTILLAS = RAIZ / "tableros" / "plantillas"
USUARIO = "pabloguerrerocr"


def fuente(repo, ruta):
    local = os.environ.get("FUENTE_LOCAL")
    if local:
        return (Path(local) / repo / ruta).read_bytes()
    url = f"https://raw.githubusercontent.com/{USUARIO}/{repo}/main/{ruta}"
    r = requests.get(url, timeout=60)
    r.raise_for_status()
    return r.content


def csv(repo, ruta):
    return pd.read_csv(io.BytesIO(fuente(repo, ruta)))


def escribir(nombre, datos):
    html = (PLANTILLAS / f"{nombre}.html").read_text(encoding="utf-8")
    html = html.replace("/*COMUN_CSS*/", (PLANTILLAS / "comun.css").read_text(encoding="utf-8"))
    html = html.replace("/*COMUN_JS*/", (PLANTILLAS / "comun.js").read_text(encoding="utf-8"))
    html = html.replace("/*DATOS*/null", json.dumps(datos, separators=(",", ":"), ensure_ascii=False))
    destino = RAIZ / nombre / "index.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    print(f"{nombre}/index.html  {len(html) / 1024:.0f} KB")


# ------------------------------------------------------------------ nowcast
def nowcast():
    n = csv("portfolio-data-analytics", "nowcasting-pib/resultados_nowcast.csv")
    columnas = ["trimestre", "observado", "nowcast", "ingenuo", "promedio"]
    escribir("nowcast", n[columnas].round(3).values.tolist())


# ------------------------------------------------------------------ comercio
CAPITULOS_ES = {
    7: "Hortalizas", 8: "Frutas", 9: "Café, té y especias", 10: "Cereales",
    15: "Grasas y aceites", 20: "Preparaciones de frutas y hortalizas",
    21: "Preparaciones alimenticias diversas", 27: "Combustibles",
    30: "Productos farmacéuticos", 39: "Plásticos", 40: "Caucho",
    48: "Papel y cartón", 72: "Hierro y acero", 73: "Manufacturas de hierro o acero",
    84: "Maquinaria y reactores", 85: "Máquinas y aparatos eléctricos",
    87: "Vehículos", 90: "Instrumentos médicos y de precisión",
    96: "Manufacturas diversas", 99: "Mercancías no especificadas",
}
SOCIOS_ES = {
    "USA": "Estados Unidos", "Belgium": "Bélgica", "Brazil": "Brasil", "Canada": "Canadá",
    "China, Hong Kong SAR": "Hong Kong", "Dominican Rep.": "Rep. Dominicana",
    "Germany": "Alemania", "Italy": "Italia", "Japan": "Japón", "Malaysia": "Malasia",
    "Mexico": "México", "Netherlands": "Países Bajos", "Panama": "Panamá",
    "Rep. of Korea": "Corea del Sur", "Spain": "España", "Trinidad and Tobago": "Trinidad y Tobago",
    "United Kingdom": "Reino Unido", "Areas, nes": "Áreas no especificadas",
    "Switzerland": "Suiza", "France": "Francia", "Ireland": "Irlanda", "India": "India",
    "Other Asia, nes": "Otros de Asia, n.e.p.", "Czechia": "Chequia", "Poland": "Polonia",
    "Singapore": "Singapur", "Philippines": "Filipinas", "Peru": "Perú", "Viet Nam": "Vietnam",
}


def comercio():
    repo = "comercio-exterior-cr"
    socios = csv(repo, "datos/comercio_por_socio.csv")
    socios = socios[~socios["es_agregado"] & (socios["valor_usd"] > 0)]
    productos = csv(repo, "datos/comercio_por_producto.csv")
    balanza = csv(repo, "datos/hallazgo_balanza.csv")
    conc = csv(repo, "datos/hallazgo_concentracion.csv")
    aporte = csv(repo, "datos/hallazgo_capitulos.csv")

    def top(df, clave, nombre, n=12):
        """Los n mayores por año y flujo, más un 'Resto' que conserva el total."""
        filas = []
        for (anio, flujo), g in df.groupby(["anio", "flujo"]):
            g = g.sort_values("valor_usd", ascending=False)
            for _, f in g.head(n).iterrows():
                filas.append([int(anio), flujo[:3], nombre(f), round(f["valor_usd"])])
            resto = g["valor_usd"].iloc[n:].sum()
            if resto > 0:
                filas.append([int(anio), flujo[:3], "Resto", round(resto)])
        return filas

    datos = {
        "balanza": balanza.round(3).values.tolist(),
        "conc": conc[["anio", "hhi", "top1_pc", "top4_pc", "top10_pc"]].values.tolist(),
        "socios": top(socios, "socio", lambda f: SOCIOS_ES.get(f["socio"], f["socio"])),
        "capitulos": top(productos, "cap_cod", lambda f: CAPITULOS_ES.get(int(f["cap_cod"]), f["capitulo"].split(";")[0])),
        "aporte": [[CAPITULOS_ES.get(int(f["cap_cod"]), f["capitulo"].split(";")[0]), round(f["cambio"]), f["aporte_pc"]]
                   for _, f in aporte.iterrows()],
    }
    escribir("comercio", datos)


# ------------------------------------------------------------------ brecha
def brecha():
    e = csv("brecha-espejo-cr", "datos/espejo.csv")
    # Misma definición que 02_analisis.sql: solo países, sin el mundo ni agregados.
    p = e[(e["socio_cod"] != 0) & ~e["es_agregado"] & (e["valor_usd"] > 0)]
    par = p.pivot_table(index=["anio", "socio"], columns="lado", values="valor_usd", aggfunc="sum").reset_index()
    par["socio"] = par["socio"].map(lambda s: SOCIOS_ES.get(s, s))
    filas = [[int(f["anio"]), f["socio"],
              None if pd.isna(f["declara_CR"]) else round(f["declara_CR"]),
              None if pd.isna(f["declara_socio"]) else round(f["declara_socio"])]
             for _, f in par.iterrows()]
    escribir("brecha", filas)


# ------------------------------------------------------------------ atlas
def atlas():
    html = fuente("portfolio-data-analytics", "poblacion-mundial/web/index.html").decode("utf-8")
    # La página del atlas se publica como fragmento (sin <!doctype>/<head>):
    # aquí se envuelve como documento completo para servirla tal cual.
    cuerpo = html
    titulo = cuerpo[cuerpo.index("<title>"):cuerpo.index("</title>") + 8]
    cuerpo = cuerpo.replace(titulo, "", 1)
    doc = ("<!doctype html>\n<html lang=\"es\">\n<head>\n<meta charset=\"utf-8\">\n"
           "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1, viewport-fit=cover\">\n"
           f"{titulo}\n</head>\n<body>\n"
           "<p style=\"max-width:1280px;margin:16px auto 0;padding:0 20px;font:12px 'JetBrains Mono',monospace\">"
           "<a href=\"../\" style=\"color:inherit\">← Pablo Guerrero</a></p>\n"
           f"{cuerpo}\n</body>\n</html>\n")
    destino = RAIZ / "atlas" / "index.html"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(doc, encoding="utf-8")
    print(f"atlas/index.html  {len(doc) / 1024:.0f} KB")


if __name__ == "__main__":
    nowcast()
    comercio()
    brecha()
    try:
        atlas()
    except (requests.HTTPError, FileNotFoundError) as e:
        # El atlas vive en otro repositorio; si todavía no está publicado en
        # main, se conserva la copia actual en vez de romper los demás.
        print(f"atlas: se conserva la copia actual ({e})")
