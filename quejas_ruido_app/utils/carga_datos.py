import pandas as pd
import streamlit as st

COLUMNAS_OBLIGATORIAS = ["x", "y", "Fecha_Queja"]

COLUMNAS_OPCIONALES = [
    "Direccion_Fuente", "Dirección_Fuente",
    "Razon_Social_Emisor",
    "Localidad_Fuente",
    "Nombre_UPZ_Fuente",
    "Barrio_Fuente",
    "Motivo_Queja",
    "Radicado",
]

# Bounding box amplio de Bogotá y sabana (lat, lon en WGS84).
# Sirve para descartar coordenadas mal geocodificadas (p. ej. puntos que
# caen en otro país por errores del geocodificador o de digitación).
LAT_MIN, LAT_MAX = 3.5, 5.5
LON_MIN, LON_MAX = -74.7, -73.5


@st.cache_data(show_spinner="Leyendo archivo de quejas...")
def cargar_quejas(archivo) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Lee el Excel de quejas y separa filas con coordenadas válidas de las descartadas.

    Devuelve (df_validas, df_descartadas). df_descartadas incluye las filas sin
    coordenadas numéricas o con coordenadas fuera del rango esperado para Bogotá,
    junto con el motivo del descarte en la columna 'motivo_descarte'.
    """
    df = pd.read_excel(archivo)

    faltantes = [c for c in COLUMNAS_OBLIGATORIAS if c not in df.columns]
    if faltantes:
        raise ValueError(
            "El archivo no tiene las columnas obligatorias: " + ", ".join(faltantes)
        )

    df = df.copy()
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df["Fecha_Queja"] = pd.to_datetime(df["Fecha_Queja"], errors="coerce")

    sin_coords = df["x"].isna() | df["y"].isna()
    fuera_de_rango = (
        ~df["x"].between(LAT_MIN, LAT_MAX) | ~df["y"].between(LON_MIN, LON_MAX)
    )

    descartadas = df[sin_coords | (fuera_de_rango & ~sin_coords)].copy()
    descartadas["motivo_descarte"] = "Sin coordenadas x/y"
    descartadas.loc[~sin_coords & fuera_de_rango, "motivo_descarte"] = (
        "Coordenadas fuera del rango esperado para Bogotá"
    )

    validas = df[~sin_coords & ~fuera_de_rango].reset_index(drop=True)

    return validas, descartadas.reset_index(drop=True)


def columna_direccion(df: pd.DataFrame) -> str | None:
    for nombre in ("Direccion_Fuente", "Dirección_Fuente"):
        if nombre in df.columns:
            return nombre
    return None
