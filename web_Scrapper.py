import requests
import json
from bs4 import BeautifulSoup
import os 

class WebScrapper:
    def __init__(self, archivo_entrada='datos/json/revistas.json',
                 archivo_salida='datos/json/Scimagorevistas.json'):
        self.archivo_entrada = archivo_entrada
        self.archivo_salida = archivo_salida
        self.url_base = "https://www.scimagojr.com/journalsearch.php?q="
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
        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(self.archivo_salida), exist_ok=True)
        with open(self.archivo_salida, 'w', encoding='utf-8') as file:
            json.dump(self.datos_revistas, file, ensure_ascii=False, indent=2)
        
    def cargar_revistas_entradas(self):
        '''Carga las revistas desde el archivo de entrada.'''
        # Asegurarse de que el directorio existe
        os.makedirs(os.path.dirname(self.archivo_entrada), exist_ok=True)
        
        if not os.path.exists(self.archivo_entrada):
            print(f"El archivo {self.archivo_entrada} no existe. Creando archivo vacío.")
            with open(self.archivo_entrada, 'w', encoding='utf-8') as file:
                json.dump([], file)
            return []
        
        with open(self.archivo_entrada, 'r', encoding='utf-8') as file:
            try:
                datos = json.load(file)
                # Verificar el formato de los datos
                if isinstance(datos, list):
                    return datos
                elif isinstance(datos, dict):
                    # Convertir a lista si es un diccionario
                    return [{"id": key, "title": value.get("title", "Sin título")} 
                             for key, value in datos.items()]
                else:
                    print(f"Formato de datos no reconocido. Creando lista vacía.")
                    return []
            except json.JSONDecodeError:
                print(f"Error al decodificar el archivo JSON. Verificar formato.")
                return []
        
    def buscar_revista(self, titulo_revista):
        '''Busca revistas en la página web de Scimago.'''
        url_busqueda = self.url_base + titulo_revista.replace(" ", "+")
        respuesta = requests.get(url_busqueda, headers=self.encabezados)
        
        if respuesta.status_code != 200:
            print(f"Error al realizar la búsqueda: {respuesta.status_code}")
            return None
            
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        enlaces = soup.select('.search_results a')
        
        if not enlaces:
            print(f"No se encontraron resultados para {titulo_revista}.")
            return None
            
        # Tomar el primer resultado
        enlace_revista = enlaces[0]['href']
        url_revista = f"https://www.scimagojr.com{enlace_revista}"
        return self.extraer_datos(url_revista)
    
    def extraer_datos(self, url_revista):
        '''Extrae los datos de la revista desde la página web.'''
        respuesta = requests.get(url_revista, headers=self.encabezados)
        
        if respuesta.status_code != 200:
            print(f"Error al acceder a la página de la revista: {respuesta.status_code}")
            return None
            
        soup = BeautifulSoup(respuesta.text, 'html.parser')
        datos_revista = {}
        
        # 1. Sitio web de la revista
        enlaces = soup.find_all('a', href=True)
        for enlace in enlaces:
            texto = enlace.text.lower()
            if 'journal' in texto or 'website' in texto or 'homepage' in texto:
                datos_revista['sitio_web'] = enlace['href']
                break
        
        # 2. H-Index
        h_index_elem = soup.select_one('.hindexnumber')
        if h_index_elem:
            datos_revista['h_index'] = h_index_elem.text.strip()
        else:
            datos_revista['h_index'] = "No disponible"
        
        # 3. Subject Area and category
        subject_areas = []
        subjects_elem = soup.select('.subject_area_box')
        for subject in subjects_elem:
            area_name = subject.select_one('.subject_area_title')
            if area_name:
                subject_area = {
                    "area": area_name.text.strip(),
                    "categorias": []
                }
                
                categorias = subject.select('.treecategory')
                for cat in categorias:
                    subject_area["categorias"].append(cat.text.strip())
                
                subject_areas.append(subject_area)
        
        datos_revista['subject_areas'] = subject_areas
        
        # 4. Publisher
        publisher_elem = soup.find('p', text=lambda t: t and "Publisher:" in t)
        if publisher_elem:
            publisher = publisher_elem.findNext()
            if publisher:
                datos_revista['publisher'] = publisher.text.strip()
            else:
                datos_revista['publisher'] = "No disponible"
        else:
            datos_revista['publisher'] = "No disponible"
        
        # 5. ISSN
        issn_elem = soup.select_one('.issn')
        if issn_elem:
            datos_revista['issn'] = issn_elem.text.strip()
        else:
            datos_revista['issn'] = "No disponible"
        
        # 6. Widget (URL del widget)
        widget_url = f"https://www.scimagojr.com/journalsearch.php?q={datos_revista.get('issn', '')}&widget=1"
        datos_revista['widget'] = widget_url
        
        # 7. Publication Type
        publication_type_elem = soup.find('p', text=lambda t: t and "Publication type:" in t)
        if publication_type_elem:
            pub_type = publication_type_elem.findNext()
            if pub_type:
                datos_revista['publication_type'] = pub_type.text.strip()
            else:
                datos_revista['publication_type'] = "No disponible"
        else:
            datos_revista['publication_type'] = "No disponible"
        
        # Información adicional útil
        # SJR
        sjr_elem = soup.select_one('.sjr')
        if sjr_elem:
            datos_revista['sjr'] = sjr_elem.text.strip()
        else:
            datos_revista['sjr'] = "No disponible"
        
        # Título
        titulo_elem = soup.select_one('.journalTitle')
        if titulo_elem:
            datos_revista['titulo'] = titulo_elem.text.strip()
        else:
            datos_revista['titulo'] = "No disponible"
        
        # Cuartil
        cuartil_elem = soup.select_one('.cellqtop')
        if cuartil_elem:
            datos_revista['cuartil'] = cuartil_elem.text.strip()
        else:
            datos_revista['cuartil'] = "No disponible"
        
        return datos_revista
        
    def procesar_revistas(self):
        """Procesa todas las revistas del archivo de entrada"""
        revistas = self.cargar_revistas_entradas()
        
        if not revistas:
            print("No se encontraron revistas para procesar")
            return
        
        total = len(revistas)
        procesadas = 0
        
        for revista in revistas:
            # Verificar que revista sea un diccionario
            if not isinstance(revista, dict):
                print(f"Error: Se esperaba un diccionario, pero se encontró {type(revista)}. Omitiendo.")
                continue
                
            # Obtener id y título con manejo seguro
            id_revista = revista.get('id') if isinstance(revista, dict) else None
            titulo_revista = revista.get('title') if isinstance(revista, dict) else None
            
            if not id_revista or not titulo_revista:
                print("Revista sin ID o título. Omitiendo.")
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
                self.guardar_datos()
            
            procesadas += 1
            
        print(f"Proceso completado. {procesadas} revistas procesadas.")

if __name__ == "__main__":
    scrapper = WebScrapper()
    scrapper.procesar_revistas()
    print("Datos guardados en el archivo JSON.")