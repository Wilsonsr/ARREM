import streamlit as st
import pandas as pd
import asyncio
import random
import re
from playwright.async_api import async_playwright

# --------------------------
# FUNCIONES AUXILIARES
# --------------------------
def limpiar_direccion(dir):
    dir = str(dir).upper().strip()
    dir = dir.replace('#', '')
    dir = re.sub(r'[^A-Z0-9\s-]', '', dir)
    dir = dir.replace('CARREAR', 'CARRERA')
    dir = dir.replace('CARERRA', 'CARRERA')
    dir = dir.replace('CRA', 'KR')
    dir = dir.replace('CALLE', 'CL')
    dir = dir.replace('CAL', 'CL')
    dir = dir.replace('CLLE', 'CL')
    dir = dir.replace('CLL', 'CL')
    dir = dir.replace('N.', '')
    dir = re.sub(r'\s+', ' ', dir)
    return dir.strip()

async def iniciar_sesion(playwright):
    browser = await playwright.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto("http://sig.saludcapital.gov.co/geocodificardireccion/")
    await page.fill('#txbUsuario', 'geoUsuario')
    await page.fill('#txbContrasena', 'SDSGeo2015')
    await page.click('#btnIngresar')
    await page.wait_for_timeout(3000)
    return browser, page

async def buscar_direccion(page, direccion):
    await page.fill('#txbDireccion', direccion)
    await page.click('#btnBuscarDireccion')
    await page.wait_for_timeout(3000)

    await page.wait_for_selector('#lblMensajeDireccion', timeout=12000)
    mensaje = await page.locator('#lblMensajeDireccion').inner_text()

    if "Encontrado" not in mensaje:
        raise ValueError(mensaje)

    async def get_text(selector):
        try:
            return (await page.locator(selector).inner_text()).strip()
        except:
            return None

    return (
        await get_text('#lblBarrio'),
        await get_text('#lblUpz'),
        await get_text('#lblLocalidad'),
        await get_text('#lblCoordenadaX'),
        await get_text('#lblCoordenadaY'),
        mensaje
    )

async def procesar_direcciones(df, columna):
    barrios, upzs, localidades, coordenadas_x, coordenadas_y, mensajes = [], [], [], [], [], []
    errores = []

    async with async_playwright() as p:
        browser, page = await iniciar_sesion(p)
        for i, direccion in enumerate(df[columna]):
            direccion = limpiar_direccion(direccion)
            datos = (None, None, None, None, None, None)
            try:
                if not isinstance(direccion, str) or len(direccion) < 6:
                    raise ValueError("Dirección inválida o muy corta")
                datos = await buscar_direccion(page, direccion)
            except Exception as e:
                errores.append({"DIRECCION": direccion, "Error": str(e)})
            barrios.append(datos[0])
            upzs.append(datos[1])
            localidades.append(datos[2])
            coordenadas_x.append(datos[3])
            coordenadas_y.append(datos[4])
            mensajes.append(datos[5])
            await asyncio.sleep(random.uniform(1, 2))
        await browser.close()

    df['Barrio'] = barrios
    df['UPZ'] = upzs
    df['Localidad'] = localidades
    df['Coordenada_X'] = coordenadas_x
    df['Coordenada_Y'] = coordenadas_y
    df['Mensaje'] = mensajes
    return df, pd.DataFrame(errores)

# --------------------------
# INTERFAZ STREAMLIT
# --------------------------
st.title("Geocodificación Bogotá - SDS")
file = st.file_uploader("📂 Sube tu archivo Excel", type=["xlsx"])

if file:
    df = pd.read_excel(file)
    columnas = df.columns.tolist()
    seleccion = st.selectbox("📍 Selecciona la columna con direcciones", columnas)
    if st.button("🚀 Ejecutar geocodificación"):
        with st.spinner("Procesando direcciones, por favor espera..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            df_resultado, errores = loop.run_until_complete(procesar_direcciones(df.copy(), seleccion))
            st.success("¡Proceso finalizado!")

            st.download_button("📥 Descargar resultados", df_resultado.to_csv(index=False).encode(), "resultados.csv")
            if not errores.empty:
                st.download_button("⚠️ Descargar errores", errores.to_csv(index=False).encode(), "errores.csv")
