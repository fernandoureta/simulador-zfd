# -*- coding: utf-8 -*-
"""Capa 2 — Ficha de indicadores por zona censal."""
import streamlit as st
import geopandas as gpd
import os

st.set_page_config(page_title="Detalle por zona", page_icon="🔍", layout="wide")
st.title("🔍 Ficha de zona censal")

DATA_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "zonas.parquet")

@st.cache_data
def cargar():
    return gpd.read_parquet(DATA_PATH)

B0, B1 = 0.9640, -1.0213

try:
    df = cargar()

    # KPIs globales
    n_zfd  = int(df["tipo"].isin(["ZFD-A","ZFD-B"]).sum())
    pop_zfd = int(df[df["tipo"].isin(["ZFD-A","ZFD-B"])]["n_per"].sum())
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
        m1.metric("IDS",     f"{zona['IDS']:.3f}",    help="Vulnerabilidad social (0–1). Más alto = más vulnerable.")
        m2.metric("IFO v2",  f"{zona['IFO_v2']:.3f}", help="Fricción de acceso a red pública (0–1). Más alto = peor acceso.")
        m3.metric("IPSS v2", f"{zona['IPSS_v2']:.3f}",help="Índice de Presión sobre el Sistema (IDS × IFO).")
        m4.metric("IDH",     f"{zona['IDH']:+.3f}",   help="Desajuste homeostático: IFO_real − IFO_esperado (OLS). Positivo = peor de lo predicho.")

        ifo_esp = B0 + B1 * zona["IDS"]
        st.caption(
            f"IFO esperado según la tendencia del sistema: **{ifo_esp:.3f}**  "
            f"→  IDH = {zona['IFO_v2']:.3f} − {ifo_esp:.3f} = **{zona['IDH']:+.3f}**"
        )
        if zona["IDH"] > 0:
            st.error(
                f"El sistema entrega **{zona['IDH']:.3f} puntos menos de acceso** "
                "del que su propia tendencia predice para esta vulnerabilidad."
            )
        else:
            st.success(
                f"El sistema entrega **{abs(zona['IDH']):.3f} puntos más de acceso** "
                "del que predice su tendencia — homeostasis exitosa."
            )

        st.markdown(f"""
| | |
|---|---|
| Categoría LISA | `{zona['lisa_cat']}` |
| Tipo ZFD | **{tipo}** |
| Población | {int(zona['n_per']):,} personas |
| Clúster ZFD | {"Clúster #" + str(int(zona['comp_zfd'])+1) if zona['comp_zfd'] >= 0 else "—"} |
""".replace(",","."))

        if tipo in ("ZFD-A","ZFD-B"):
            st.warning("⚠️ Zona de Falla Doble — alta vulnerabilidad social combinada con acceso deficiente a la red pública.")
        elif tipo == "LL":
            st.success("✅ Acceso concentrado — la red de salud compensa la demanda en esta zona.")
        else:
            st.info("Sin patrón espacial significativo (NS).")

    st.divider()
    st.subheader(f"Todas las zonas de {comuna_sel}")
    cols_show = ["ID_ZONA","tipo","IDS","IFO_v2","IPSS_v2","IDH","lisa_cat","n_per"]
    st.dataframe(
        zonas_com[cols_show].set_index("ID_ZONA")
            .style.format({"IDS":"{:.3f}","IFO_v2":"{:.3f}","IPSS_v2":"{:.3f}","IDH":"{:+.3f}","n_per":"{:.0f}"})
            .background_gradient(subset=["IDH"], cmap="RdYlGn_r")
    )

except FileNotFoundError:
    st.error("Archivo `data/zonas.parquet` no encontrado.")
