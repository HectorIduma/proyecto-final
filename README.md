# Proyecto Final - Aplicación Web de Consulta de Revistas

Este repositorio contiene el código fuente de una aplicación web para consultar revistas a través de archivos JSON cargados dentro del proyecto.

## Descripción

La aplicación permite a los usuarios consultar información de diversas revistas mediante una interfaz web. Los datos de las revistas se encuentran almacenados en archivos JSON dentro del proyecto.

## Desarrollado con ❤️ por: 
  Héctor Iduma.
  Ian Rodriguez.
  Genaro Islas.

## Características

- Consulta de información de revistas almacenadas en archivos JSON
- Interfaz de búsqueda para filtrar revistas
- Visualización detallada de la información de cada revista
- Interfaz de usuario intuitiva y responsive

## Tecnologías utilizadas

- **Frontend**: HTML, CSS, Bootstrap
- **Backend**: Python

## Estructura del proyecto

```
PROYECTO-FINAL/ │ 
├── pycache/ 
│ ├── revista_clases.cpython-312.pyc │
  └── revista_clases.cpython-313.pyc │ 
├── datos/ │
 ├── csv/ │
 └── json/ │
├── templates/ │
   ├── area.html │
   ├── base.html │
   ├── buscar.html │
   ├── catalogo.html │
   ├── creditos.html │
   ├── explorar.html │
   ├── index.html │
   ├── revista.html │
   ├── revistas_por_area.html │
   └── revistas_por_letra.html │
├── app.py
├── app2.py
├── README.md
├── revista_clases.py
├── Scimago.json(JSON Usado para pruebas)
├── search_page.html
└── web_Scrapper.py
```

## Requisitos previos

- Se deben instalar todas las librerías que ocupa el programa
- Crear un environment con todas las librerías necesarias para el funcionamiento del proyecto

## Instalación

1. Clona este repositorio:
   ```
   git clone https://github.com/HectorIduma/proyecto-final.git
   ```

2. Navega al directorio del proyecto:
   ```
   cd proyecto-final
   ```

3. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

4. Crea un environment e instala las dependencias:
   ```
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. Inicia la aplicación:
   ```
   python app2.py
   (Actualmente el programa cuenta con 11900 revistas, si se quiere seguir generando, se ejecuta el
   archivo web_Scrapper)
   ```

6. Abre tu navegador y visita `http://localhost:5000`

## Uso

1. Ejecuta la aplicación siguiendo las instrucciones de instalación
2. Accede a la página web generada
3. Utiliza la función de búsqueda para encontrar la información que necesites
4. Navega por los resultados mostrados en la interfaz

## Web Scrapper

El proyecto incluye un componente de web scraping que permite extraer información de diferentes sitios web. El scrapper funciona de la siguiente manera:

1. Realiza peticiones HTTP a los sitios web objetivo
2. Analiza el HTML de las páginas utilizando técnicas de parsing
3. Extrae la información relevante según los selectores definidos
4. Procesa y almacena los datos obtenidos para su posterior visualización
5. Implementa técnicas para evitar bloqueos por parte de los sitios web (delays, rotación de user agents, etc.)

El scrapper está diseñado para respetar las políticas de robots.txt y evitar sobrecargar los servidores de destino.

## Contribuir

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add amazing feature'`)
4. Haz push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## Link del proyecto

Link del proyecto: [https://github.com/HectorIduma/proyecto-final](https://github.com/HectorIduma/proyecto-final)

---
## USO DE IAS GENERATIVAS
  Parte 1. Se utilizo ia para leer los archivos con terminacion en .csv
  Parte 2. Se utilizo para crear mas de una estrategia de busqueda y extraccion de informacion(las primeras estrategias son creadas por humanos)
  Parte 3. Se uso a momento de establecer una guía para la ejecución de código siendo mayormente utilizada para comprender 
            la lógica que seguían otros códigos vistos en clase y así implementarlos adaptando su uso. En algunas partes se uso parar generar pequeñas partes del html.
