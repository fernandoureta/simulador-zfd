# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(
    page_title="ZFD · Gran Santiago",
    page_icon="🗺️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap');

.stApp { font-family: 'Inter', sans-serif; }

/* ── Hero ── */
.zfd-hero { text-align: center; padding: 2rem 0 1.25rem; }

.zfd-kicker {
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: .12em;
    color: #475569;
    margin-bottom: .75rem;
}

.zfd-number {
    font-family: 'Inter', sans-serif;
    font-size: clamp(56px, 15vw, 88px);
    font-weight: 900;
    color: #C0392B;
    letter-spacing: -2px;
    line-height: 1;
    margin: 0;
}

.zfd-unit {
    font-size: clamp(14px, 3.5vw, 18px);
    font-weight: 500;
    color: #94A3B8;
    margin: .5rem 0 0;
}

.zfd-desc {
    font-size: clamp(13px, 3.2vw, 15px);
    color: #CBD5E1;
    line-height: 1.65;
    max-width: 400px;
    margin: 1rem auto 0;
}

/* ── Stats ── */
.stat-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin: 1.5rem 0 1rem;
}

.stat-box {
    background: #0E1223;
    border: 1px solid #1E2D42;
    border-radius: 14px;
    padding: 16px 8px;
    text-align: center;
}

.stat-v {
    font-family: 'JetBrains Mono', monospace;
    font-size: clamp(18px, 5.5vw, 26px);
    font-weight: 700;
    color: #F8FAFC;
    line-height: 1;
}

.stat-l {
    font-size: 10px;
    color: #475569;
    margin-top: 6px;
    text-transform: uppercase;
    letter-spacing: .05em;
    line-height: 1.3;
}

/* ── Legend ── */
.legend-row {
    display: flex;
    gap: 14px;
    justify-content: center;
    flex-wrap: wrap;
    margin: 1rem 0 .5rem;
}
.legend-item { display: flex; align-items: center; gap: 6px; font-size: 12px; color: #94A3B8; }
.ldot { width: 9px; height: 9px; border-radius: 50%; flex-shrink: 0; }

/* ── Nav section label ── */
.nav-label {
    text-align: center;
    font-size: 11px;
    font-weight: 600;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: .1em;
    margin: 1.25rem 0 .6rem;
}
</style>
""", unsafe_allow_html=True)

# ── HERO ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="zfd-hero">
  <div class="zfd-kicker">Gran Santiago · Región Metropolitana</div>
  <div class="zfd-number">1.178.472</div>
  <div class="zfd-unit">personas en Zonas de Falla Doble</div>
  <div class="zfd-desc">
    El 19,2% del Gran Santiago vive donde la alta vulnerabilidad social
    coincide con acceso deficiente a la red pública de salud.
  </div>
</div>
""", unsafe_allow_html=True)

# ── STATS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="stat-row">
  <div class="stat-box">
    <div class="stat-v">19,2%</div>
    <div class="stat-l">Del Gran<br>Santiago</div>
  </div>
  <div class="stat-box">
    <div class="stat-v">310</div>
    <div class="stat-l">Zonas<br>censales</div>
  </div>
  <div class="stat-box">
    <div class="stat-v">23</div>
    <div class="stat-l">Clústeres<br>territoriales</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── LEGEND ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="legend-row">
  <span class="legend-item"><span class="ldot" style="background:#C0392B"></span>ZFD-A · exclusión periférica</span>
  <span class="legend-item"><span class="ldot" style="background:#E8A29A"></span>ZFD-B · sustitución privada</span>
  <span class="legend-item"><span class="ldot" style="background:#2C7FB8"></span>LL · acceso adecuado</span>
</div>
""", unsafe_allow_html=True)

st.divider()

# ── NAVIGATION ────────────────────────────────────────────────────────────────
st.markdown('<div class="nav-label">Explorar</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.page_link("pages/01_mapa_3d.py",       label="🗺️ Mapa 3D",    use_container_width=True)
with col2:
    st.page_link("pages/02_detalle_zona.py",   label="🔍 Por zona",   use_container_width=True)
with col3:
    st.page_link("pages/03_simulador.py",      label="⚙️ Simular",    use_container_width=True)

st.divider()

with st.expander("Metodología"):
    st.markdown("""
**IPSS v2 = IDS × IFO v2** — Índice de Posición en el Sistema de Salud
**ZFD** = LISA HH (Moran's I = 0,3776 · p = 0,001) AND IDH > 0
**IDS** — vulnerabilidad social: hacinamiento, adultos ≥60, discapacidad, jefatura femenina
**IFO v2** — accesibilidad 2SFCA radio diferenciado · r(IDS, IFO) = −0,491
Fuentes: INE Censo 2017 · DEIS MINSAL
""")
