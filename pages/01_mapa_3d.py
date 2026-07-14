# -*- coding: utf-8 -*-
"""
Capa 1 — Mapa 3D
Visualización geoespacial 3D de IPSS v2 por zona censal (pydeck).
"""
import streamlit as st
import pandas as pd
import pydeck as pdk
import numpy as np

st.set_page_config(page_title="Mapa 3D ZFD", page_icon="🗺️", layout="wide")
st.title("🗺️ Mapa 3D — Intensidad IPSS por zona censal")

# ── Datos ──────────────────────────────────────────────────────────────────────
@st.cache_data
def cargar_datos():
    import geopandas as gpd
    from shapely import wkb

    ifo   = pd.read_parquet("data/ifo_v2_zonal.parquet")
    lisa  = pd.read_parquet("data/lisa_zonal.parquet")
    censo = pd.read_parquet("data/censo_zonal_rm_indicadores.parquet")

    GRAN_SANTIAGO = list(range(13101, 13133)) + [13201, 13401]
    censo = censo[censo["CUT"].isin(GRAN_SANTIAGO)].copy()
    censo["geometry"] = censo["SHAPE"].apply(
        lambda v: wkb.loads(v) if isinstance(v, bytes) else None
    )
    censo = censo[censo["geometry"].notna()].copy()

    ifo["COMUNA"] = ifo["COMUNA"].str.title().str.strip()
    cols_ok = [c for c in ifo.columns if c not in lisa.columns] + ["ID_ZONA"]
    full = lisa.merge(ifo[cols_ok], on="ID_ZONA", how="left")
    full["COMUNA"]   = full["COMUNA"].str.title().str.strip()
    full["lisa_cat"] = full["lisa_cat"].fillna("NS")

    B0, B1 = 0.9640, -1.0213
    full["IDH"] = full["IFO_v2"] - (B0 + B1 * full["IDS"])

    COMUNAS_B = {"Las Condes","Vitacura","Providencia","Ñuñoa","Lo Barnechea","La Reina"}
    full["grupo_b"] = full["COMUNA"].isin(COMUNAS_B)
    full["ZFD"]     = (full["lisa_cat"] == "HH") & (full["IDH"] > 0)

    def cat4(row):
        if row["ZFD"] and not row["grupo_b"]: return "ZFD-A"
        if row["ZFD"] and row["grupo_b"]:     return "ZFD-B"
        if row["lisa_cat"] == "LL":           return "LL"
        return "Resto"
    full["tipo"] = full.apply(cat4, axis=1)

    gdf = gpd.GeoDataFrame(
        censo[["ID_ZONA","geometry"]], geometry="geometry", crs="EPSG:4326"
    ).merge(full[["ID_ZONA","tipo","IPSS_v2","IDS","IFO_v2","IDH","COMUNA","lisa_cat"]], on="ID_ZONA", how="inner")

    # Centroide para pydeck ColumnLayer
    gdf["lon"] = gdf.geometry.centroid.x
    gdf["lat"] = gdf.geometry.centroid.y
    return gdf[["ID_ZONA","COMUNA","tipo","IPSS_v2","IDS","IFO_v2","IDH","lon","lat"]].dropna()

try:
    df = cargar_datos()

    COLOR_MAP = {
        "ZFD-A": [192, 57, 43, 200],
        "ZFD-B": [232, 162, 154, 200],
        "LL":    [44, 127, 184, 160],
        "Resto": [180, 180, 180, 100],
    }
    df["color"] = df["tipo"].map(COLOR_MAP)

    ESCALA = st.slider("Escala altura (IPSS × factor)", 100, 5000, 1500, step=100)
    df["elevation"] = df["IPSS_v2"] * ESCALA

    layer = pdk.Layer(
        "ColumnLayer",
        data=df,
        get_position=["lon","lat"],
        get_elevation="elevation",
        elevation_scale=1,
        radius=150,
        get_fill_color="color",
        pickable=True,
        auto_highlight=True,
    )

    view = pdk.ViewState(
        longitude=df["lon"].mean(),
        latitude=df["lat"].mean(),
        zoom=10, pitch=45, bearing=0,
    )

    st.pydeck_chart(pdk.Deck(
        layers=[layer], initial_view_state=view,
        tooltip={"text": "{COMUNA}\nTipo: {tipo}\nIPSS: {IPSS_v2:.3f}\nIDS: {IDS:.3f}\nIFO: {IFO_v2:.3f}"},
    ))

    col1, col2, col3 = st.columns(3)
    col1.metric("Zonas ZFD-A", int((df["tipo"]=="ZFD-A").sum()))
    col2.metric("Zonas ZFD-B", int((df["tipo"]=="ZFD-B").sum()))
    col3.metric("Zonas LL",    int((df["tipo"]=="LL").sum()))

except FileNotFoundError:
    st.warning("Archivos de datos no encontrados en `data/`. Coloca los parquet en esa carpeta.")
    st.code("data/ifo_v2_zonal.parquet\ndata/lisa_zonal.parquet\ndata/censo_zonal_rm_indicadores.parquet")
