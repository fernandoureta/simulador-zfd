# -*- coding: utf-8 -*-
"""Capa 1 — Mapa coroplético de exclusión en salud (Folium + polígonos reales)."""
import streamlit as st
import geopandas as gpd
import folium
import os

st.set_page_config(page_title="Mapa ZFD", page_icon="🗺️", layout="centered",
                   initial_sidebar_state="collapsed")
st.title("🗺️ Zonas de Falla Doble · Gran Santiago")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "zonas.parquet")

@st.cache_data
def cargar():
    gdf = gpd.read_parquet(DATA_PATH)
    cols = ["ID_ZONA", "COMUNA", "tipo", "IPSS_v2", "IDS", "IFO_v2", "IDH", "n_per", "geometry"]
    return gdf[cols]

COLORES = {
    "ZFD-A": "#C0392B",
    "ZFD-B": "#E8A29A",
    "LL":    "#2C7FB8",
    "Resto": "#666666",
}

OPACIDAD = {
    "ZFD-A": 0.88,
    "ZFD-B": 0.78,
    "LL":    0.55,
    "Resto": 0.10,
}

def estilo(feature):
    tipo = feature["properties"].get("tipo", "Resto")
    return {
        "fillColor":   COLORES.get(tipo, "#666"),
        "fillOpacity": OPACIDAD.get(tipo, 0.1),
        "color":       "transparent",
        "weight":      0,
    }

try:
    gdf = cargar()

    m = folium.Map(
        location=[-33.46, -70.65],
        zoom_start=11,
        tiles="CartoDB DarkMatter",
        scrollWheelZoom=False,
        attributionControl=False,
    )

    # Orden de renderizado: Resto → LL → ZFD-B → ZFD-A (ZFD-A queda encima)
    for tipo in ["Resto", "LL", "ZFD-B", "ZFD-A"]:
        sub = gdf[gdf["tipo"] == tipo].copy()
        if len(sub) == 0:
            continue

        tooltip = None
        if tipo in ("ZFD-A", "ZFD-B"):
            tooltip = folium.GeoJsonTooltip(
                fields=["COMUNA", "tipo", "IPSS_v2", "n_per"],
                aliases=["Comuna", "Tipo", "IPSS", "Hab."],
                localize=True,
                sticky=False,
            )
        elif tipo == "LL":
            tooltip = folium.GeoJsonTooltip(
                fields=["COMUNA", "IPSS_v2"],
                aliases=["Comuna", "IPSS"],
                localize=True,
                sticky=False,
            )

        folium.GeoJson(
            sub[["geometry", "tipo", "COMUNA", "IPSS_v2", "n_per"]],
            style_function=estilo,
            tooltip=tooltip,
            name=tipo,
        ).add_to(m)

    st.components.v1.html(m._repr_html_(), height=520)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Zonas ZFD-A", int((gdf["tipo"] == "ZFD-A").sum()), "exclusión periférica")
    col2.metric("Zonas ZFD-B", int((gdf["tipo"] == "ZFD-B").sum()), "sustitución privada")
    col3.metric("Zonas LL",    int((gdf["tipo"] == "LL").sum()),    "acceso adecuado")
    col4.metric("Total zonas", len(gdf))

    with st.expander("ℹ️ Sobre el mapa"):
        st.markdown("""
**ZFD-A** (rojo): alta vulnerabilidad social Y acceso deficiente a red pública,
fuera de las 6 comunas con cobertura ISAPRE dominante.

**ZFD-B** (rosa): mismo patrón en Las Condes, Vitacura, Providencia, Ñuñoa,
Lo Barnechea y La Reina — red pública ausente por sustitución privada.

**LL** (azul): clústers de bajo-bajo — la red de salud compensa la vulnerabilidad.

Toca una zona para ver sus indicadores.
""")

except FileNotFoundError:
    st.error("Archivo `data/zonas.parquet` no encontrado.")
    st.code("Ejecuta preparar_datos_simulador.py para generar el archivo.")
