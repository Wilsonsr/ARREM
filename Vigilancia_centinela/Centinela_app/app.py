
import streamlit as st
import pandas as pd
from utils.san_rafael import procesar_san_rafael
# Importar los otros módulos cuando estén listos
# from limpieza_caps_chapinero import procesar_caps
# from limpieza_meissen import procesar_meissen
# from limpieza_kennedy import procesar_kennedy

st.set_page_config(page_title="Vigilancia Centinela", layout="wide")
st.title("📌 Vigilancia Centinela - Cargar y Procesar por Unidad")

# Elegir semana con número y mostrar rango
semanas_2025 = {
    1: ("2024-12-29", "2025-01-04"),
    2: ("2025-01-05", "2025-01-11"),
    3: ("2025-01-12", "2025-01-18"),
    4: ("2025-01-19", "2025-01-25"),
    5: ("2025-01-26", "2025-02-01"),
    6: ("2025-02-02", "2025-02-08"),
    7: ("2025-02-09", "2025-02-15"),
    8: ("2025-02-16", "2025-02-22"),
    9: ("2025-02-23", "2025-03-01"),
    10: ("2025-03-02", "2025-03-08"),
    11: ("2025-03-09", "2025-03-15"),
    12: ("2025-03-16", "2025-03-22"),
    13: ("2025-03-23", "2025-03-29"),
    14: ("2025-03-30", "2025-04-05"),
    15: ("2025-04-06", "2025-04-12"),
    16: ("2025-04-13", "2025-04-19"),
    17: ("2025-04-20", "2025-04-26"),
    18: ("2025-04-27", "2025-05-03"),
    19: ("2025-05-04", "2025-05-10"),
    20: ("2025-05-11", "2025-05-17"),
    21: ("2025-05-18", "2025-05-24"),
    22: ("2025-05-25", "2025-05-31"),
    23: ("2025-06-01", "2025-06-07"),
    24: ("2025-06-08", "2025-06-14"),
    25: ("2025-06-15", "2025-06-21"),
    26: ("2025-06-22", "2025-06-28"),
    27: ("2025-06-29", "2025-07-05"),
    28: ("2025-07-06", "2025-07-12"),
    29: ("2025-07-13", "2025-07-19"),
    30: ("2025-07-20", "2025-07-26"),
    31: ("2025-07-27", "2025-08-02"),
    32: ("2025-08-03", "2025-08-09"),
    33: ("2025-08-10", "2025-08-16"),
    34: ("2025-08-17", "2025-08-23"),
    35: ("2025-08-24", "2025-08-30"),
    36: ("2025-08-31", "2025-09-06"),
    37: ("2025-09-07", "2025-09-13"),
    38: ("2025-09-14", "2025-09-20"),
    39: ("2025-09-21", "2025-09-27"),
    40: ("2025-09-28", "2025-10-04"),
    41: ("2025-10-05", "2025-10-11"),
    42: ("2025-10-12", "2025-10-18"),
    43: ("2025-10-19", "2025-10-25"),
    44: ("2025-10-26", "2025-11-01"),
    45: ("2025-11-02", "2025-11-08"),
    46: ("2025-11-09", "2025-11-15"),
    47: ("2025-11-16", "2025-11-22"),
    48: ("2025-11-23", "2025-11-29"),
    49: ("2025-11-30", "2025-12-06"),
    50: ("2025-12-07", "2025-12-13"),
    51: ("2025-12-14", "2025-12-20"),
    52: ("2025-12-21", "2025-12-27"),
    53: ("2025-12-28", "2026-01-03"),
}

semana = st.number_input("Semana epidemiológica", min_value=1, max_value=53, value=16, step=1)
inicio, fin = semanas_2025.get(semana, ("", ""))
st.caption(f"📅 Semana {semana}: del {inicio} al {fin}")

# Elegir unidad
unidad = st.selectbox("Selecciona unidad centinela", [
    "Seleccione...",
    "San Rafael",
    "CAPS Chapinero",
    "USS Meissen",
    "USS Kennedy"
])

archivo = None
if unidad != "Seleccione...":
    archivo = st.file_uploader(f"Cargar archivo de {unidad}", type=["xlsx"])

# Procesar archivo
if archivo and st.button("Procesar"):
    with st.spinner("Procesando..."):
        if unidad == "San Rafael":
            df, _ = procesar_san_rafael(archivo, semana)
        # elif unidad == "CAPS Chapinero":
        #     df, _ = procesar_caps(archivo, semana)
        # elif unidad == "USS Meissen":
        #     df, _ = procesar_meissen(archivo, semana)
        # elif unidad == "USS Kennedy":
        #     df, _ = procesar_kennedy(archivo, semana)
        else:
            df = pd.DataFrame()

    if not df.empty:
        st.success("✅ Procesamiento completado.")
        st.dataframe(df)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("📥 Descargar CSV", data=csv, file_name=f"{unidad}_semana{semana}.csv")
    else:
        st.warning("No se generaron resultados.")
