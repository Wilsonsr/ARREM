import streamlit as st
import pandas as pd
import numpy as np
from io import BytesIO
import plotly.graph_objects as go
from statsmodels.tsa.holtwinters import ExponentialSmoothing

st.set_page_config(page_title="Proyección Enfermería por Densidad", layout="wide")
st.title("Proyección de Matriculados, Graduados y Nuevos Profesionales en Enfermería")

# Parámetros de usuario
st.sidebar.header("🎯 Parámetros de Proyección")
densidad_objetivo = st.sidebar.slider("👩‍⚕️ Densidad deseada (enfermeros por 10.000 habitantes en 2035)", 15.0, 30.0, 20.0, 0.5)
tasa_graduacion = st.sidebar.slider("🎓 Tasa de graduación (matriculados que se gradúan luego de 4 años)", 0.5, 1.0, 0.8, 0.01)
tasa_cotizacion = st.sidebar.slider("📈 Tasa de graduados que comienzan a cotizar", 0.5, 1.0, 0.9, 0.01)
base_exponencial = st.sidebar.slider("📊 Base de distribución exponencial (2032–2035)", 1.00, 1.30, 1.05, 0.01)

# Cargar datos
archivo_csv = "C:/Users/wsand/Dropbox/MINSALUD/2025/Julio/medicina_graduados_primer_curso/data_enfermeria_graduado.csv"
df = pd.read_csv(archivo_csv)
df.columns = ['Anio', 'Poblacion', 'Matriculados', 'Graduados', 'Medicos_Totales',
              'Poblacion_y', 'Densidad_Medicos', 'Variacion_Medicos', 'Variacion_Porc_Medicos']
df = df.sort_values('Anio').reset_index(drop=True)

# Proyección 2024–2025
if 2023 in df['Anio'].values:
    mat_2023 = df.loc[df['Anio'] == 2023, 'Matriculados'].values[0]
    pob_2023 = df.loc[df['Anio'] == 2023, 'Poblacion'].values[0]
    df = pd.concat([df, pd.DataFrame({'Anio': [2024, 2025]})], ignore_index=True)
    df.loc[df['Anio'] == 2024, 'Matriculados'] = mat_2023 * 1.02
    df.loc[df['Anio'] == 2025, 'Matriculados'] = mat_2023 * (1.02**2)
    df.loc[df['Anio'] == 2024, 'Poblacion'] = pob_2023 * 1.01
    df.loc[df['Anio'] == 2025, 'Poblacion'] = pob_2023 * (1.01**2)

# Extender hasta 2035
df = pd.concat([df, pd.DataFrame({'Anio': list(range(df['Anio'].max() + 1, 2036))})], ignore_index=True)
df = df.drop_duplicates('Anio').sort_values('Anio').reset_index(drop=True)

# Asegurar datos desde 2026
if df['Anio'].min() > 2026:
    df = pd.concat([pd.DataFrame({'Anio': list(range(2026, df['Anio'].min()))}), df], ignore_index=True)
    df = df.sort_values('Anio').reset_index(drop=True)

# Cálculo de graduados y nuevos profesionales
df['Cohorte'] = df['Matriculados'].shift(4)
df['Graduados_Proyectados'] = np.where(df['Anio'] >= 2024, df['Cohorte'] * tasa_graduacion, df['Graduados'])
df['Nuevos_Medicos'] = np.where(df['Anio'] >= 2025, df['Graduados_Proyectados'] * tasa_cotizacion, np.nan).round()

# Acumulado
df['Medicos_Acumulados'] = np.nan
df.loc[df['Anio'] == 2029, 'Medicos_Acumulados'] = 92681
df['Poblacion'] = df['Poblacion'].ffill().bfill()

# Meta
poblacion_2035 = df.loc[df['Anio'] == 2035, 'Poblacion'].values[0]
medicos_necesarios = int((densidad_objetivo / 10000) * poblacion_2035)
medicos_faltantes = max(0, medicos_necesarios - 92681)

# Distribución entre 2030 y 2035
def distribuir(meta, anios, base):
    pesos = np.array([base**i for i in range(len(anios))])
    pesos = pesos / pesos.sum()
    dist = {anio: int(np.floor(meta * peso)) for anio, peso in zip(anios, pesos)}
    dist[anios[-1]] += meta - sum(dist.values())
    return dist

anios_futuros = [2030, 2031, 2032, 2033, 2034, 2035]
nuevos_medicos = distribuir(medicos_faltantes, anios_futuros, base_exponencial)

for anio in anios_futuros:
    df.loc[df['Anio'] == anio, 'Nuevos_Medicos'] = nuevos_medicos[anio]
    grad = nuevos_medicos[anio] / tasa_cotizacion
    df.loc[df['Anio'] == anio, 'Graduados_Proyectados'] = grad
    df.loc[df['Anio'] == anio - 4, 'Matriculados'] = grad / tasa_graduacion

for i, row in df.iterrows():
    if row['Anio'] >= 2030:
        df.at[i, 'Medicos_Acumulados'] = df.at[i - 1, 'Medicos_Acumulados'] + row['Nuevos_Medicos']

# Holt-Winters
df_hw = df.copy()
df_hist = df_hw[df_hw['Anio'] <= 2023].dropna(subset=['Matriculados'])
modelo_hw = ExponentialSmoothing(df_hist['Matriculados'], trend='add', seasonal=None)
ajuste_hw = modelo_hw.fit()
pred_hw = ajuste_hw.forecast(8)
df_hw['Matriculados_HW'] = np.nan
df_hw.loc[df_hw['Anio'].between(2024, 2031), 'Matriculados_HW'] = pred_hw.values

# Comparación 2026–2029
df_comp = pd.merge(df[['Anio', 'Matriculados']], df_hw[['Anio', 'Matriculados_HW']], on='Anio', how='inner')
df_comp['Diferencia'] = df_comp['Matriculados'] - df_comp['Matriculados_HW']
df_dif = df_comp[df_comp['Anio'].between(2026, 2031)]
diferencia_total = int(df_dif['Diferencia'].sum())

# Gráfico principal ajustado
fig = go.Figure()

# Matriculados
df_matriculados = df[~df['Matriculados'].isna()]
fig.add_trace(go.Scatter(x=df_matriculados['Anio'], y=df_matriculados['Matriculados'],
                         mode='lines+markers', name='Matriculados', line=dict(color='red')))

# Graduados
df_graduados = df[~df['Graduados_Proyectados'].isna()]
fig.add_trace(go.Scatter(x=df_graduados['Anio'], y=df_graduados['Graduados_Proyectados'],
                         mode='lines+markers', name='Graduados', line=dict(color='green')))

# Nuevos Enfermeros
df_nuevos = df[~df['Nuevos_Medicos'].isna()]
fig.add_trace(go.Scatter(x=df_nuevos['Anio'], y=df_nuevos['Nuevos_Medicos'],
                         mode='lines+markers', name='Nuevos Enfermeros', line=dict(color='blue')))

# Holt-Winters
df_hw_valid = df_hw[~df_hw['Matriculados_HW'].isna()]
fig.add_trace(go.Scatter(x=df_hw_valid['Anio'], y=df_hw_valid['Matriculados_HW'],
                         mode='lines+markers', name='Matriculados HW', line=dict(color='orange', dash='dash')))

# Anotaciones de diferencia
for _, row in df_dif.iterrows():
    fig.add_annotation(
        x=row['Anio'],
        y=row['Matriculados'],
        text=f"Δ={int(row['Diferencia']):+}",
        showarrow=True,
        arrowhead=2,
        arrowsize=1,
        arrowwidth=1,
        arrowcolor="gray",
        ax=0,
        ay=-40,
        font=dict(size=12, color="crimson"),
        bgcolor="white",
        bordercolor="crimson",
        borderwidth=1
    )

fig.update_layout(
    title="📊 Proyección de Matriculados, Graduados y Nuevos Profesionales en Enfermería",
    xaxis_title="Año",
    yaxis_title="Número de Personas",
    height=600,
    yaxis=dict(tickformat=",d"),
    shapes=[
        dict(type="line", x0=2026, x1=2026, y0=0, y1=max(df[['Matriculados', 'Graduados_Proyectados', 'Nuevos_Medicos']].max()),
             line=dict(color="gray", dash="dot"), xref='x', yref='y'),
        dict(type="line", x0=2032, x1=2032, y0=0, y1=max(df[['Matriculados', 'Graduados_Proyectados', 'Nuevos_Medicos']].max()),
             line=dict(color="gray", dash="dot"), xref='x', yref='y')
    ]
)
st.plotly_chart(fig, use_container_width=True)

# Mensajes
st.markdown(f"""
### 🧮 Enfermeros requeridos en 2035 para alcanzar {densidad_objetivo} por 10.000 hab:
### 👉 **{medicos_necesarios:,}** necesarios en total
""")

mensaje_dif = (
    f"✅ Entre 2026 y 2031, se proyectaron **{diferencia_total:,}** matriculados **adicionales** respecto al modelo natural (Holt-Winters)."
    if diferencia_total > 0 else
    f"⚠️ Entre 2026 y 2029, hay **{abs(diferencia_total):,}** matriculados **menos** que los esperados según Holt-Winters."
)
st.markdown(f"### 📌 Diferencia acumulada 2026–2031:\n{mensaje_dif}")

# Tabla comparativa
st.subheader("📊 Comparación año a año (2026–2031)")
st.dataframe(df_dif.round(0))

# Tabla general
st.subheader("📋 Tabla de resultados")
st.dataframe(df[['Anio', 'Matriculados', 'Graduados_Proyectados', 'Nuevos_Medicos', 'Medicos_Acumulados']].round(0))

# Botón de descarga
def to_excel_bytes(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()

st.download_button(
    label="📥 Descargar Excel",
    data=to_excel_bytes(df),
    file_name='proyeccion_enfermeria_densidad.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
