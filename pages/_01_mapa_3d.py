# -*- coding: utf-8 -*-
"""Capa 1 — Mapa 3D de exclusión en salud (pydeck HexagonLayer)."""
import streamlit as st
import geopandas as gpd
import pydeck as pdk
import os

st.set_page_config(page_title="Mapa 3D ZFD", page_icon="🗺️", layout="wide",
                   initial_sidebar_state="collapsed")
st.title("🗺️ Focos de exclusión en salud · Gran Santiago")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "zonas.parquet")

@st.cache_data
def cargar():
    gdf = gpd.read_parquet(DATA_PATH)
    return gdf[["ID_ZONA","COMUNA","tipo","IPSS_v2","IDS","IFO_v2","IDH","n_per","lon","lat"]].dropna(subset=["lon","lat"])

# De negro/invisible (IPSS bajo) → rojo ZFD canónico (IPSS alto)
COLOR_RANGE = [
    [20,  20,  35],
    [60,  25,  25],
    [100, 35,  32],
    [145, 47,  40],
    [175, 55,  43],
    [192, 57,  43],
]

try:
    df = cargar()

    layer = pdk.Layer(
        "HexagonLayer",
        data=df,
        get_position=["lon", "lat"],
        get_elevation_weight="IPSS_v2",
        get_color_weight="IPSS_v2",
        elevation_aggregation="MEAN",
        color_aggregation="MEAN",
        radius=700,
        elevation_scale=5000,
        extruded=True,
        coverage=0.88,
        color_range=COLOR_RANGE,
        pickable=True,
        auto_highlight=True,
    )

    view = pdk.ViewState(
        longitude=-70.65, latitude=-33.46,
        zoom=10, pitch=52, bearing=0
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={"text": "Zonas en celda: {count}\nIPSS medio: {colorValue:.3f}"},
    ))

    st.caption("☝️ Un dedo: mover · Dos dedos: rotar y zoom")

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Zonas ZFD-A", int((df["tipo"]=="ZFD-A").sum()), "exclusión periférica")
    col2.metric("Zonas ZFD-B", int((df["tipo"]=="ZFD-B").sum()), "sustitución privada")
    col3.metric("Zonas LL",    int((df["tipo"]=="LL").sum()),    "acceso adecuado")
    col4.metric("Total zonas", len(df))

    with st.expander("ℹ️ Sobre el mapa"):
        st.markdown("""
Cada hexágono agrupa zonas censales cercanas. **La altura y el color** representan
el IPSS medio del grupo (IDS × IFO v2): a mayor altura y más rojo, mayor exclusión.

Los picos más altos marcan los **focos territoriales** donde la vulnerabilidad social
alta coincide con acceso deficiente a la red pública de salud.
""")

except FileNotFoundError:
    st.error("Archivo `data/zonas.parquet` no encontrado.")
    st.code("Ejecuta preparar_datos_simulador.py para generar el archivo.")
