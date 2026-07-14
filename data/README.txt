Coloca aquí los siguientes archivos parquet antes de ejecutar la app:

  ifo_v2_zonal.parquet           <- desde 00 Fuentes de datos/90_derivados_rm/
  lisa_zonal.parquet             <- desde 00 Fuentes de datos/90_derivados_rm/
  censo_zonal_rm_indicadores.parquet  <- desde 00 Fuentes de datos/90_derivados_rm/

Para ejecutar localmente:
  pip install -r requirements.txt
  streamlit run app.py

Para deploy en Streamlit Cloud:
  1. Sube este repositorio a GitHub
  2. Conecta el repo en https://share.streamlit.io
  3. Archivo principal: app.py
  NOTA: los parquet son datos sensibles — no los incluyas en el repo público.
  Usa st.secrets o un bucket S3/GCS para los datos en producción.
