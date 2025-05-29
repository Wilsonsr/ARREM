import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import pandas as pd
import asyncio
from playwright.async_api import async_playwright
import os
import random
import re

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
    browser = await playwright.chromium.launch(headless=False)
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

async def geocodificar_con_playwright(ruta_archivo, columna):
    df = pd.read_excel(ruta_archivo)
    if columna not in df.columns:
        raise ValueError(f"La columna '{columna}' no existe en el archivo.")

    df[columna] = df[columna].apply(limpiar_direccion)

    barrios, upzs, localidades = [], [], []
    coordenadas_x, coordenadas_y = [], []
    mensajes_estado = []
    errores = []

    async with async_playwright() as p:
        browser, page = await iniciar_sesion(p)

        for i, direccion in enumerate(df[columna]):
            datos = (None, None, None, None, None, None)
            try:
                if not isinstance(direccion, str) or len(direccion.strip()) < 6:
                    raise ValueError("Dirección inválida o demasiado corta")

                datos = await buscar_direccion(page, direccion)

            except Exception as e:
                errores.append({'DIRECCION': direccion, 'Error': str(e)})
                if "Connection closed" in str(e) or "socket.send()" in str(e):
                    await browser.close()
                    browser, page = await iniciar_sesion(p)

            barrios.append(datos[0])
            upzs.append(datos[1])
            localidades.append(datos[2])
            coordenadas_x.append(datos[3])
            coordenadas_y.append(datos[4])
            mensajes_estado.append(datos[5])

            await asyncio.sleep(random.uniform(1.5, 3))

        await browser.close()

    df['Barrio'] = barrios
    df['UPZ'] = upzs
    df['Localidad'] = localidades
    df['Coordenada_X'] = coordenadas_x
    df['Coordenada_Y'] = coordenadas_y
    df['Mensaje'] = mensajes_estado

    ruta_salida = os.path.splitext(ruta_archivo)[0] + "_geocodificado_SIG.xlsx"
    df.to_excel(ruta_salida, index=False)

    if errores:
        pd.DataFrame(errores).to_excel("errores_geocodificacion.xlsx", index=False)

    return ruta_salida

def seleccionar_archivo():
    ruta = filedialog.askopenfilename(
        title="Seleccionar archivo Excel",
        filetypes=[("Archivos Excel", "*.xlsx")]
    )
    if not ruta:
        return

    try:
        df = pd.read_excel(ruta)
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")
        return

    columnas = df.columns.tolist()
    columna = simpledialog.askstring(
        "Columna de direcciones",
        f"Columnas encontradas:\n{columnas}\n\nEscribe el nombre exacto de la columna con las direcciones:"
    )

    if columna:
        try:
            salida = asyncio.run(geocodificar_con_playwright(ruta, columna))
            messagebox.showinfo("Éxito", f"Archivo guardado: {salida}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

# Interfaz gráfica
ventana = tk.Tk()
ventana.title("Geocodificador SIG Bogotá")
ventana.geometry("320x180")

boton = tk.Button(ventana, text="Seleccionar archivo Excel", command=seleccionar_archivo)
boton.pack(pady=50)

ventana.mainloop()
