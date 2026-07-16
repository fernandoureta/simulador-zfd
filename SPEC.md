# Simulador Territorial ZFD — Especificación técnica

**Repo:** github.com/fernandoureta/simulador-zfd  
**URL:** https://simulador-zfd-jucq32bgktmgw82xeglshx.streamlit.app/  
**Última actualización:** 2026-07-16

---

## Estructura real del repo (el repo manda, este doc se adapta)

```
simulador-zfd/
├── app.py                          # entrypoint — portada y navegación
├── requirements.txt
├── SPEC.md                         # este archivo
├── data/
│   ├── zonas.parquet               # [NMV] 1636 zonas · 0.3 MB
│   │                               #   geometrías simplif. 44 m + índices + centroides
│   └── establecimientos.parquet   # [NMV] 405 establecimientos GS con lat/lon
│                                   #   26 hospitales · 236 primarias · 99 urgencias
└── pages/                          # Streamlit multipage nativo
    ├── 01_mapa_3d.py               # [NMV] Capa 1 — mapa 3D pydeck
    ├── 02_detalle_zona.py          # [NMV] Capa 2 — ficha + establecimientos
    └── 03_simulador.py             # [NMV] Capa 3 — simulador distancia-decay
```

**Post-feria (EXT):** carpeta `core/` con `optimizer.py` (MCLP greedy),
`graph.py` (centralidades sobre W_queen.npz), `W_queen.npz` (scipy sparse).

---

## Datos verificados

| Archivo | Registros | Tamaño | Columnas clave |
|---|---|---|---|
| `zonas.parquet` | 1.636 zonas | 0.3 MB | ID_ZONA, COMUNA, IDS, IFO_v2, IPSS_v2, IDH, tipo, lat, lon, geometry, comp_zfd |
| `establecimientos.parquet` | 405 establecimientos GS | 0.03 MB | cod, EstablecimientoGlosa, tipo_grupo, Latitud, Longitud, radio_m, reduccion_max |

---

## Núcleo de cálculo

### Constantes OLS (NUNCA se recalculan en la app)
```
B0 = 0.9640   B1 = -1.0213
IDH = IFO_v2 - (B0 + B1 * IDS)
ZFD = (lisa_cat == "HH") AND (IDH > 0)
```

### Grupos 2SFCA y parámetros de reducción

| Grupo | Tipos | Radio | reduccion_max |
|---|---|---|---|
| hospital | Hospital | 5.000 m | 0.15 |
| primaria | CESFAM, CECOSF, COSAM | 1.500 m | 0.10 |
| urgencia | SAPU, SAR | 2.000 m | 0.08 |

### Distance-decay (simulador)
```
ΔIFO(zona i) = reduccion_max × max(0, 1 − dist(i, nuevo) / radio)
```
Calibrado como reducción máxima empírica al agregar 1 establecimiento en el 2SFCA.

### CESFAM necesarios (ficha de zona)
```
N_cesfam = ceil(IDH / 0.10)   # reduccion_max primaria a distancia cero
```

---

## Componentes conexas ZFD (material evaluador, no al póster)

| Clúster | Zonas | Hab. ZFD | % ZFD |
|---|---|---|---|
| 1 | 108 | 379.148 | 32,2% |
| 2 | 63 | 243.837 | 20,7% |
| 3 | 37 | 131.163 | 11,1% |
| 4 | 24 | 90.220 | 7,7% |
| 5 | 21 | 87.282 | 7,4% |
| **Total** | **310 zonas · 23 clústeres** | **1.178.472 hab.** | **top-3 = 64,0%** |

---

## Limitación declarada del modelo

El optimizador (EXT) solo recomienda ubicaciones sobre zonas ZFD-A.
Las zonas ZFD-B (Las Condes, Vitacura, Providencia, Ñuñoa, Lo Barnechea, La Reina)
se excluyen: un establecimiento público allí no atiende demanda real — la población
usa ISAPRE. Que la herramienta se niegue a recomendar el oriente ES la demostración
de que el modelo entiende su propia frontera.

---

## Cronograma NMV (feria 21/07)

| Día | Estado |
|---|---|
| 16 jul (hoy) | ✅ `zonas.parquet` + `establecimientos.parquet` · simulador distancia-decay · ficha CESFAM counter |
| 17–18 jul | Prueba en celular · ajustar vista inicial mapa · UI polish |
| 19 jul | Verificar RAM en Streamlit Cloud · congelar app |
| 20 jul | Imprimir · despertar app · tablet plan D |
| 21 jul (feria) | Despertar app 10:30 · llevar tablet |
