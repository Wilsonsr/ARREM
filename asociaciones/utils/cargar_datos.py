import pandas as pd
import streamlit as st

@st.cache_data
def cargar_datos(ruta_archivo):
    """Carga datos desde un archivo Excel y devuelve un DataFrame de pandas."""

    if ruta_archivo is not None:
        return pd.read_excel(ruta_archivo)
    return None