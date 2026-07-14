# -*- coding: utf-8 -*-
"""
Capa 2 — Detalle por zona
Ficha de indicadores para cualquier zona censal del Gran Santiago.
"""
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Detalle por zona", page_icon="🔍", layout="wide")
st.title("🔍 Detalle por zona censal")

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

    comunas = sorted(df["COMUNA"].unique())
    col1, col2 = st.columns([1, 2])

    with col1:
        comuna_sel = st.selectbox("Comuna", comunas)
        zonas_com  = df[df["COMUNA"] == comuna_sel].sort_values("ID_ZONA")
        zona_sel   = st.selectbox("Zona censal (ID_ZONA)", zonas_com["ID_ZONA"].tolist())

    zona = df[df["ID_ZONA"] == zona_sel].iloc[0]

    with col2:
        tipo = zona["tipo"]
        COLOR = {"ZFD-A":"🔴","ZFD-B":"🟠","LL":"🔵","Resto":"⚪"}
        st.markdown(f"### {COLOR.get(tipo,'⚫')} {tipo} — {zona['COMUNA']}")

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("IDS", f"{zona['IDS']:.3f}", help="Vulnerabilidad social (0–1)")
        c2.metric("IFO v2", f"{zona['IFO_v2']:.3f}", help="Fricción de acceso (0–1)")
        c3.metric("IPSS v2", f"{zona['IPSS_v2']:.3f}", help="Índice de presión sobre el sistema (IDS × IFO)")
        c4.metric("IDH", f"{zona['IDH']:+.3f}", help="Desajuste homeostático: IFO_real − IFO_esperado")

        st.markdown(f"""
| Variable | Valor |
|---|---|
| LISA clúster | `{zona['lisa_cat']}` |
| Tipo ZFD | **{tipo}** |
| ID_ZONA | {int(zona['ID_ZONA'])} |
        """)

        if tipo in ("ZFD-A", "ZFD-B"):
            st.error(f"⚠️ Zona de Falla Doble — alta vulnerabilidad Y acceso deficiente a red pública.")
        elif tipo == "LL":
            st.success("✅ Red compensa — clúster LL (baja vulnerabilidad O buen acceso relativo).")
        else:
            st.info("Sin patrón espacial significativo.")

    st.divider()
    st.subheader(f"Todas las zonas de {comuna_sel}")
    cols_show = ["ID_ZONA","tipo","IDS","IFO_v2","IPSS_v2","IDH","lisa_cat"]
    st.dataframe(zonas_com[cols_show].set_index("ID_ZONA").style.format("{:.3f}", subset=["IDS","IFO_v2","IPSS_v2","IDH"]))

except FileNotFoundError:
    st.warning("Archivos de datos no encontrados en `data/`.")
