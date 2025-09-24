import pandas as pd
from utils.cargar_datos import cargar_datos
from utils.clean_columns import limpiar_columnas
import streamlit as st

# ------- App -------
def main():
    st.title("Asociaciones")

    archivo = st.file_uploader("Subir tu archivo de Excel", type=["xlsx", "xls"])
    df = cargar_datos(archivo)

    if df is None:
        st.info("Carga un archivo para continuar.")
        return

    st.subheader("Vista previa (original)")
    st.dataframe(df.head())

    # Limpieza automática
    df_limpio, mapping = limpiar_columnas(df)
    st.session_state["df_limpio"] = df_limpio  # para los pasos siguientes

    st.success("Limpieza de nombres de columnas aplicada automáticamente.")
    with st.expander("Mapeo columnas (antes → después)"):
        st.table(pd.DataFrame({"antes": mapping.keys(), "después": mapping.values()}))

    st.subheader("Vista previa (después de limpieza)")
    st.dataframe(df_limpio.head())

if __name__ == "__main__":
    main()