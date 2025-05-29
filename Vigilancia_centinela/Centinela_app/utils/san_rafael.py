
import pandas as pd
import numpy as np
from dateutil.relativedelta import relativedelta

# Diccionario de semanas
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

codigos_adicionales = ["A419","C340","C341","C349","C450","C716","D022","D381","D386","D430",
                       "G468","R001","R092","R570","R571","R572","R579","R960","R961","R98X","Z515"]

excluir_codigos = ["I770", "I952", "I970", "I971", "I972", "I978", "I979", "J341", "J342", "J380", "J386", "J690",
                   "J691", "J698", "J700", "J701", "J702", "J703", "J704", "J708", "J709", "J940", "J941", "J942",
                   "J950", "J951", "J952", "J953", "J954", "J955", "J958", "J959", "J986"]

def cargar_datos(file):
    return pd.read_excel(file, skiprows=5)

def filtrar_por_semana(df, semana):
    inicio, fin = semanas_2025[semana]
    df["Fecha Ingreso"] = pd.to_datetime(df["Fecha Ingreso"])
    return df[(df["Fecha Ingreso"] >= inicio) & (df["Fecha Ingreso"] <= fin)]

def filtrar_bogota(df):
    return df[df["Municipio"] == "Bogotá D.C."]

def eliminar_duplicados(df):
    return df.drop_duplicates()

def filtrar_diagnosticos(df):
    df['Codigo CIE10'] = df['Codigo CIE10'].astype(str)
    df['CIE10 Egreso'] = df['CIE10 Egreso'].astype(str).replace('nan', '')
    cond_ing = df['Codigo CIE10'].str.startswith(('I', 'J'))
    cond_egr = df['CIE10 Egreso'].str.startswith(('I', 'J'))
    cond_adic = df['CIE10 Egreso'].isin(codigos_adicionales) & cond_ing
    cond_vacio = (df['CIE10 Egreso'] == '') & cond_ing
    return df[cond_ing | cond_egr | cond_adic | cond_vacio]

def eliminar_duplicados_columnas(df):
    return df.drop_duplicates(subset=['Documento', 'Fecha Ingreso'], keep='last')

def reemplazar_ingreso_por_egreso(df):
    def logic(row):
        i = row['Codigo CIE10'].strip().upper()
        e = row['CIE10 Egreso'].strip().upper()
        if i == e or (i.startswith(('I', 'J')) and not e.startswith(('I', 'J'))):
            return row
        if not i.startswith(('I', 'J')) and e.startswith(('I', 'J')):
            row['Codigo CIE10'] = e
            row["Diagnostico principal de Ingreso"] = row['Diagnostico Egreso']
        return row
    return df.apply(logic, axis=1)

def excluir_codigos_invalidos(df):
    return df[~df['Codigo CIE10'].isin(excluir_codigos) & ~df['CIE10 Egreso'].isin(excluir_codigos)]

def exportar_excel(df, output_path):
    df.to_excel(output_path, index=False)
    return output_path

def procesar_san_rafael(file, semana, output="Base_HUCSR_CONSOLIDADO.xlsx"):
    df = cargar_datos(file)
    df = filtrar_por_semana(df, semana)
    df = filtrar_bogota(df)
    df = eliminar_duplicados(df)
    df = filtrar_diagnosticos(df)
    df = eliminar_duplicados_columnas(df)
    df = reemplazar_ingreso_por_egreso(df)
    df = excluir_codigos_invalidos(df)
    path = exportar_excel(df, output)
    return df, path
