# -*- coding: utf-8 -*-
"""
Capa 3 — Simulador de intervención
Proyecta el impacto de agregar establecimientos de salud en zonas ZFD-A.
"""
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Simulador", page_icon="⚙️", layout="wide")
st.title("⚙️ Simulador de intervención territorial")
st.caption("¿Cuántas zonas ZFD-A dejarían de ser ZFD si se agrega capacidad de atención?")

@st.cache_data
def cargar_datos():
    ifo  = pd.read_parquet("data/ifo_v2_zonal.parquet")
    lisa = pd.read_parquet("data/lisa_zonal.parquet")

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
    return full

try:
    df = cargar_datos()
    zfd_a = df[df["tipo"] == "ZFD-A"].copy()

    st.markdown(f"**Base de simulación:** {len(zfd_a)} zonas ZFD-A")

    st.subheader("Parámetros de intervención")
    col1, col2 = st.columns(2)

    with col1:
        reduccion_ifo = st.slider(
            "Reducción de IFO por zona intervenida (puntos)",
            min_value=0.05, max_value=0.50, value=0.15, step=0.01,
            help="Cuánto baja el IFO v2 si se añade un establecimiento de salud primario en la zona"
        )
        n_zonas = st.slider(
            "Número de zonas a intervenir",
            min_value=1, max_value=len(zfd_a), value=min(20, len(zfd_a)), step=1
        )

    with col2:
        criterio = st.radio(
            "Priorizar zonas por:",
            ["Mayor IPSS v2 (mayor presión)", "Mayor IDH (mayor desajuste)", "Mayor IDS (mayor vulnerabilidad)"],
        )

    col_ord = {"Mayor IPSS v2 (mayor presión)": "IPSS_v2",
               "Mayor IDH (mayor desajuste)": "IDH",
               "Mayor IDS (mayor vulnerabilidad)": "IDS"}[criterio]

    # Simulación
    zfd_sim = zfd_a.sort_values(col_ord, ascending=False).copy()
    intervenir = zfd_sim.head(n_zonas).index
    zfd_sim["IFO_sim"] = zfd_sim["IFO_v2"].copy()
    zfd_sim.loc[intervenir, "IFO_sim"] = (zfd_sim.loc[intervenir, "IFO_v2"] - reduccion_ifo).clip(lower=0)

    B0, B1 = 0.9640, -1.0213
    zfd_sim["IDH_sim"] = zfd_sim["IFO_sim"] - (B0 + B1 * zfd_sim["IDS"])
    zfd_sim["IPSS_sim"] = zfd_sim["IDS"] * zfd_sim["IFO_sim"]

    # ¿Cuántas salen de ZFD?  (IDH_sim <= 0 ya no es "encima de la recta")
    salen = int((zfd_sim.loc[intervenir, "IDH_sim"] <= 0).sum())
    siguen = n_zonas - salen

    st.divider()
    st.subheader("Resultado de la simulación")
    r1, r2, r3 = st.columns(3)
    r1.metric("Zonas intervenidas", n_zonas)
    r2.metric("Zonas que salen de ZFD", salen, delta=f"-{salen} zonas ZFD-A")
    r3.metric("Reducción relativa ZFD-A", f"{salen/len(zfd_a)*100:.1f}%")

    # Gráfico comparativo
    fig, axes = plt.subplots(1, 2, figsize=(10, 4))
    for ax, col, title in zip(axes,
                              ["IDH", "IDH_sim"],
                              ["IDH actual", "IDH simulado"]):
        ax.hist(zfd_sim[col], bins=20, color="#C0392B" if "sim" not in col else "#E8A29A",
                edgecolor="white", linewidth=0.5)
        ax.axvline(0, color="#1F2A30", lw=1.5, ls="--")
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("IDH (desajuste homeostático)")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    st.subheader(f"Top zonas intervenidas (ordenadas por {col_ord})")
    cols_show = ["COMUNA", "IDS", "IFO_v2", "IFO_sim", "IDH", "IDH_sim", "IPSS_v2", "IPSS_sim"]
    st.dataframe(
        zfd_sim.loc[intervenir, cols_show]
               .sort_values(col_ord, ascending=False)
               .style.format("{:.3f}", subset=["IDS","IFO_v2","IFO_sim","IDH","IDH_sim","IPSS_v2","IPSS_sim"])
               .background_gradient(subset=["IDH_sim"], cmap="RdYlGn_r")
    )

except FileNotFoundError:
    st.warning("Archivos de datos no encontrados en `data/`.")
    st.code("data/ifo_v2_zonal.parquet\ndata/lisa_zonal.parquet")
