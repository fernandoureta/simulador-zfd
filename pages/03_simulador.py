# -*- coding: utf-8 -*-
"""
Capa 3 — Simulador de intervención territorial.
Input: agregar N CESFAM en una comuna ZFD-A.
Modelo: accesibilidad potencial (no predicción operacional).
Calibración: ΔIFO = −0,07 por CESFAM  (calibrado como 1/5 de la brecha IFO entre
ZFD-A media y LL media: 0,670 → 0,343 ≈ 0,33, dividido entre 5 establecimientos).
"""
import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

st.set_page_config(page_title="Simulador ZFD", page_icon="⚙️", layout="wide")
st.title("⚙️ Simulador de intervención territorial")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "zonas.parquet")

DELTA_IFO_CESFAM = -0.07   # calibrado desde datos: -(IFO_LL − IFO_ZFD-A) / 5
B0, B1           =  0.9640, -1.0213

@st.cache_data
def cargar():
    return gpd.read_parquet(DATA_PATH)

try:
    df = cargar()
    zfd_a = df[df["tipo"] == "ZFD-A"].copy()

    # ── Panel de contexto ────────────────────────────────────────────────────────
    st.markdown(
        f"**Base de simulación:** {len(zfd_a)} zonas ZFD-A · "
        f"{int(zfd_a['n_per'].sum()):,} personas · IDH medio = +{zfd_a['IDH'].mean():.3f}".replace(",",".")
    )
    st.caption(
        "⚠️ **Modelo de accesibilidad potencial, no predicción operacional.** "
        "Cada CESFAM reduce el IFO en 0,07 puntos para las zonas de la comuna seleccionada, "
        "asumiendo capacidad promedio de la red pública existente y sin redistribución "
        "conductual de demanda."
    )

    st.divider()

    # ── Parámetros ───────────────────────────────────────────────────────────────
    comunas_zfda = sorted(zfd_a["COMUNA"].dropna().unique())
    col1, col2 = st.columns([1, 2])

    with col1:
        comuna_sel = st.selectbox("Comuna de intervención", comunas_zfda)
        n_cesfam   = st.select_slider(
            "Número de CESFAM nuevos",
            options=[1, 2, 3, 4, 5],
            value=2,
        )
        st.caption(
            f"ΔIFO aplicado: {DELTA_IFO_CESFAM * n_cesfam:.2f}  "
            f"({n_cesfam} × {DELTA_IFO_CESFAM:.2f} por CESFAM)"
        )

    # ── Simulación ───────────────────────────────────────────────────────────────
    # Zonas intervenidas = todas las ZFD-A de la comuna seleccionada
    mask_comuna = zfd_a["COMUNA"] == comuna_sel
    zfd_sim     = zfd_a.copy()
    delta       = float(n_cesfam) * DELTA_IFO_CESFAM   # negativo

    zfd_sim["IFO_sim"]  = zfd_sim["IFO_v2"].copy()
    zfd_sim.loc[mask_comuna, "IFO_sim"] = (
        zfd_sim.loc[mask_comuna, "IFO_v2"] + delta
    ).clip(lower=0.0)

    zfd_sim["IDH_sim"]  = zfd_sim["IFO_sim"]  - (B0 + B1 * zfd_sim["IDS"])
    zfd_sim["IPSS_sim"] = zfd_sim["IDS"] * zfd_sim["IFO_sim"]

    # Zonas que salen de ZFD (IDH_sim ≤ 0) DENTRO de la comuna intervenida
    intervenidas  = zfd_sim[mask_comuna]
    n_intervenidas = len(intervenidas)
    salen         = int((intervenidas["IDH_sim"] <= 0).sum())
    pop_salen     = int(intervenidas.loc[intervenidas["IDH_sim"] <= 0, "n_per"].sum())
    pop_interviene = int(intervenidas["n_per"].sum())

    with col2:
        r1, r2, r3 = st.columns(3)
        r1.metric("Zonas ZFD-A en la comuna", n_intervenidas)
        r2.metric("Zonas que salen de ZFD", salen,
                  delta=f"−{salen} zonas" if salen > 0 else "ninguna")
        r3.metric("Personas rescatadas", f"{pop_salen:,}".replace(",","."),
                  delta=f"{pop_salen/pop_interviene*100:.0f}% de la comuna intervenida" if pop_interviene > 0 else "—")

        if salen == 0 and n_intervenidas > 0:
            idh_min = float(intervenidas["IDH"].min())
            cesfam_necesarios = int(np.ceil(-idh_min / DELTA_IFO_CESFAM))
            st.info(
                f"Con {n_cesfam} CESFAM el IDH no alcanza a cruzar cero en ninguna zona. "
                f"La zona más marginal tiene IDH = +{idh_min:.3f}; "
                f"necesitaría al menos **{cesfam_necesarios} CESFAM** para salir de ZFD."
            )
        elif salen == n_intervenidas:
            st.success(
                f"✅ Todas las zonas ZFD-A de {comuna_sel} salen de la falla doble "
                f"con {n_cesfam} CESFAM. Esto equivale a {pop_salen:,} personas rescatadas.".replace(",",".")
            )
        else:
            st.warning(
                f"{salen} de {n_intervenidas} zonas salen de ZFD. "
                f"Las {n_intervenidas - salen} restantes tienen IDH demasiado alto "
                "para ser rescatadas con esta intervención."
            )

    # ── Gráfico IDH actual vs simulado ───────────────────────────────────────────
    st.divider()
    fig, axes = plt.subplots(1, 2, figsize=(10, 3.5))
    RED, REDP, INK = "#C0392B", "#E8A29A", "#1F2A30"

    for ax, col_idh, title, color in [
        (axes[0], "IDH",     "IDH actual",   RED),
        (axes[1], "IDH_sim", "IDH simulado", REDP),
    ]:
        datos_all    = zfd_sim[col_idh]
        datos_comun  = intervenidas[col_idh] if col_idh == "IDH_sim" else intervenidas["IDH"]
        ax.hist(datos_all, bins=20, color="#D9D9D9", edgecolor="white", lw=0.5, label="Otras comunas")
        ax.hist(datos_comun, bins=10, color=color, edgecolor="white", lw=0.5, alpha=0.9, label=comuna_sel)
        ax.axvline(0, color=INK, lw=1.5, ls="--", alpha=0.7)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("IDH (desajuste homeostático)")
        ax.legend(fontsize=8)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

    # ── Tabla de zonas intervenidas ──────────────────────────────────────────────
    with st.expander(f"Detalle zonas ZFD-A de {comuna_sel} ({n_intervenidas} zonas)"):
        tabla = intervenidas[["ID_ZONA","IDS","IFO_v2","IFO_sim","IDH","IDH_sim","n_per"]].copy()
        tabla["sale_ZFD"] = tabla["IDH_sim"] <= 0
        st.dataframe(
            tabla.sort_values("IDH").set_index("ID_ZONA")
                .style.format({"IDS":"{:.3f}","IFO_v2":"{:.3f}","IFO_sim":"{:.3f}",
                               "IDH":"{:+.3f}","IDH_sim":"{:+.3f}","n_per":"{:.0f}"})
                .background_gradient(subset=["IDH_sim"], cmap="RdYlGn_r")
        )

    # ── Nota metodológica expandible ─────────────────────────────────────────────
    with st.expander("Nota metodológica"):
        st.markdown(f"""
**Calibración ΔIFO = −0,07 por CESFAM**

Estimada como 1/5 de la brecha entre el IFO medio de las zonas ZFD-A (0,670) y el
IFO medio de las zonas LL (0,343) del Gran Santiago. Asume que 5 CESFAM de capacidad
promedio (≈ 15.000 inscritos c/u) serían suficientes para cerrar el déficit de
accesibilidad potencial de una zona típica ZFD-A.

**Supuestos y limitaciones**
- La demanda no se redistribuye (la población no cambia de CESFAM al agregar uno nuevo).
- El nuevo establecimiento opera con la capacidad promedio de la red pública existente.
- El efecto se aplica a todas las zonas de la comuna; en la realidad depende del radio
  2SFCA (1.500 m) del establecimiento.
- Los coeficientes OLS están congelados: β₀ = {B0}, β₁ = {B1}.
- IFO v2 captura **accesibilidad potencial**, no utilización real ni calidad de atención.

**Para citar:** IPSS v2 = IDS × IFO v2 · ZFD = LISA HH AND IDH > 0 · Moran's I = 0,3776 (p = 0,001)
""")

except FileNotFoundError:
    st.error("Archivo `data/zonas.parquet` no encontrado.")
    st.code("Ejecuta preparar_datos_simulador.py para generar el archivo.")
