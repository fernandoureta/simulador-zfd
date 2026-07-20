# -*- coding: utf-8 -*-
"""Capa 2 — Ficha de indicadores por zona censal."""
import streamlit as st
import geopandas as gpd
import pandas as pd
import numpy as np
import os

st.set_page_config(page_title="Detalle por zona", page_icon="🔍", layout="centered",
                   initial_sidebar_state="collapsed")
st.title("🔍 Ficha de zona censal")

DATA_DIR  = os.path.join(os.path.dirname(__file__), "..", "data")
B0, B1    = 0.9640, -1.0213
RED_MAX   = 0.10   # reducción IFO de un CESFAM en su centroide exacto

def dist_m(lat1, lon1, lat2, lon2):
    """Distancia aproximada en metros (error < 0.2% en Gran Santiago)."""
    dlat = (np.asarray(lat2) - lat1) * 111_320
    dlon = (np.asarray(lon2) - lon1) * 111_320 * 0.832
    return np.sqrt(dlat**2 + dlon**2)

@st.cache_data
def cargar():
    zonas = gpd.read_parquet(os.path.join(DATA_DIR, "zonas.parquet"))
    estab = pd.read_parquet(os.path.join(DATA_DIR, "establecimientos.parquet"))
    return zonas, estab

try:
    df, estab = cargar()

    # KPIs globales
    n_zfd    = int(df["tipo"].isin(["ZFD-A","ZFD-B"]).sum())
    pop_zfd  = int(df[df["tipo"].isin(["ZFD-A","ZFD-B"])]["n_per"].sum())
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Zonas Gran Santiago", f"{len(df):,}".replace(",","."))
    col2.metric("Zonas ZFD",           f"{n_zfd}")
    col3.metric("Personas en ZFD",     f"{pop_zfd:,}".replace(",","."))
    col4.metric("% Gran Santiago",     f"{pop_zfd/df['n_per'].sum()*100:.1f}%")

    st.divider()

    # Selector
    comunas = sorted(df["COMUNA"].dropna().unique())
    c1, c2  = st.columns([1, 3])
    with c1:
        comuna_sel = st.selectbox("Comuna", comunas)
        zonas_com  = df[df["COMUNA"] == comuna_sel].sort_values("ID_ZONA")
        zona_id    = st.selectbox("Zona censal (ID_ZONA)", zonas_com["ID_ZONA"].tolist())

    zona = df[df["ID_ZONA"] == zona_id].iloc[0]
    tipo = zona["tipo"]
    ICON = {"ZFD-A":"🔴","ZFD-B":"🟠","LL":"🔵","Resto":"⚪"}

    with c2:
        st.markdown(f"### {ICON.get(tipo,'⚫')} {tipo} — zona {int(zona_id)} · {zona['COMUNA']}")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("IDS",     f"{zona['IDS']:.3f}",    help="Vulnerabilidad social (0–1).")
        m2.metric("IFO v2",  f"{zona['IFO_v2']:.3f}", help="Fricción de acceso a red pública (0–1).")
        m3.metric("IPSS v2", f"{zona['IPSS_v2']:.3f}",help="Presión sobre el sistema (IDS × IFO).")
        m4.metric("IDH",     f"{zona['IDH']:+.3f}",   help="Desajuste homeostático: IFO_real − IFO_esperado.")

        ifo_esp = B0 + B1 * float(zona["IDS"])
        st.caption(
            f"IFO esperado = {B0} − {abs(B1)} × {zona['IDS']:.3f} = **{ifo_esp:.3f}**  "
            f"→  IDH = {zona['IFO_v2']:.3f} − {ifo_esp:.3f} = **{zona['IDH']:+.3f}**"
        )

        # ── Diagnóstico homeostático ─────────────────────────────────────────
        if tipo == "ZFD-A":
            idh_val = float(zona["IDH"])
            cesfam_n = max(1, int(np.ceil(idh_val / RED_MAX)))
            st.error(
                f"⚠️ **Zona de Falla Doble.** El sistema entrega **{idh_val:.3f} puntos menos "
                f"de acceso** del que su tendencia predice.  \n"
                f"Requiere **{cesfam_n} CESFAM** nuevos en esta zona para cruzar el umbral "
                f"homeostático (ΔIFO = −{RED_MAX:.2f} por CESFAM a distancia cero)."
            )
        elif tipo == "ZFD-B":
            st.warning(
                "🟠 **Red pública ausente por sustitución privada.** IFO alto por falta "
                "de establecimientos públicos, no por distancia. La población usa ISAPRE."
            )
        elif tipo == "LL":
            st.success(
                f"✅ **Homeostasis exitosa.** El sistema entrega "
                f"**{abs(zona['IDH']):.3f} puntos más de acceso** del que predice — "
                "la red compensa la vulnerabilidad."
            )
        else:
            st.info("Sin patrón espacial significativo (NS).")

        st.markdown(f"""
| | |
|---|---|
| Categoría LISA | `{zona['lisa_cat']}` |
| Tipo ZFD | **{tipo}** |
| Población | {int(zona['n_per']):,} personas |
| Clúster ZFD | {"Clúster #" + str(int(zona['comp_zfd'])+1) if zona['comp_zfd'] >= 0 else "—"} |
""".replace(",","."))

        # ── Establecimientos que cubren esta zona ────────────────────────────
        zona_lat, zona_lon = float(zona["lat"]), float(zona["lon"])
        estab_cubre = estab[estab["tipo_grupo"] != "otro"].copy()
        estab_cubre["dist_m"] = dist_m(zona_lat, zona_lon,
                                       estab_cubre["Latitud"].values,
                                       estab_cubre["Longitud"].values)
        dentro = estab_cubre[estab_cubre["dist_m"] <= estab_cubre["radio_m"]].sort_values("dist_m")

        GRUPOS_LABEL = {"hospital":"🏥 Hospital","primaria":"🏡 Primaria","urgencia":"🚨 Urgencia"}
        st.markdown("**Red pública que cubre esta zona:**")
        if len(dentro) == 0:
            st.warning("Ningún establecimiento público dentro de su radio de atención.")
        else:
            for grp, sub in dentro.groupby("tipo_grupo"):
                label = GRUPOS_LABEL.get(grp, grp)
                with st.expander(f"{label} — {len(sub)} establecimiento(s)"):
                    st.dataframe(
                        sub[["EstablecimientoGlosa","dist_m"]].rename(
                            columns={"EstablecimientoGlosa":"Establecimiento","dist_m":"Distancia (m)"}
                        ).assign(**{"Distancia (m)": lambda d: d["Distancia (m)"].round(0).astype(int)})
                        .reset_index(drop=True)
                    )

    st.divider()
    st.subheader(f"Todas las zonas de {comuna_sel}")
    cols_show = ["ID_ZONA","tipo","IDS","IFO_v2","IPSS_v2","IDH","lisa_cat","n_per"]
    st.dataframe(
        zonas_com[cols_show].set_index("ID_ZONA")
            .style.format({"IDS":"{:.3f}","IFO_v2":"{:.3f}","IPSS_v2":"{:.3f}",
                           "IDH":"{:+.3f}","n_per":"{:.0f}"})
            .background_gradient(subset=["IDH"], cmap="RdYlGn_r")
    )

except FileNotFoundError as e:
    st.error(f"Archivo no encontrado: {e}")
    st.code("Ejecuta preparar_datos_simulador.py para generar los archivos de datos.")
