import string
from flask import Flask, render_template, request, redirect, url_for, session, flash
import random
import os
import json
import revista_clases as rc
from revista_clases import Revista

app = Flask(__name__)

sistema = rc.sistema_de_busqueda()

# Cargar datos
with open('Scimago.json', encoding='utf-8') as f:
    data = json.load(f)

for item in data:
    revista = Revista(
        title=item.get("title", ""),
        url=item.get("url", ""),
        h_index=item.get("h-index", "N/A"),
        subject_area=",".join(item.get("subject_area", [])),
        publisher=item.get("publisher", ""),
        issn=item.get("issn", ""),
        publication_type=item.get("publication_type", ""),
        search_url=item.get("search_url", ""),
        widget_url=item.get("widget_url", ""),
        widget_html=item.get("widget_html", "")
    )
    sistema.agregar_revista(revista)

# Función auxiliar para extraer áreas únicas
def get_areas():
    areas = set()
    for journal in data:
        for sa in journal.get("subject_area", []):
            for area in sa.split(','):
                areas.add(area.strip())
    return sorted(areas)

# Funcion que devuelve una lista de revistas por área
def get_revistas_por_area(area_buscada):
    revistas = []
    for journal in data:
        for sa in journal.get("subject_area", []):
            if area_buscada in [a.strip() for a in sa.split(",")]:
                revistas.append({
                    "title": journal.get("title"),
                    "url": journal.get("url", "#"),
                    "h_index": journal.get("h-index", "Desconocido")
                })
                break
    return revistas

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/area')
def area():
    selected_area = request.args.get("area")
    areas = get_areas()
    journals = get_revistas_por_area(selected_area) if selected_area else []
    return render_template("area.html", areas=areas, journals=journals, selected=selected_area)
    
@app.route('/area/<nombre_area>')
def revistas_por_area(nombre_area):
    journals = get_revistas_por_area(nombre_area)
    return render_template('revistas_por_area.html', area=nombre_area, journals=journals)


##@app.route('/buscar')
##def buscar():
##  return render_template('buscar.html')

##@app.route('/catalogo')
##def catalogo():
##  return render_template('catalogo.html')

@app.route('/explorar')
def explorar():
    letras = [chr(i) for i in range(65, 91)]  # A-Z
    return render_template('explorar.html', letras=letras)

@app.route('/explorar/<letra>')
def explorar_por_letra(letra):
    letra = letra.lower().strip()
    revistas = [revista for revista in sistema.revista if revista.title.strip().lower().startswith(letra)]
    return render_template('revistas_por_letra.html', letra=letra, revistas=revistas)





##@app.route('/creditos')
##def creditos():
##    return render_template('creditos.html')

if __name__ == '__main__':
    app.run(debug=True)

