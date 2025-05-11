from flask import Flask, render_template, request
import json

app = Flask(__name__)

# Cargar datos
with open('Scimago.json', encoding='utf-8') as f:
    data = json.load(f)

# Función auxiliar para extraer áreas únicas
def get_areas():
    areas = set()
    for journal in data:
        for sa in journal.get("subject_area", []):
            for area in sa.split(','):
                areas.add(area.strip())
    return sorted(areas)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/area')
def area():
    ''' Muestra la lista de áreas '''
    areas = get_areas()
    return render_template('area.html', areas=areas)

@app.route('/buscar')
def buscar():
    return render_template('buscar.html')

##@app.route('/catalogo')
##def catalogo():
##  return render_template('catalogo.html')

##@app.route('/explorar')
##def explorar():
##    return render_template('explorar.html')

##@app.route('/creditos')
##def creditos():
##    return render_template('creditos.html')

if __name__ == '__main__':
    app.run(debug=True)

