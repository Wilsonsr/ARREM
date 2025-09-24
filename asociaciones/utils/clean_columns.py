import pandas as pd

def limpiar_columnas(df: pd.DataFrame):
    df2 = df.copy()
    cols_originales = list(df2.columns)
    df2.columns = (df2.columns
                     .str.strip()
                     .str.replace(r"\s+", "_", regex=True)
                     .str.replace(r"[^\w]", "", regex=True))
    mapping = dict(zip(cols_originales, df2.columns))
    return df2, mapping

