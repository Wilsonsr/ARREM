from pathlib import Path

import geopandas as gpd
import pandas as pd
import streamlit as st

RUTA_ZONAS = Path(__file__).resolve().parent.parent / "data" / "zonas_rumba_extendida.geojson"
CRS_GEOGRAFICO = "EPSG:4326"
CRS_METRICO = "EPSG:3116"  # MAGNA-SIRGAS Bogotá, distancias en metros


@st.cache_data(show_spinner=False)
def cargar_zonas() -> gpd.GeoDataFrame:
    zonas = gpd.read_file(RUTA_ZONAS)
    if zonas.crs is None:
        zonas = zonas.set_crs(CRS_GEOGRAFICO)
    return zonas.to_crs(CRS_GEOGRAFICO)


def ubicar_quejas(
    df: pd.DataFrame,
    zonas: gpd.GeoDataFrame,
    col_lat: str = "x",
    col_lon: str = "y",
) -> gpd.GeoDataFrame:
    """Cruza cada queja con las zonas de rumba extendida.

    Agrega: zona_rumba (si cae dentro de una o más zonas), dentro_zona_rumba,
    zona_mas_cercana y distancia_m (0 cuando el punto ya está dentro de una zona).
    """
    puntos = gpd.GeoDataFrame(
        df.copy(),
        geometry=gpd.points_from_xy(df[col_lon], df[col_lat]),
        crs=CRS_GEOGRAFICO,
    )

    cruce = gpd.sjoin(puntos, zonas[["zona", "geometry"]], how="left", predicate="intersects")
    zona_por_punto = cruce.groupby(level=0)["zona"].apply(
        lambda s: "; ".join(dict.fromkeys(v for v in s if pd.notna(v)))
    )
    puntos["zona_rumba"] = zona_por_punto.reindex(puntos.index).replace("", None)
    puntos["dentro_zona_rumba"] = puntos["zona_rumba"].notna()

    zonas_m = zonas.to_crs(CRS_METRICO)
    puntos_m = puntos.to_crs(CRS_METRICO)

    zona_cercana, distancia_m = [], []
    for geom in puntos_m.geometry:
        distancias = zonas_m.geometry.distance(geom)
        idx_min = distancias.idxmin()
        zona_cercana.append(zonas_m.loc[idx_min, "zona"])
        distancia_m.append(round(float(distancias.min()), 1))

    puntos["zona_mas_cercana"] = zona_cercana
    puntos["distancia_m"] = distancia_m

    return puntos


def clasificar_estado(puntos: gpd.GeoDataFrame, buffer_m: float) -> pd.Series:
    """Clasifica cada queja en 'Dentro de zona', 'Cerca (<= buffer)' o 'Fuera de zona'."""
    condiciones = [
        puntos["dentro_zona_rumba"],
        puntos["distancia_m"] <= buffer_m,
    ]
    return pd.Series(
        [
            "Dentro de zona" if dentro else ("Cerca de zona" if cerca else "Fuera de zona")
            for dentro, cerca in zip(*condiciones)
        ],
        index=puntos.index,
    )
