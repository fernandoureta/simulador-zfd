# -*- coding: utf-8 -*-
"""Capa 1 — Mapa 3D IPSS por zona censal (pydeck ColumnLayer)."""
import streamlit as st
import geopandas as gpd
import pydeck as pdk
import os

st.set_page_config(page_title="Mapa 3D ZFD", page_icon="🗺️", layout="wide")
st.title("🗺️ Mapa 3D — Intensidad IPSS por zona censal")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "zonas.parquet")

@st.cache_data
def cargar():
    gdf = gpd.read_parquet(DATA_PATH)
    return gdf[["ID_ZONA","COMUNA","tipo","IPSS_v2","IDS","IFO_v2","IDH","n_per","lon","lat"]].dropna(subset=["lon","lat"])

try:
    df = cargar()

    COLOR_MAP = {
        "ZFD-A": [192,  57,  43, 210],
        "ZFD-B": [232, 162, 154, 200],
        "LL":    [ 44, 127, 184, 170],
        "Resto": [170, 170, 170,  90],
    }
    df = df.copy()
    df["color"] = df["tipo"].map(COLOR_MAP)

    variable = st.selectbox("Variable de altura", ["IPSS_v2","IDS","IFO_v2","IDH"])
    escala   = st.slider("Escala de altura", 500, 8000, 2500, step=250)
    df["elevation"] = df[variable].clip(lower=0) * escala

    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["lon","lat"],
        get_elevation="elevation",
        radius=150,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
        elevation_scale=1,
    )
    view = pdk.ViewState(longitude=-70.65, latitude=-33.46, zoom=10, pitch=48, bearing=0)

    st.pydeck_chart(pdk.Deck(
        layers=[layer],
        initial_view_state=view,
        map_style="mapbox://styles/mapbox/dark-v10",
        tooltip={"text": "{COMUNA}\nTipo: {tipo}\nIPSS: {IPSS_v2}\nIDS: {IDS}\nIFO: {IFO_v2}\nIDH: {IDH}"},
    ))

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Zonas ZFD-A", int((df["tipo"]=="ZFD-A").sum()), "crecimiento no compensado")
    col2.metric("Zonas ZFD-B", int((df["tipo"]=="ZFD-B").sum()), "sustitución privada")
    col3.metric("Zonas LL",    int((df["tipo"]=="LL").sum()),    "acceso concentrado")
    col4.metric("Total zonas", len(df))

    with st.expander("ℹ️ Sobre el mapa"):
        st.markdown("""
**ZFD-A** (rojo): zonas con alta vulnerabilidad social (IDS↑) Y acceso deficiente a la red pública (IFO↑),
fuera de las 6 comunas con cobertura ISAPRE dominante.

**ZFD-B** (rosa): mismo patrón en Las Condes, Vitacura, Providencia, Ñuñoa, Lo Barnechea, La Reina —
red pública ausente por sustitución privada.

**LL** (azul): clústers de bajo-bajo (baja vulnerabilidad O buena accesibilidad) — la red compensa.

La altura representa la intensidad de la variable seleccionada.
""")

except FileNotFoundError:
    st.error("Archivo `data/zonas.parquet` no encontrado.")
    st.code("Ejecuta preparar_datos_simulador.py para generar el archivo.")
