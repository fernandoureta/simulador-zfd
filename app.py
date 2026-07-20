# -*- coding: utf-8 -*-
import streamlit as st

st.set_page_config(
    page_title="ZFD · Gran Santiago",
    page_icon="🗺️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

pg = st.navigation([
    st.Page("pages/inicio.py",          title="INICIO",            icon="🏠", default=True),
    st.Page("pages/02_detalle_zona.py", title="DETALLES POR ZONA", icon="🔍"),
    st.Page("pages/03_simulador.py",    title="SIMULADOR",         icon="⚙️"),
])
pg.run()
