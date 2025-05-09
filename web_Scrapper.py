import requests
import json
from bs4 import BeautifulSoup
import os 

'''Este archivo contiene la clase WebScrapper, que se encarga de realizar el web scraping de una página web y guardar los datos en un archivo JSON.'''
class WebScrapper:
    def __init__(self, archivo_entrada = 'HectorIduma/proyecto-final/datos/json/revistas.json',
                 archivo_salida = 'HectorIduma/proyecto-final/datos/json/Scimagorevistas.json'):
        self.archivo_entrada = archivo_entrada
        self.archivo_salida = archivo_salida
        self.url = "https://www.scimagojr.com/journalsearch.php?q="
        self.encabezados = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        self.datos_revistas = self.cargar_datos_existentes()
        
    def cargar_datos_existentes(self):
        '''Carga los datos existentes desde el archivo JSON. Si el archivo no existe, devuelve un diccionario vacío.'''
        if os.path.exists(self.archivo_salida):
            with open(self.archivo_salida, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            return {}
        
    def guardar_datos(self):
        '''Guarda los datos en el archivo JSON.'''
        with open(self.archivo_salida, 'w', encoding='utf-8') as file:
            json.dump(self.datos_revistas, file, ensure_ascii=False, indent=2)
        
    def cargar_revistas_entradas(self):
        '''Carga las revistas desde el archivo de entrada.'''
        with open(self.archivo_entrada, 'r', encoding='utf-8') as file:
            return json.load(file)
        
    def buscar_revistas(self,titulo_revista):
        '''Busca revistas en la página web de Scimago.'''
        url_busqueda = self.url_base + titulo_revista.replace(" ", "+")
        respuesta = requests.get(url_busqueda, headers=self.encabezados)
        if respuesta.status_code == 200:
            soup = BeautifulSoup(respuesta.text, 'html.parser')
            resultados = soup.find_all('div', class_='search-results')
            if resultados:
                return self.extraer_datos(resultados)
            else:
                print(f"No se encontraron resultados para {titulo_revista}.")
                return None
        else:
            print(f"Error al realizar la búsqueda: {respuesta.status_code}")
            return None
        enlace_revista = resultados_busqueda[0]['href']
        url_revista = f"https://www.scimagojr.com{enlace_revista}"
        
        return self.extraer_datos(url_revista)
    
    def extraer_datos(self, url_revista):
        '''Extrae los datos de la revista desde la página web.'''
        respuesta = requests.get(url_revista, headers=self.encabezados)
        respuesta.raise_for_status()  # Lanza un error si la respuesta no es exitosa
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        datos_revista = {}
        sitio_web_elementos = soup.find_all('div', class_='sitio-web')
        if sitio_web_elementos:
            for elemento in sitio_web_elementos:
                enlace = elemento.find('a')
                if enlace and 'href' in enlace.attrs:
                    datos_revista['sitio_web'] = enlace['href']
        else:
            print(f"No se encontraron datos para la revista en {url_revista}.")
            return None
        
    def procesar_revistas(self):
        """Procesa todas las revistas del archivo de entrada"""
        revistas = self.cargar_revistas_entrada()
        
        if not revistas:
            print("No se encontraron revistas para procesar")
            return
        
        total = len(revistas)
        procesadas = 0
        
        for revista in revistas:
            id_revista = revista.get('id')
            titulo_revista = revista.get('title')
            
            if not id_revista or not titulo_revista:
                continue
                
            if id_revista in self.datos_revistas:
                print(f"La revista '{titulo_revista}' ya está en la base de datos")
                procesadas += 1
                continue
                
            print(f"Procesando {procesadas+1}/{total}: {titulo_revista}")
            
            datos_scimago = self.buscar_revista(titulo_revista)
            
            if datos_scimago:
                self.datos_revistas[id_revista] = {
                    **revista,
                    **datos_scimago
                }
                self._guardar_datos()
            
            procesadas += 1
            
        print(f"Proceso completado. {procesadas} revistas procesadas.")
        

if __name__ == "__main__":
    scrapper = WebScrapper()
    scrapper.procesar_revistas()
    print("Datos guardados en el archivo JSON.")
        
        
        
        
