// Utilidades comunes de los tableros: formato en español (coma decimal),
// tooltip y colores leídos de las variables CSS para respetar el tema.
const nf = (d) => new Intl.NumberFormat("de-DE", { minimumFractionDigits: d, maximumFractionDigits: d });
const num = (v, d = 0) => nf(d).format(v);
const firmado = (v, d = 0) => (v > 0 ? "+" : v < 0 ? "−" : "") + nf(d).format(Math.abs(v));
const usdM = v => {
  const a = Math.abs(v), s = v < 0 ? "−" : "";
  if (a >= 1e9) return s + "$" + nf(a >= 1e10 ? 1 : 2).format(a / 1e9) + " mm";
  if (a >= 1e6) return s + "$" + nf(0).format(a / 1e6) + " M";
  return s + "$" + nf(0).format(a / 1e3) + " mil";
};
const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

const tip = d3.select("body").append("div").attr("class", "tip").attr("hidden", true);
function mostrarTip(e, titulo, filas) {
  tip.attr("hidden", null).html(`<b>${titulo}</b>` + filas.map(f => `<div class="f"><span>${f[0]}</span><span>${f[1]}</span></div>`).join(""));
  const t = tip.node();
  let x = e.clientX + 14, y = e.clientY + 14;
  if (x + t.offsetWidth > innerWidth - 8) x = e.clientX - t.offsetWidth - 14;
  if (y + t.offsetHeight > innerHeight - 8) y = e.clientY - t.offsetHeight - 14;
  tip.style("left", Math.max(4, x) + "px").style("top", Math.max(4, y) + "px");
}
const ocultarTip = () => tip.attr("hidden", true);

// Repinta cuando cambia el tema del sistema o el atributo data-theme.
function alCambiarTema(fn) {
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", fn);
  new MutationObserver(fn).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
}

// Gráficos anchos: en pantallas angostas se dibujan con menos ancho lógico
// para que el texto no quede diminuto al escalar el SVG.
const ancho = (normal = 1000) => innerWidth < 700 ? 560 : normal;
function alRedimensionar(fn) {
  let t, ultimo = ancho();
  addEventListener("resize", () => { clearTimeout(t); t = setTimeout(() => { if (ancho() !== ultimo) { ultimo = ancho(); fn(); } }, 150); });
}

// Botón de reproducción para un deslizador de años.
function reproductor(boton, deslizador, alCambiar) {
  let timer = null;
  const parar = () => { clearInterval(timer); timer = null; boton.text("▶").attr("aria-label", "Reproducir"); };
  boton.on("click", () => {
    if (timer) return parar();
    const n = deslizador.node();
    if (+n.value >= +n.max) n.value = n.min;
    boton.text("❚❚").attr("aria-label", "Pausar");
    timer = setInterval(() => {
      if (+n.value >= +n.max) return parar();
      n.value = +n.value + 1; alCambiar(+n.value);
    }, 700);
  });
  deslizador.on("input", e => { parar(); alCambiar(+e.target.value); });
}
