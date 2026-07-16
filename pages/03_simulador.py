# -*- coding: utf-8 -*-
"""
Capa 3 — Simulador de intervención territorial.

Modelo: accesibilidad potencial con distancia-decay lineal.
  ΔIFO(zona i) = reduccion_max × max(0, 1 − dist(i, nuevo_estab) / radio)

El nuevo establecimiento se coloca en el centroide de la zona ZFD-A más
afectada (mayor IDH) de la comuna seleccionada.

Nota: "modelo de accesibilidad potencial, no predicción operacional."
"""
import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Simulador ZFD", page_icon="⚙️", layout="wide")
st.title("⚙️ Simulador de intervención territorial")

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
B0, B1   = 0.9640, -1.0213

TIPOS = {
    "CESFAM (primaria, radio 1.5 km)": {"radio": 1500, "reduccion_max": 0.10, "grupo": "primaria"},
    "SAPU / SAR (urgencia, radio 2 km)": {"radio": 2000, "reduccion_max": 0.08, "grupo": "urgencia"},
    "Hospital (radio 5 km)":            {"radio": 5000, "reduccion_max": 0.15, "grupo": "hospital"},
}

def dist_m(lat1, lon1, lat2_arr, lon2_arr):
    dlat = (np.asarray(lat2_arr) - lat1) * 111_320
    dlon = (np.asarray(lon2_arr) - lon1) * 111_320 * 0.832
    return np.sqrt(dlat**2 + dlon**2)

@st.cache_data
def cargar():
    zonas = gpd.read_parquet(os.path.join(DATA_DIR, "zonas.parquet"))
    estab = pd.read_parquet(os.path.join(DATA_DIR, "establecimientos.parquet"))
    return zonas, estab

try:
    df, estab = cargar()
    zfd_a     = df[df["tipo"] == "ZFD-A"].copy()

    st.markdown(
        f"**Base:** {len(zfd_a)} zonas ZFD-A · "
        f"{int(zfd_a['n_per'].sum()):,} personas · IDH medio = +{zfd_a['IDH'].mean():.3f}"
        .replace(",",".")
    )
    st.caption(
        "⚠️ **Modelo de accesibilidad potencial, no predicción operacional.** "
        "El nuevo establecimiento se ubica en la zona más afectada de la comuna. "
        "ΔIFO decae linealmente con la distancia dentro del radio de captación. "
        "La demanda no se redistribuye entre inscripciones."
    )
    st.divider()

    # ── Parámetros ───────────────────────────────────────────────────────────────
    comunas_zfda = sorted(zfd_a["COMUNA"].dropna().unique())
    col1, col2   = st.columns([1, 2])

    with col1:
        comuna_sel = st.selectbox("Comuna de intervención", comunas_zfda)
        tipo_sel   = st.selectbox("Tipo de establecimiento", list(TIPOS.keys()))
        cfg        = TIPOS[tipo_sel]
        radio      = cfg["radio"]
        red_max    = cfg["reduccion_max"]

    # ── Ubicación óptima del nuevo establecimiento ───────────────────────────────
    # Colocar en el centroide de la zona ZFD-A con mayor IDH de la comuna
    zfd_com = zfd_a[zfd_a["COMUNA"] == comuna_sel]
    if len(zfd_com) == 0:
        st.warning(f"No hay zonas ZFD-A en {comuna_sel}.")
        st.stop()

    worst_zone = zfd_com.loc[zfd_com["IDH"].idxmax()]
    new_lat    = float(worst_zone["lat"])
    new_lon    = float(worst_zone["lon"])

    # ── Simulación: distance-decay sobre TODAS las zonas ────────────────────────
    sim = df.copy()
    d   = dist_m(new_lat, new_lon, sim["lat"].values, sim["lon"].values)
    decay = (1 - d / radio).clip(lower=0)   # factor lineal en [0,1]

    sim["IFO_sim"]  = (sim["IFO_v2"] - red_max * decay).clip(lower=0)
    sim["IDH_sim"]  = sim["IFO_sim"] - (B0 + B1 * sim["IDS"])
    sim["IPSS_sim"] = sim["IDS"] * sim["IFO_sim"]

    # Zonas afectadas (dentro del radio) que son ZFD-A
    dentro_radio = d <= radio
    zfd_en_radio = sim[dentro_radio & (sim["tipo"] == "ZFD-A")].copy()
    salen        = int((zfd_en_radio["IDH_sim"] <= 0).sum())
    pop_salen    = int(zfd_en_radio.loc[zfd_en_radio["IDH_sim"] <= 0, "n_per"].sum())
    n_en_radio   = len(zfd_en_radio)

    # Establecimientos existentes en el área afectada (para contexto)
    estab_grupo  = estab[estab["tipo_grupo"] == cfg["grupo"]]
    d_est        = dist_m(new_lat, new_lon, estab_grupo["Latitud"].values, estab_grupo["Longitud"].values)
    n_exist_radio = int((d_est <= radio).sum())

    with col2:
        r1, r2, r3, r4 = st.columns(4)
        r1.metric("Zona de colocación", f"ID {int(worst_zone['ID_ZONA'])}", f"IDH máx = +{float(worst_zone['IDH']):.3f}")
        r2.metric("ZFD-A dentro del radio", n_en_radio)
        r3.metric("Zonas rescatadas", salen,
                  delta=f"−{salen} zonas ZFD" if salen > 0 else "ninguna")
        r4.metric("Personas rescatadas", f"{pop_salen:,}".replace(",","."))

        if n_exist_radio > 0:
            st.info(
                f"Ya existen **{n_exist_radio} establecimientos** del mismo tipo "
                f"dentro del radio de {radio/1000:.1f} km. El nuevo establecimiento "
                "reduce IFO marginalmente sobre los ya cubiertos."
            )

        if salen == 0 and n_en_radio > 0:
            idh_min   = float(zfd_en_radio["IDH"].min())
            cesfam_n  = int(np.ceil(idh_min / red_max))
            st.warning(
                f"Ninguna zona ZFD-A dentro del radio cruza el umbral homeostático. "
                f"La zona más marginal tiene IDH = +{idh_min:.3f}; "
                f"necesita al menos **{cesfam_n} establecimientos** de este tipo."
            )
        elif salen > 0:
            st.success(
                f"✅ **{salen} zona(s) salen de ZFD** → {pop_salen:,} personas rescatadas."
                .replace(",",".")
            )

    # ── Mapa de efecto ───────────────────────────────────────────────────────────
    st.subheader("Efecto espacial del establecimiento")
    c_map1, c_map2 = st.columns(2)

    for col_grafico, col_idh, titulo in [
        (c_map1, "IDH",     "IDH actual"),
        (c_map2, "IDH_sim", "IDH simulado"),
    ]:
        fig, ax = plt.subplots(figsize=(4.5, 4))
        RED, BLUE, GREY = "#C0392B", "#2C7FB8", "#D9D9D9"
        colors = sim["tipo"].map({"ZFD-A":RED,"ZFD-B":"#E8A29A","LL":BLUE,"Resto":GREY})
        ax.scatter(sim["lon"], sim["lat"], c=colors, s=2, alpha=0.6, lw=0)
        # Nuevo establecimiento
        ax.scatter(new_lon, new_lat, marker="*", s=180, c="#27AE60", zorder=5, label="Nuevo estab.")
        # Radio
        theta = np.linspace(0, 2*np.pi, 120)
        r_deg_lat = radio / 111_320
        r_deg_lon = radio / (111_320 * 0.832)
        ax.plot(new_lon + r_deg_lon * np.cos(theta), new_lat + r_deg_lat * np.sin(theta),
                "g--", lw=1, alpha=0.6)
        ax.set_title(titulo, fontsize=10)
        ax.axis("off")
        ax.legend(fontsize=7, loc="lower left")
        fig.tight_layout(pad=0.2)
        col_grafico.pyplot(fig)
        plt.close(fig)

    # ── Tabla de zonas en el radio ────────────────────────────────────────────────
    with st.expander(f"Zonas ZFD-A dentro del radio ({n_en_radio} zonas)"):
        if len(zfd_en_radio) == 0:
            st.info("Sin zonas ZFD-A dentro del radio.")
        else:
            tabla = zfd_en_radio[["ID_ZONA","COMUNA","IDS","IFO_v2","IFO_sim","IDH","IDH_sim","n_per"]].copy()
            tabla["dist_km"] = (d[zfd_en_radio.index] / 1000).round(2)
            tabla["sale_ZFD"] = tabla["IDH_sim"] <= 0
            st.dataframe(
                tabla.sort_values("IDH").set_index("ID_ZONA")
                    .style.format({"IDS":"{:.3f}","IFO_v2":"{:.3f}","IFO_sim":"{:.3f}",
                                   "IDH":"{:+.3f}","IDH_sim":"{:+.3f}","n_per":"{:.0f}","dist_km":"{:.2f}"})
                    .background_gradient(subset=["IDH_sim"], cmap="RdYlGn_r")
            )

    with st.expander("Nota metodológica"):
        st.markdown(f"""
**Ubicación del establecimiento**
Se coloca en el centroide de la zona ZFD-A con mayor IDH de la comuna seleccionada
(la más afectada). En la realidad, la ubicación óptima depende de infraestructura
existente, acceso vial y densidad de demanda.

**Fórmula de reducción de IFO**
ΔIFO(zona i) = {red_max} × max(0, 1 − distancia / {radio} m)
Calibrado como la reducción máxima de IFO observada en el 2SFCA al agregar un
establecimiento del mismo tipo en una zona ZFD-A típica.

**Supuestos**
- La demanda no se redistribuye (sin cambio de inscripción).
- El establecimiento opera con capacidad promedio de la red pública.
- Coeficientes OLS congelados: β₀ = {B0}, β₁ = {B1}.
- IFO v2 captura **accesibilidad potencial**, no utilización real.
""")

except FileNotFoundError as e:
    st.error(f"Archivo no encontrado: {e}")
    st.code("Ejecuta preparar_datos_simulador.py para generar los archivos de datos.")
