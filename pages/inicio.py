# -*- coding: utf-8 -*-
"""
Capa 1 — Mapa interactivo del Gran Santiago.

Muestra las 1.636 zonas censales coloreadas por su clasificación ZFD, la red
pública (hospitales y CESFAM) y una capa de comunas que despliega indicadores
agregados al pasar el cursor por encima.
"""
import os

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

COLORES = {
    "ZFD-A": "#E2434A",
    "ZFD-B": "#F27186",
    "LL":    "#2F6FA8",
    "Resto": "#1E293B",
}
OPACIDAD = {"ZFD-A": 0.90, "ZFD-B": 0.84, "LL": 0.50, "Resto": 0.30}

COLOR_HOSPITAL = "#FFC24B"
COLOR_CESFAM   = "#3FD07E"

TILES_URL  = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
TILES_ATTR = "Esri, HERE, Garmin, &copy; OpenStreetMap contributors"

# CSS inyectado dentro del mapa Folium: oscurece el basemap para que las zonas
# resalten, y define el latido de los CESFAM (sin GIF, escala sin perder nitidez).
CSS_MAPA = f"""
<style>
.leaflet-tile-pane {{ filter: brightness(.55) saturate(.55) contrast(1.08); }}
.leaflet-container {{ background: #080B14; }}

.cesfam-dot {{
    width: 6px; height: 6px; border-radius: 50%;
    background: {COLOR_CESFAM}; opacity: .9;
    box-shadow: 0 0 0 .5px rgba(8,11,20,.85);
    animation: latido 2.8s ease-out infinite;
}}
@keyframes latido {{
    0%   {{ box-shadow: 0 0 0 .5px rgba(8,11,20,.85), 0 0 0 0 rgba(63,208,126,.45); }}
    70%  {{ box-shadow: 0 0 0 .5px rgba(8,11,20,.85), 0 0 0 8px rgba(63,208,126,0); }}
    100% {{ box-shadow: 0 0 0 .5px rgba(8,11,20,.85), 0 0 0 0 rgba(63,208,126,0); }}
}}

.hosp-dot {{
    width: 13px; height: 13px; border-radius: 3px;
    background: {COLOR_HOSPITAL};
    border: 1.5px solid #080B14;
    box-shadow: 0 0 10px rgba(255,194,75,.45);
    position: relative;
}}
.hosp-dot::before, .hosp-dot::after {{
    content: ''; position: absolute; background: #080B14;
}}
.hosp-dot::before {{ left: 4.4px; top: 1.8px; width: 1.8px; height: 6.4px; }}
.hosp-dot::after  {{ top: 4.4px; left: 1.8px; height: 1.8px; width: 6.4px; }}

.leyenda-mapa {{
    position: absolute; left: 14px; top: 14px; z-index: 900;
    background: rgba(8,11,20,.82); backdrop-filter: blur(8px);
    border: 1px solid rgba(148,163,184,.18); border-radius: 12px;
    padding: 12px 14px; font-family: Inter, sans-serif; font-size: 11.5px;
    color: #CBD5E1; line-height: 1.9; box-shadow: 0 8px 30px rgba(0,0,0,.5);
}}
.leyenda-mapa .fila {{ display: flex; align-items: center; gap: 8px; }}
.leyenda-mapa .caja {{ width: 11px; height: 11px; border-radius: 3px; flex-shrink: 0; }}
.leyenda-mapa .sep  {{ height: 1px; background: rgba(148,163,184,.16); margin: 7px 0; }}
</style>
"""


def miles(x) -> str:
    """Formato chileno: separador de miles con punto."""
    return f"{int(round(x)):,}".replace(",", ".")


def dec(x, n: int = 3) -> str:
    """Formato chileno: coma decimal."""
    return f"{x:.{n}f}".replace(".", ",")


@st.cache_data
def cargar():
    zonas = gpd.read_parquet(os.path.join(DATA_DIR, "zonas.parquet"))
    estab = pd.read_parquet(os.path.join(DATA_DIR, "establecimientos.parquet"))
    return zonas, estab


@st.cache_data
def preparar_comunas(_zonas: gpd.GeoDataFrame, hosp_por_comuna: dict, cesfam_por_comuna: dict) -> gpd.GeoDataFrame:
    """Disuelve las zonas censales en comunas y agrega sus indicadores."""
    geo = _zonas.dissolve(by="COMUNA")[["geometry"]].reset_index()

    ind = (
        _zonas.groupby("COMUNA")
        .apply(
            lambda g: pd.Series(
                {
                    "n_zonas":   len(g),
                    "poblacion": g["n_per"].sum(),
                    "n_zfd":     int(g["tipo"].isin(["ZFD-A", "ZFD-B"]).sum()),
                    "pob_zfd":   g.loc[g["tipo"].isin(["ZFD-A", "ZFD-B"]), "n_per"].sum(),
                    "IDS":       g["IDS"].mean(),
                    "IFO":       g["IFO_v2"].mean(),
                    "IPSS":      g["IPSS_v2"].mean(),
                    "IDH":       g["IDH"].mean(),
                }
            ),
            include_groups=False,
        )
        .reset_index()
    )

    com = geo.merge(ind, on="COMUNA")
    com["pct_zfd"]  = com["pob_zfd"] / com["poblacion"].replace(0, 1) * 100
    com["n_hosp"]   = com["COMUNA"].map(hosp_por_comuna).fillna(0).astype(int)
    com["n_cesfam"] = com["COMUNA"].map(cesfam_por_comuna).fillna(0).astype(int)

    # Campos ya formateados para el tooltip
    com["t_comuna"] = com["COMUNA"]
    com["t_pob"]    = com["poblacion"].apply(lambda v: f"{miles(v)} habitantes")
    com["t_zonas"]  = com["n_zonas"].apply(lambda v: f"{int(v)} zonas censales")
    com["t_zfd"]    = com.apply(
        lambda r: f"{int(r['n_zfd'])} zonas · {miles(r['pob_zfd'])} personas ({dec(r['pct_zfd'], 1)}%)",
        axis=1,
    )
    com["t_ids"]  = com["IDS"].apply(dec)
    com["t_ifo"]  = com["IFO"].apply(dec)
    com["t_ipss"] = com["IPSS"].apply(dec)
    com["t_idh"]  = com["IDH"].apply(lambda v: ("+" if v > 0 else "") + dec(v))
    com["t_red"]  = com.apply(
        lambda r: (
            ("sin hospital" if r["n_hosp"] == 0 else f"{int(r['n_hosp'])} hospital"
             + ("es" if r["n_hosp"] > 1 else ""))
            + " · "
            + (f"{int(r['n_cesfam'])} CESFAM" if r["n_cesfam"] else "sin CESFAM")
        ),
        axis=1,
    )
    return com


# ── CSS de la página ──────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500;700&display=swap');
.stApp { font-family: 'Inter', sans-serif; }
.block-container { max-width: 1300px; padding-top: 3.4rem; padding-bottom: 2rem; }

.zfd-head { text-align:center; padding:0 0 1rem; }
.zfd-kicker {
    font-family:'JetBrains Mono',monospace; font-size:10.5px; font-weight:500;
    text-transform:uppercase; letter-spacing:.22em; color:#8090A8; margin-bottom:.75rem;
}
.zfd-title {
    font-size:clamp(26px,3.6vw,40px); font-weight:800; color:#F1F5F9;
    letter-spacing:-1px; line-height:1.1; margin:0;
}
.zfd-sub { font-size:14.5px; color:#8FA0B8; margin:.8rem auto 0; max-width:640px; line-height:1.6; }
.zfd-sub b { color:#F27186; font-weight:700; }

.stat-row { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:0 0 1.1rem; }
.stat-box {
    background:linear-gradient(160deg,#101728 0%,#0B101C 100%);
    border:1px solid #1B2740; border-radius:16px; padding:14px 10px; text-align:center;
}
.stat-v {
    font-family:'JetBrains Mono',monospace; font-size:clamp(20px,2.6vw,28px);
    font-weight:700; color:#F1F5F9; line-height:1; letter-spacing:-.5px;
}
.stat-v.acento { color:#F27186; }
.stat-l {
    font-size:9.5px; color:#54627A; margin-top:8px; text-transform:uppercase;
    letter-spacing:.13em; line-height:1.4; font-weight:500;
}

.hint {
    text-align:center; font-size:11.5px; color:#54627A; margin:0 0 .7rem;
    letter-spacing:.03em;
}
.mapa-wrap {
    border:1px solid #1B2740; border-radius:18px; overflow:hidden;
    box-shadow:0 16px 50px rgba(0,0,0,.5);
}
.nav-label {
    text-align:center; font-size:10px; font-weight:600; color:#334155;
    text-transform:uppercase; letter-spacing:.16em; margin:1.4rem 0 .7rem;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── ENCABEZADO ────────────────────────────────────────────────────────────────
st.markdown(
    """
<div class="zfd-head">
  <div class="zfd-kicker">Gran Santiago · Región Metropolitana · 2024</div>
  <div class="zfd-title">La Topografía de la Exclusión en Salud</div>
  <div class="zfd-sub">
    <b>1.178.472 personas</b> viven donde la alta vulnerabilidad social coincide
    con acceso deficiente a la red pública de salud.
  </div>
</div>
""",
    unsafe_allow_html=True,
)

try:
    zonas, estab = cargar()

    hospitales = estab[estab["tipo_grupo"] == "hospital"].copy()
    cesfam     = estab[estab["tipo_grupo"] == "primaria"].copy()
    comunas    = preparar_comunas(
        zonas,
        hospitales["ComunaGlosa"].value_counts().to_dict(),
        cesfam["ComunaGlosa"].value_counts().to_dict(),
    )

    # ── INDICADORES ───────────────────────────────────────────────────────────
    n_zfd = int(zonas["tipo"].isin(["ZFD-A", "ZFD-B"]).sum())
    st.markdown(
        f"""
<div class="stat-row">
  <div class="stat-box"><div class="stat-v">{miles(len(zonas))}</div><div class="stat-l">Zonas censales</div></div>
  <div class="stat-box"><div class="stat-v acento">{n_zfd}</div><div class="stat-l">Zonas de falla doble</div></div>
  <div class="stat-box"><div class="stat-v acento">19,2%</div><div class="stat-l">Del Gran Santiago</div></div>
  <div class="stat-box"><div class="stat-v">{len(hospitales)} · {len(cesfam)}</div><div class="stat-l">Hospitales · CESFAM</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    ver_cesfam = st.toggle(
        "Mostrar los 236 CESFAM",
        value=False,
        help="Centros de atención primaria de la red pública",
    )

    # ── MAPA ──────────────────────────────────────────────────────────────────
    m = folium.Map(
        location=[-33.48, -70.65],
        zoom_start=11,
        tiles=TILES_URL,
        attr=TILES_ATTR,
        attributionControl=False,
        zoom_control=False,
    )
    minx, miny, maxx, maxy = zonas.total_bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]], padding=(8, 8))
    m.get_root().header.add_child(folium.Element(CSS_MAPA))

    # Zonas censales, de fondo hacia adelante
    for tipo in ["Resto", "LL", "ZFD-B", "ZFD-A"]:
        sub = zonas[zonas["tipo"] == tipo][["geometry", "tipo"]]
        if sub.empty:
            continue
        folium.GeoJson(
            sub,
            name=tipo,
            style_function=lambda _f, t=tipo: {
                "fillColor": COLORES[t],
                "fillOpacity": OPACIDAD[t],
                "color": "transparent",
                "weight": 0,
            },
        ).add_to(m)

    # Capa de comunas: sin relleno visible. Al pasar el cursor solo se dibuja
    # el contorno, para no tapar las zonas que están debajo.
    folium.GeoJson(
        comunas,
        name="Comunas",
        style_function=lambda _f: {
            "fillColor": "#ffffff",
            "fillOpacity": 0.01,
            "color": "#3E4C63",
            "weight": 0.7,
        },
        highlight_function=lambda _f: {
            "fillColor": "#ffffff",
            "fillOpacity": 0.01,
            "color": "#FFFFFF",
            "weight": 3,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["t_comuna", "t_pob", "t_zonas", "t_zfd", "t_ids", "t_ifo", "t_ipss", "t_idh", "t_red"],
            aliases=[
                "Comuna",
                "Población",
                "Territorio",
                "Zona de Falla Doble",
                "IDS · demanda social",
                "IFO · fricción de oferta",
                "IPSS · presión sistema",
                "IDH · desacoplamiento",
                "Red pública",
            ],
            localize=False,
            sticky=True,
            labels=True,
            style=(
                "background:rgba(8,11,20,.94); color:#E2E8F0;"
                "border:1px solid rgba(148,163,184,.22); border-radius:12px;"
                "padding:12px 14px; font-family:Inter,sans-serif; font-size:12px;"
                "box-shadow:0 10px 34px rgba(0,0,0,.6);"
            ),
        ),
    ).add_to(m)

    # CESFAM — puntos que laten, con desfase para que no pulsen todos a la vez
    if ver_cesfam:
        for i, (_, c) in enumerate(cesfam.iterrows()):
            if pd.isna(c["Latitud"]) or pd.isna(c["Longitud"]):
                continue
            folium.Marker(
                location=[c["Latitud"], c["Longitud"]],
                icon=folium.DivIcon(
                    html=f'<div class="cesfam-dot" style="animation-delay:{(i % 9) * 0.27:.2f}s"></div>',
                    icon_size=(6, 6),
                    icon_anchor=(3, 3),
                ),
                tooltip=folium.Tooltip(
                    f"<b>{c['EstablecimientoGlosa']}</b><br>CESFAM · {c['ComunaGlosa']}",
                    style="font-family:Inter,sans-serif;font-size:12px;",
                ),
            ).add_to(m)

    # Hospitales — marca fija con cruz, por encima de los CESFAM
    for _, h in hospitales.iterrows():
        if pd.isna(h["Latitud"]) or pd.isna(h["Longitud"]):
            continue
        folium.Marker(
            location=[h["Latitud"], h["Longitud"]],
            icon=folium.DivIcon(html='<div class="hosp-dot"></div>', icon_size=(13, 13), icon_anchor=(6, 6)),
            tooltip=folium.Tooltip(
                f"<b>{h['EstablecimientoGlosa']}</b><br>Hospital · {h['ComunaGlosa']}",
                style="font-family:Inter,sans-serif;font-size:12px;",
            ),
        ).add_to(m)

    # Leyenda flotante dentro del mapa
    m.get_root().html.add_child(
        folium.Element(
            f"""
<div class="leyenda-mapa">
  <div class="fila"><span class="caja" style="background:{COLORES['ZFD-A']}"></span>ZFD-A · exclusión periférica</div>
  <div class="fila"><span class="caja" style="background:{COLORES['ZFD-B']}"></span>ZFD-B · sustitución privada</div>
  <div class="fila"><span class="caja" style="background:{COLORES['LL']}"></span>Acceso adecuado</div>
  <div class="sep"></div>
  <div class="fila"><span class="hosp-dot"></span>Hospital público</div>
  <div class="fila"><span class="cesfam-dot"></span>CESFAM</div>
</div>
"""
        )
    )

    st.markdown(
        '<div class="hint">Pasa el cursor sobre una comuna para ver sus indicadores</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="mapa-wrap">', unsafe_allow_html=True)
    st.components.v1.html(m._repr_html_(), height=560)
    st.markdown("</div>", unsafe_allow_html=True)

except FileNotFoundError:
    st.error("No se encontraron los datos en `data/`. Verifica zonas.parquet y establecimientos.parquet.")

# ── NAVEGACIÓN ────────────────────────────────────────────────────────────────
st.markdown('<div class="nav-label">Explorar</div>', unsafe_allow_html=True)
col1, col2 = st.columns(2)
with col1:
    st.page_link("pages/03_simulador.py", label="⚙️ Simulador", use_container_width=True)
with col2:
    st.page_link("pages/02_detalle_zona.py", label="🔍 Detalles por zona", use_container_width=True)

with st.expander("Metodología"):
    st.markdown(
        """
**IPSS v2 = IDS × IFO v2** — Índice de Presión sobre el Sistema de Salud
**ZFD** = LISA HH (Moran's I = 0,3776 · p = 0,001) AND IDH > 0
**IDS** — vulnerabilidad social: hacinamiento, adultos ≥60, discapacidad, jefatura femenina
**IFO v2** — accesibilidad 2SFCA con radio diferenciado · r(IDS, IFO) = −0,491
Fuentes: INE Censo 2024 · DEIS MINSAL 2024
"""
    )
