# -*- coding: utf-8 -*-
"""
Capa 1 — Mapa interactivo del Gran Santiago.

Muestra las 1.636 zonas censales coloreadas por su clasificación ZFD, los 26
hospitales públicos, y una capa de comunas que despliega indicadores agregados
al pasar el cursor por encima.
"""
import os

import folium
import geopandas as gpd
import pandas as pd
import streamlit as st

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

COLORES = {
    "ZFD-A": "#C0392B",
    "ZFD-B": "#E8A29A",
    "LL":    "#2C7FB8",
    "Resto": "#334155",
}
OPACIDAD = {"ZFD-A": 0.88, "ZFD-B": 0.80, "LL": 0.55, "Resto": 0.12}

TILES_URL  = "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}"
TILES_ATTR = "Esri, HERE, Garmin, &copy; OpenStreetMap contributors"


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
def preparar_comunas(_zonas: gpd.GeoDataFrame, hosp_por_comuna: dict) -> gpd.GeoDataFrame:
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
    com["pct_zfd"] = com["pob_zfd"] / com["poblacion"].replace(0, 1) * 100
    com["n_hosp"]  = com["COMUNA"].map(hosp_por_comuna).fillna(0).astype(int)

    # Campos ya formateados para el tooltip
    com["t_comuna"] = com["COMUNA"]
    com["t_pob"]    = com["poblacion"].apply(lambda v: f"{miles(v)} habitantes")
    com["t_zonas"]  = com.apply(lambda r: f"{int(r['n_zonas'])} zonas censales", axis=1)
    com["t_zfd"]    = com.apply(
        lambda r: f"{int(r['n_zfd'])} zonas · {miles(r['pob_zfd'])} personas ({dec(r['pct_zfd'], 1)}%)",
        axis=1,
    )
    com["t_ids"]  = com["IDS"].apply(dec)
    com["t_ifo"]  = com["IFO"].apply(dec)
    com["t_ipss"] = com["IPSS"].apply(dec)
    com["t_idh"]  = com["IDH"].apply(lambda v: ("+" if v > 0 else "") + dec(v))
    com["t_hosp"] = com["n_hosp"].apply(
        lambda v: "sin hospital público" if v == 0 else (f"{v} hospital" if v == 1 else f"{v} hospitales")
    )
    return com


# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');
.stApp { font-family: 'Inter', sans-serif; }

/* Layout ancho para el mapa, pero acotado para que no se estire de borde a borde */
.block-container { max-width: 1280px; padding-top: 2rem; }

.zfd-head { text-align:center; padding:.5rem 0 1rem; }
.zfd-kicker {
    font-family:'JetBrains Mono',monospace; font-size:11px; text-transform:uppercase;
    letter-spacing:.12em; color:#475569; margin-bottom:.5rem;
}
.zfd-title { font-size:clamp(22px,4vw,32px); font-weight:800; color:#F8FAFC; letter-spacing:-.5px; margin:0; }
.zfd-sub   { font-size:14px; color:#94A3B8; margin:.5rem 0 0; }
.zfd-sub b { color:#E8A29A; font-weight:600; }

.stat-row { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin:0 0 1rem; }
.stat-box { background:#0E1223; border:1px solid #1E2D42; border-radius:14px; padding:14px 8px; text-align:center; }
.stat-v   { font-family:'JetBrains Mono',monospace; font-size:clamp(17px,2.4vw,24px); font-weight:700; color:#F8FAFC; line-height:1; }
.stat-l   { font-size:10px; color:#475569; margin-top:6px; text-transform:uppercase; letter-spacing:.05em; line-height:1.3; }

.legend-row  { display:flex; gap:16px; justify-content:center; flex-wrap:wrap; margin:.75rem 0; }
.legend-item { display:flex; align-items:center; gap:6px; font-size:12px; color:#94A3B8; }
.ldot  { width:9px; height:9px; border-radius:50%; flex-shrink:0; }
.lhosp { width:11px; height:11px; border-radius:3px; background:#F5B942; border:1.5px solid #0b0f1a; flex-shrink:0; }

.hint { text-align:center; font-size:12px; color:#64748B; margin:.25rem 0 .75rem; }
.nav-label { text-align:center; font-size:11px; font-weight:600; color:#334155;
             text-transform:uppercase; letter-spacing:.1em; margin:1.25rem 0 .6rem; }
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
    hosp_por_comuna = hospitales["ComunaGlosa"].value_counts().to_dict()
    comunas = preparar_comunas(zonas, hosp_por_comuna)

    # ── INDICADORES ───────────────────────────────────────────────────────────
    n_zfd  = int(zonas["tipo"].isin(["ZFD-A", "ZFD-B"]).sum())
    pob_gs = zonas["n_per"].sum()
    st.markdown(
        f"""
<div class="stat-row">
  <div class="stat-box"><div class="stat-v">{len(zonas)}</div><div class="stat-l">Zonas<br>censales</div></div>
  <div class="stat-box"><div class="stat-v">{n_zfd}</div><div class="stat-l">Zonas de<br>falla doble</div></div>
  <div class="stat-box"><div class="stat-v">19,2%</div><div class="stat-l">Del Gran<br>Santiago</div></div>
  <div class="stat-box"><div class="stat-v">{len(hospitales)}</div><div class="stat-l">Hospitales<br>públicos</div></div>
</div>
""",
        unsafe_allow_html=True,
    )

    # ── MAPA ──────────────────────────────────────────────────────────────────
    m = folium.Map(
        location=[-33.48, -70.65],
        zoom_start=11,
        tiles=TILES_URL,
        attr=TILES_ATTR,
        attributionControl=False,
    )
    # Encuadra el Gran Santiago para que no sobre mapa vacío alrededor
    minx, miny, maxx, maxy = zonas.total_bounds
    m.fit_bounds([[miny, minx], [maxy, maxx]], padding=(8, 8))

    # Zonas censales, de fondo hacia adelante
    cols_zona = ["geometry", "tipo", "COMUNA", "IPSS_v2", "n_per"]
    for tipo in ["Resto", "LL", "ZFD-B", "ZFD-A"]:
        sub = zonas[zonas["tipo"] == tipo][cols_zona]
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

    # Capa de comunas: invisible pero sensible al cursor, va encima de todo
    folium.GeoJson(
        comunas,
        name="Comunas",
        style_function=lambda _f: {
            "fillColor": "#ffffff",
            "fillOpacity": 0.01,
            "color": "#64748B",
            "weight": 0.8,
        },
        highlight_function=lambda _f: {
            "fillColor": "#F8FAFC",
            "fillOpacity": 0.18,
            "color": "#F8FAFC",
            "weight": 2.5,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["t_comuna", "t_pob", "t_zonas", "t_zfd", "t_ids", "t_ifo", "t_ipss", "t_idh", "t_hosp"],
            aliases=[
                "Comuna",
                "Población",
                "Territorio",
                "Zona de Falla Doble",
                "IDS · demanda social",
                "IFO · fricción de oferta",
                "IPSS · presión sistema",
                "IDH · desacoplamiento",
                "Red hospitalaria",
            ],
            localize=False,
            sticky=True,
            labels=True,
            style=(
                "background-color:#0E1223; color:#E2E8F0; border:1px solid #1E2D42;"
                "border-radius:10px; padding:10px 12px; font-family:Inter,sans-serif;"
                "font-size:12px; box-shadow:0 8px 28px rgba(0,0,0,.55);"
            ),
        ),
    ).add_to(m)

    # Hospitales públicos
    for _, h in hospitales.iterrows():
        if pd.isna(h["Latitud"]) or pd.isna(h["Longitud"]):
            continue
        folium.CircleMarker(
            location=[h["Latitud"], h["Longitud"]],
            radius=5.5,
            color="#0b0f1a",
            weight=1.5,
            fill=True,
            fill_color="#F5B942",
            fill_opacity=1,
            tooltip=folium.Tooltip(
                f"<b>{h['EstablecimientoGlosa']}</b><br>{h['ComunaGlosa']}",
                style="font-family:Inter,sans-serif; font-size:12px;",
            ),
        ).add_to(m)

    st.markdown(
        '<div class="hint">Pasa el cursor sobre una comuna para ver sus indicadores</div>',
        unsafe_allow_html=True,
    )
    st.components.v1.html(m._repr_html_(), height=680)

    # ── LEYENDA ───────────────────────────────────────────────────────────────
    st.markdown(
        """
<div class="legend-row">
  <span class="legend-item"><span class="ldot" style="background:#C0392B"></span>ZFD-A · exclusión periférica</span>
  <span class="legend-item"><span class="ldot" style="background:#E8A29A"></span>ZFD-B · sustitución privada</span>
  <span class="legend-item"><span class="ldot" style="background:#2C7FB8"></span>LL · acceso adecuado</span>
  <span class="legend-item"><span class="lhosp"></span>Hospital público</span>
</div>
""",
        unsafe_allow_html=True,
    )

except FileNotFoundError:
    st.error("No se encontraron los datos en `data/`. Verifica zonas.parquet y establecimientos.parquet.")

st.divider()

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
