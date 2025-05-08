import csv
import glob
import os
import json

def columnas_areas(ruta):
    resultado = {}  # Usamos un diccionario para registrar de dónde viene cada título

    archivos_csv = glob.glob(os.path.join(ruta, '*.csv'))

    for ruta in archivos_csv:
        area_nombre = os.path.splitext(os.path.basename(ruta))[0]  # nombre del archivo sin extensión
        print(f"Procesando: {ruta} como área: {area_nombre}")
        with open(ruta, newline='', encoding='latin-1') as archivo:
            lector = csv.DictReader(archivo)
            for fila in lector:
                try:
                    titulo = fila['TITULO:'].strip().lower()
                    if titulo not in resultado:
                        resultado[titulo] = {'areas': [], 'catalogos': []}
                    if area_nombre not in resultado[titulo]['areas']:
                        resultado[titulo]['areas'].append(area_nombre)
                except KeyError:
                    print(f"⚠️ Columna 'TITULO:' no encontrada en: {ruta}")
    return resultado

def columnas_catalogos(ruta):
    resultado = {}

    archivos_csv = glob.glob(os.path.join(ruta, '*.csv'))

    for ruta in archivos_csv:
        catalogo_nombre = os.path.splitext(os.path.basename(ruta))[0]
        print(f"Procesando: {ruta} como catálogo: {catalogo_nombre}")
        with open(ruta, newline='', encoding='latin-1') as archivo:
            lector = csv.DictReader(archivo)
            for fila in lector:
                try:
                    titulo = fila['TITULO:'].strip().lower()
                    if titulo not in resultado:
                        resultado[titulo] = {'areas': [], 'catalogos': []}
                    if catalogo_nombre not in resultado[titulo]['catalogos']:
                        resultado[titulo]['catalogos'].append(catalogo_nombre)
                except KeyError:
                    print(f"⚠️ Columna 'TITULO:' no encontrada en: {ruta}")
    return resultado

def revista_total(area, catalogos):
    revistas = {}

    for titulo, datos in revistas_areas.items():
        revistas[titulo] = {'areas': datos['areas'], 'catalogos': []}

    for titulo, datos in revistas_catalogos.items():
        if titulo in revistas:
            revistas[titulo]['catalogos'] = datos['catalogos']
        else:
            revistas[titulo] = {'areas': [], 'catalogos': datos['catalogos']}
    return revistas

def revista_json(revista):
    os.makedirs('datos/json', exist_ok=True)

    ruta_json = 'datos/json/revistas.json'

    with open(ruta_json, 'w', encoding='latin-1') as f:
       json.dump(revista, f, ensure_ascii=False, indent=4)

    print(f"✅ Diccionario guardado en: {ruta_json}")

if __name__ == '__main__':
    ruta_areas = 'datos/csv/areas'
    ruta_catalogos = 'datos/csv/catalogos'

    revistas_areas = columnas_areas(ruta_areas)
    revistas_catalogos = columnas_catalogos(ruta_catalogos)

    revista = revista_total(revistas_areas, revistas_catalogos)

    revista_json(revista)