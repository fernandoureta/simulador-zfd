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
import folium
import os

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
    default_idx  = list(comunas_zfda).index("Maipú") if "Maipú" in comunas_zfda else 0
    col1, col2   = st.columns([1, 2])

    with col1:
        comuna_sel = st.selectbox("Comuna de intervención", comunas_zfda, index=default_idx)
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
    decay = np.clip(1 - d / radio, 0, None)  # numpy: a_min=0, no lower=

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

    # ── Mapa de efecto (Folium) ──────────────────────────────────────────────────
    st.subheader("Efecto espacial del establecimiento")

    COLORES_TIPO = {"ZFD-A": "#C0392B", "ZFD-B": "#E8A29A", "LL": "#2C7FB8", "Resto": "#334155"}
    OPACIDAD_TIPO = {"ZFD-A": 0.85, "ZFD-B": 0.75, "LL": 0.55, "Resto": 0.08}
    VERDE = "#27AE60"

    sim["rescued"] = (dentro_radio & (sim["tipo"] == "ZFD-A") & (sim["IDH_sim"] <= 0)).astype(bool)

    def hacer_mapa(mostrar_rescate):
        m = folium.Map(
            location=[new_lat, new_lon],
            zoom_start=12,
            tiles="CartoDB DarkMatter",
            attributionControl=False,
            scrollWheelZoom=False,
        )

        def estilo(feat):
            tipo = feat["properties"]["tipo"]
            rescued = feat["properties"].get("rescued", False)
            if mostrar_rescate and rescued:
                return {"fillColor": VERDE, "fillOpacity": 0.90,
                        "color": "#ffffff", "weight": 0.8}
            return {
                "fillColor": COLORES_TIPO.get(tipo, "#334155"),
                "fillOpacity": OPACIDAD_TIPO.get(tipo, 0.08),
                "color": "transparent", "weight": 0,
            }

        cols_geo = ["geometry", "tipo", "COMUNA", "IPSS_v2", "n_per", "rescued"]
        for tipo in ["Resto", "LL", "ZFD-B", "ZFD-A"]:
            sub = sim[sim["tipo"] == tipo][cols_geo]
            tooltip = None
            if tipo in ("ZFD-A", "ZFD-B"):
                tooltip = folium.GeoJsonTooltip(
                    fields=["COMUNA", "tipo", "IPSS_v2", "n_per"],
                    aliases=["Comuna", "Tipo", "IPSS", "Hab."],
                    localize=True, sticky=False,
                )
            folium.GeoJson(sub, style_function=estilo, tooltip=tooltip).add_to(m)

        folium.Circle(
            location=[new_lat, new_lon], radius=radio,
            color=VERDE, weight=2,
            fill=True, fill_color=VERDE, fill_opacity=0.08,
        ).add_to(m)

        folium.Marker(
            location=[new_lat, new_lon],
            popup=folium.Popup(
                f"<b>Nuevo {cfg['grupo']}</b><br>{comuna_sel}<br>"
                f"Radio: {radio/1000:.1f} km", max_width=180
            ),
            icon=folium.Icon(color="green", icon="plus-sign"),
        ).add_to(m)

        return m

    tab1, tab2 = st.tabs(["📍 Situación actual", "✅ Con intervención"])
    with tab1:
        st.components.v1.html(hacer_mapa(False)._repr_html_(), height=460)
    with tab2:
        st.components.v1.html(hacer_mapa(True)._repr_html_(), height=460)

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
