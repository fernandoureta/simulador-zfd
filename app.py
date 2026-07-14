# -*- coding: utf-8 -*-
"""
Simulador Territorial ZFD
Punto de entrada principal — muestra portada y navegación.
"""
import streamlit as st

st.set_page_config(
    page_title="Simulador Territorial ZFD",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Simulador Territorial ZFD")
st.subheader("La Topografía de la Exclusión en Salud · Región Metropolitana")

st.markdown("""
Este simulador visualiza las **Zonas de Falla Doble (ZFD)** del Gran Santiago:
territorios donde la vulnerabilidad social alta se combina con acceso deficiente
a la red pública de salud.

---

### Capas disponibles

| Página | Descripción |
|--------|-------------|
| 🗺️ Mapa 3D | Visualización geoespacial 3D con intensidad IPSS por zona censal |
| 🔍 Detalle por zona | Indicadores IDS, IFO, IPSS e IDH para cualquier zona del Gran Santiago |
| ⚙️ Simulador de intervención | Proyecta el impacto de agregar establecimientos de salud en zonas ZFD |

---

**Metodología:** IPSS v2 = IDS × IFO v2  ·  ZFD = LISA HH AND IDH > 0
Moran's I = 0,3776 (p = 0,001)  ·  r(IDS, IFO) = −0,491 (p < 0,001)
""")

st.info("Usa el menú lateral para navegar entre las tres capas del simulador.")
