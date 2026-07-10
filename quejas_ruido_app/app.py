import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from utils.carga_datos import cargar_quejas, columna_direccion, vista_segura
from utils.geoespacial import cargar_zonas, clasificar_estado, ubicar_quejas

COLOR_ESTADO = {
    "Dentro de zona": "green",
    "Cerca de zona": "orange",
    "Fuera de zona": "red",
}

st.set_page_config(page_title="Quejas de Ruido vs. Zonas de Rumba", layout="wide")
st.title("🔊 Quejas de ruido vs. zonas de rumba extendida")

with st.expander("ℹ️ ¿Cómo se usa esta app?", expanded=False):
    st.markdown(
        """
        1. Sube el Excel acumulado de quejas de ruido (el mismo formato que se diligencia en campo).
        2. La app ubica cada queja sobre las 29 zonas de rumba extendida y calcula:
           - si la queja quedó **dentro** de una zona,
           - la **zona más cercana** y la **distancia** en metros cuando quedó fuera,
           - filtros por **fecha**, **localidad** y **zona**.
        3. Revisa el mapa y la tabla, y descarga el resultado en CSV si lo necesitas.

        **Columnas mínimas que debe traer el archivo:** `x` (latitud), `y` (longitud) y `Fecha_Queja`.
        """
    )

archivo = st.sidebar.file_uploader("📂 Base de quejas (Excel)", type=["xlsx", "xls"])

if archivo is None:
    st.info("Sube un archivo Excel de quejas en la barra lateral para comenzar.")
    st.stop()

try:
    df, descartadas = cargar_quejas(archivo)
except ValueError as e:
    st.error(str(e))
    st.stop()

if not descartadas.empty:
    st.warning(
        f"⚠️ Se descartaron {len(descartadas)} de {len(descartadas) + len(df)} filas: "
        "sin coordenadas o con coordenadas fuera del rango esperado para Bogotá "
        "(posibles errores de geocodificación)."
    )
    with st.expander(f"Ver las {len(descartadas)} filas descartadas"):
        col_dir_desc = columna_direccion(descartadas)
        cols_desc = [c for c in ["Fecha_Queja", col_dir_desc, "x", "y", "motivo_descarte"] if c and c in descartadas.columns]
        st.dataframe(vista_segura(descartadas[cols_desc]), use_container_width=True)

if df.empty:
    st.warning("El archivo no tiene filas con coordenadas (x, y) válidas dentro de Bogotá.")
    st.stop()

zonas = cargar_zonas()
puntos = ubicar_quejas(df, zonas)

buffer_m = st.sidebar.slider(
    "Distancia máxima para considerar una queja 'cerca' de una zona (metros)",
    min_value=0, max_value=500, value=100, step=10,
)
puntos["estado_zona"] = clasificar_estado(puntos, buffer_m)

st.sidebar.markdown("### Filtros")

fechas_validas = puntos["Fecha_Queja"].dropna()
if not fechas_validas.empty:
    fecha_min, fecha_max = fechas_validas.min().date(), fechas_validas.max().date()
    rango_fechas = st.sidebar.date_input(
        "Rango de Fecha_Queja", value=(fecha_min, fecha_max),
        min_value=fecha_min, max_value=fecha_max,
    )
else:
    rango_fechas = None

estados_sel = st.sidebar.multiselect(
    "Estado frente a la zona", list(COLOR_ESTADO.keys()), default=list(COLOR_ESTADO.keys()),
)

if "Localidad_Fuente" in puntos.columns:
    localidades = sorted(puntos["Localidad_Fuente"].dropna().unique())
    localidades_sel = st.sidebar.multiselect("Localidad", localidades, default=localidades)
else:
    localidades_sel = None

filtrado = puntos[puntos["estado_zona"].isin(estados_sel)]

if rango_fechas and len(rango_fechas) == 2:
    inicio, fin = rango_fechas
    filtrado = filtrado[
        filtrado["Fecha_Queja"].dt.date.between(inicio, fin) | filtrado["Fecha_Queja"].isna()
    ]

if localidades_sel is not None:
    filtrado = filtrado[filtrado["Localidad_Fuente"].isin(localidades_sel)]

col1, col2, col3, col4 = st.columns(4)
col1.metric("Quejas filtradas", len(filtrado))
col2.metric("Dentro de zona", int((filtrado["estado_zona"] == "Dentro de zona").sum()))
col3.metric("Cerca de zona", int((filtrado["estado_zona"] == "Cerca de zona").sum()))
col4.metric("Fuera de zona", int((filtrado["estado_zona"] == "Fuera de zona").sum()))

st.subheader("Mapa")
if filtrado.empty:
    st.warning("No hay quejas que cumplan los filtros seleccionados.")
else:
    centro = zonas.geometry.union_all().centroid
    mapa = folium.Map(location=[centro.y, centro.x], zoom_start=12, tiles="cartodbpositron")

    folium.GeoJson(
        zonas,
        name="Zonas de rumba extendida",
        style_function=lambda f: {"color": "#7B3FE4", "weight": 2, "fillColor": "#7B3FE4", "fillOpacity": 0.12},
        tooltip=folium.GeoJsonTooltip(fields=["zona"], aliases=["Zona:"]),
    ).add_to(mapa)

    col_dir = columna_direccion(filtrado)
    for _, fila in filtrado.iterrows():
        partes = []
        if col_dir:
            partes.append(f"<b>{fila[col_dir]}</b>")
        if "Razon_Social_Emisor" in filtrado.columns:
            partes.append(str(fila["Razon_Social_Emisor"]))
        partes.append(f"Fecha queja: {fila['Fecha_Queja'].date() if pd.notna(fila['Fecha_Queja']) else 's/d'}")
        partes.append(f"Estado: {fila['estado_zona']}")
        if fila["dentro_zona_rumba"]:
            partes.append(f"Zona: {fila['zona_rumba']}")
        else:
            partes.append(f"Zona más cercana: {fila['zona_mas_cercana']} ({fila['distancia_m']:.0f} m)")

        folium.CircleMarker(
            location=[fila["x"], fila["y"]],
            radius=6,
            color=COLOR_ESTADO[fila["estado_zona"]],
            fill=True,
            fill_opacity=0.85,
            popup=folium.Popup("<br>".join(partes), max_width=300),
        ).add_to(mapa)

    st_folium(mapa, width=None, height=550, returned_objects=[])

st.subheader("Tabla de resultados")
columnas_tabla = [c for c in [
    "Fecha_Queja", columna_direccion(filtrado), "Razon_Social_Emisor",
    "Localidad_Fuente", "Nombre_UPZ_Fuente", "estado_zona",
    "zona_rumba", "zona_mas_cercana", "distancia_m", "x", "y",
] if c and c in filtrado.columns]

st.dataframe(vista_segura(filtrado[columnas_tabla]), use_container_width=True)

csv = filtrado.drop(columns="geometry").to_csv(index=False).encode("utf-8-sig")
st.download_button("📥 Descargar resultados (CSV)", data=csv, file_name="quejas_ubicadas.csv", mime="text/csv")
