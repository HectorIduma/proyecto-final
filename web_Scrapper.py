import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re

def scrape_scimago(journal_title):
    """
    Extrae información sobre una revista científica de Scimago
    """
    # Convertir espacios para la URL de búsqueda
    search_url = f"https://www.scimagojr.com/journalsearch.php?q={journal_title.replace(' ', '+')}"
    
    try:
        # Añadir User-Agent para evitar ser bloqueado
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        print(f"Buscando '{journal_title}' en: {search_url}")
        search_response = requests.get(search_url, headers=headers)
        search_response.raise_for_status()  # Verificar si la solicitud fue exitosa
        
        # Guardar la página de búsqueda para depuración
        with open("search_page.html", "w", encoding="utf-8") as f:
            f.write(search_response.text)
        print("Página de búsqueda guardada en 'search_page.html' para depuración")
        
        search_soup = BeautifulSoup(search_response.text, 'html.parser')
        
        # ESTRATEGIA 1: Buscar por clase específica
        result_link = search_soup.find('a', class_='search_results_title')
        
        # ESTRATEGIA 2: Buscar por contenedor y título
        if not result_link:
            result_cells = search_soup.select('.search_results')
            for cell in result_cells:
                links = cell.find_all('a')
                for link in links:
                    if journal_title.lower() in link.text.lower():
                        result_link = link
                        print(f"Encontrado mediante estrategia 2: {link.text}")
                        break
                if result_link:
                    break
        
        # ESTRATEGIA 3: Buscar cualquier enlace con href que contenga 'journalssearch'
        if not result_link:
            all_links = search_soup.find_all('a', href=re.compile(r'journalsearch\.php'))
            for link in all_links:
                if link.text and len(link.text.strip()) > 0:
                    result_link = link
                    print(f"Encontrado mediante estrategia 3: {link.text}")
                    break
        
        if not result_link:
            print(f"No se encontraron resultados para '{journal_title}'")
            print("Revisa la estructura HTML en 'search_page.html'")
            return None
        
        # Obtener la URL completa de la revista
        href = result_link.get('href')
        if not href:
            print("El enlace no tiene atributo href")
            return None
            
        if href.startswith('http'):
            journal_url = href
        else:
            journal_url = "https://www.scimagojr.com/" + href
        
        print(f"Accediendo a: {journal_url}")
        
        # Pequeña pausa para evitar bloqueos
        time.sleep(2)
        
        # Usar directamente la URL específica de la revista en lugar de la URL de búsqueda
        journal_response = requests.get(journal_url, headers=headers)
        journal_response.raise_for_status()
        
        # Guardar la página de la revista para depuración
        with open("journal_page.html", "w", encoding="utf-8") as f:
            f.write(journal_response.text)
        print("Página de la revista guardada en 'journal_page.html' para depuración")
        
        journal_soup = BeautifulSoup(journal_response.text, 'html.parser')
        
        # EXTRACCIÓN DE DATOS CON MÚLTIPLES ESTRATEGIAS
        
        # 1. H-index - CORREGIDA LA EXTRACCIÓN
        h_index = None
        
        # Estrategia 1: Buscar el elemento específico con clase 'hindexnumber'
        h_index_element = journal_soup.find('span', class_='hindexnumber')
        if h_index_element:
            h_index = h_index_element.text.strip()
        
        # Estrategia 2: Buscar en celda con clase 'cellh'
        if not h_index:
            h_cell = journal_soup.select_one('.cellh')
            if h_cell:
                h_index = h_cell.text.strip()
        
        # Estrategia 3: Buscar en toda la página para el h-index
        if not h_index:
            # Primero intentamos encontrar cualquier número que aparezca cerca de "H index"
            h_section = journal_soup.find(string=re.compile(r'H[\s\-]*index', re.IGNORECASE))
            if h_section:
                parent = h_section.parent
                if parent:
                    # Buscar números en el texto del padre
                    h_index_numbers = re.search(r'(\d+)', parent.text)
                    if h_index_numbers:
                        h_index = h_index_numbers.group(1)
        
        # Estrategia 4: Buscar en divs o spans que contengan "h-index" o "h index"
        if not h_index:
            h_divs = journal_soup.find_all(['div', 'span'], string=re.compile(r'[Hh][\s\-]*Index'))
            for div in h_divs:
                numbers = re.search(r'(\d+)', div.text)
                if numbers:
                    h_index = numbers.group(1)
                    break
                # También buscar en el elemento siguiente
                next_elem = div.find_next()
                if next_elem:
                    numbers = re.search(r'(\d+)', next_elem.text)
                    if numbers:
                        h_index = numbers.group(1)
                        break
        
        # Estrategia 5: Último recurso, buscar en toda la página
        if not h_index:
            h_pattern = re.search(r'[Hh][\s\-]*Index:?\s*(\d+)', journal_soup.text)
            if h_pattern:
                h_index = h_pattern.group(1)
        
        # 2. Áreas temáticas
        subject_areas = []
        # Múltiples estrategias para áreas temáticas
        selectors = [
            '.journalsubject .subjectarea span',
            '.cellsubject span',
            '.subject-area',
            '.subjectarea'
        ]
        
        for selector in selectors:
            elements = journal_soup.select(selector)
            if elements:
                subject_areas = [e.text.strip() for e in elements if e.text.strip()]
                if subject_areas:
                    break
        
        # Si no se encuentran áreas con selectores, buscar patrones en el texto
        if not subject_areas:
            subject_section = journal_soup.find(string=re.compile(r'Subject Area', re.IGNORECASE))
            if subject_section:
                parent = subject_section.parent
                if parent:
                    # Buscar en los siguientes elementos hermanos
                    next_elements = parent.find_next_siblings()
                    for elem in next_elements[:3]:  # Revisar solo los próximos 3 elementos
                        if elem.text.strip() and not re.match(r'Publisher|ISSN|Type', elem.text):
                            areas = [area.strip() for area in elem.text.split(',')]
                            subject_areas.extend([area for area in areas if area])
                            if subject_areas:
                                break
        
        # 3. Editorial
        publisher = None
        publisher_selectors = [
            'div.journalpublisher', 
            '.cellpublisher', 
            '.publisher'
        ]
        
        for selector in publisher_selectors:
            element = journal_soup.select_one(selector)
            if element and element.text.strip():
                publisher = element.text.strip()
                break
        
        # Si no se encontró por selectores, buscar etiquetas con "Publisher"
        if not publisher:
            publisher_labels = journal_soup.find_all(['label', 'div', 'span'], string=re.compile(r'Publisher:', re.IGNORECASE))
            for label in publisher_labels:
                next_elem = label.find_next()
                if next_elem and next_elem.text.strip():
                    publisher = next_elem.text.strip()
                    break
                # O extraer del texto después de "Publisher:"
                if ':' in label.text:
                    pub_text = label.text.split(':', 1)[1].strip()
                    if pub_text:
                        publisher = pub_text
                        break
        
        # Si aún no se encuentra, buscar en texto completo
        if not publisher:
            publisher_pattern = re.search(r'Publisher:?\s*([^\n]+)', journal_soup.text)
            if publisher_pattern:
                publisher = publisher_pattern.group(1).strip()
        
        # 4. ISSN
        issn = None
        issn_element = journal_soup.find('div', class_='issn')
        if not issn_element:
            issn_element = journal_soup.select_one('.journalissn')
            
        if issn_element:
            issn = issn_element.text.strip()
            # Limpiar prefijo "ISSN:" si existe
            if 'ISSN:' in issn:
                issn = issn.split('ISSN:', 1)[1].strip()
        
        # Si no se encuentra, buscar por text
        if not issn:
            issn_pattern = re.search(r'ISSN:?\s*([\d\-X]+)', journal_soup.text)
            if issn_pattern:
                issn = issn_pattern.group(1).strip()
        
        # 5. Tipo de publicación - CORREGIDA LA EXTRACCIÓN
        pub_type = None
        
        # Estrategia 1: Usar selectores más específicos y expandidos
        type_selectors = [
            'div.publicationtype', 
            '.celltype', 
            '.type',
            '.journal-type',
            '.journal_type',
            '.publication-type'
        ]
        
        for selector in type_selectors:
            element = journal_soup.select_one(selector)
            if element and element.text.strip():
                pub_type = element.text.strip()
                # Limpiar prefijo "Type:" si existe
                if 'Type:' in pub_type:
                    pub_type = pub_type.split('Type:', 1)[1].strip()
                break
        
        # Estrategia 2: Buscar elementos que contengan "Type:" o "Publication Type:"
        if not pub_type:
            type_labels = journal_soup.find_all(
                ['label', 'div', 'span', 'p', 'td'], 
                string=re.compile(r'(Type|Publication Type):', re.IGNORECASE)
            )
            for label in type_labels:
                # Intentar extraer del texto después de "Type:"
                if ':' in label.text:
                    type_text = label.text.split(':', 1)[1].strip()
                    if type_text and not re.match(r'^\s*$', type_text):
                        pub_type = type_text
                        break
                # O buscar en el siguiente elemento
                next_elem = label.find_next()
                if next_elem and next_elem.text.strip():
                    pub_type = next_elem.text.strip()
                    break
        
        # Estrategia 3: Buscar en tablas o secciones específicas
        if not pub_type:
            # Buscar en filas de tabla que contengan "Type"
            type_rows = journal_soup.find_all('tr')
            for row in type_rows:
                if re.search(r'Type', row.text, re.IGNORECASE):
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        pub_type = cells[1].text.strip()
                        break
        
        # Estrategia 4: Búsqueda amplia en el texto
        if not pub_type:
            # Patrones comunes para tipo de publicación
            type_patterns = [
                r'Type:?\s*([^\n;]+)',
                r'Publication Type:?\s*([^\n;]+)',
                r'Document Type:?\s*([^\n;]+)'
            ]
            
            for pattern in type_patterns:
                type_match = re.search(pattern, journal_soup.text, re.IGNORECASE)
                if type_match:
                    pub_type = type_match.group(1).strip()
                    break
        
        # Crear diccionario con los datos encontrados
        data = {
            "title": journal_title,
            "url": journal_url,
            "h-index": h_index,
            "subject_area": subject_areas,
            "publisher": publisher,
            "issn": issn,
            "publication_type": pub_type,
            "search_url": search_url
        }
        
        # Imprimir resumen para verificación
        print("\n--- DATOS EXTRAÍDOS ---")
        print(f"Revista: '{journal_title}'")
        print(f"URL: {journal_url}")
        print(f"H-index: {h_index}")
        print(f"Áreas: {', '.join(subject_areas) if subject_areas else 'No encontrado'}")
        print(f"Editorial: {publisher}")
        print(f"ISSN: {issn}")
        print(f"Tipo: {pub_type}")
        print("---------------------\n")
        
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"Error al acceder a Scimago: {e}")
        return None
    except Exception as e:
        print(f"Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_journals_from_json(input_json_path, output_json_path):
    """
    Lee títulos de revistas desde un archivo JSON y ejecuta el scraper para cada uno
    
    Args:
        input_json_path: Ruta al archivo JSON con los títulos de revistas
        output_json_path: Ruta donde guardar los resultados del scraping
    """
    print(f"Leyendo revistas desde: {input_json_path}")
    
    try:
        # Intentar cargar el archivo de entrada
        with open(input_json_path, 'r', encoding='utf-8') as f:
            journals_data = json.load(f)
        
        # Verificar que se haya cargado correctamente
        if not journals_data:
            print("El archivo JSON está vacío o tiene un formato incorrecto.")
            return
            
        print(f"Se encontraron datos en el archivo JSON. Procesando...")
        
        # Crear directorio de salida si no existe
        os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
        
        # Cargar datos existentes del archivo de salida o crear lista vacía
        existing_data = []
        if os.path.exists(output_json_path):
            try:
                with open(output_json_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # Si no es una lista, convertirlo en una lista
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                print(f"Archivo de salida existente cargado con {len(existing_data)} revistas.")
            except json.JSONDecodeError:
                print("El archivo JSON de salida está corrupto. Creando uno nuevo.")
                existing_data = []
            except Exception as e:
                print(f"Error al cargar archivo de salida: {e}")
                existing_data = []
        
        # Contador para estadísticas
        processed_count = 0
        success_count = 0
        
        # Procesar cada título de revista en el JSON
        for key, value in journals_data.items():
            # Buscar el título en diferentes posibles ubicaciones/formatos
            journal_title = None
            
            # Opción 1: El valor directamente es el título
            if isinstance(value, str):
                journal_title = value
            
            # Opción 2: El título está dentro de un diccionario bajo alguna clave común
            elif isinstance(value, dict):
                # Posibles claves para el título
                title_keys = ["titulo", "Titulo", "TITULO", "title", "Title", "TITLE", "TABULADOR"]
                
                for tk in title_keys:
                    if tk in value:
                        journal_title = value[tk]
                        break
            
            # Si no encontramos título, usamos la clave como título
            if not journal_title:
                journal_title = key
                
            print(f"\nProcesando revista: '{journal_title}'")
            processed_count += 1
            
            # Verificar si la revista ya existe en los datos de salida
            journal_exists = False
            for existing_journal in existing_data:
                if existing_journal.get('title', '').lower() == journal_title.lower():
                    print(f"La revista '{journal_title}' ya existe en el archivo de salida. Saltando...")
                    journal_exists = True
                    success_count += 1  # Contamos como exitoso aunque se salte
                    break
            
            if journal_exists:
                continue
                
            # Ejecutar el scraper para esta revista
            print(f"Obteniendo datos de Scimago para '{journal_title}'...")
            info = scrape_scimago(journal_title)
            
            # Si se obtuvieron datos, añadirlos al archivo de salida
            if info:
                existing_data.append(info)
                success_count += 1
                print(f"Revista '{journal_title}' añadida al archivo de salida.")
                
                # Cada 5 revistas, guardamos los resultados parciales
                if processed_count % 5 == 0:
                    with open(output_json_path, 'w', encoding='utf-8') as f:
                        json.dump(existing_data, f, indent=4, ensure_ascii=False)
                    print(f"Guardado parcial: {processed_count} revistas procesadas, {success_count} exitosas.")
                
                # Pausa para evitar sobrecargar el servidor
                time.sleep(3)
            else:
                print(f"No se pudo obtener información para '{journal_title}'.")
        
        # Guardar todos los resultados al finalizar
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        
        print(f"\n=== RESUMEN FINAL ===")
        print(f"Total de revistas procesadas: {processed_count}")
        print(f"Revistas con información obtenida: {success_count}")
        print(f"Información guardada en: {output_json_path}")
        
    except json.JSONDecodeError as e:
        print(f"Error al decodificar el archivo JSON de entrada: {e}")
    except FileNotFoundError:
        print(f"No se encontró el archivo: {input_json_path}")
    except Exception as e:
        print(f"Error inesperado al procesar el archivo JSON: {e}")
        import traceback
        traceback.print_exc()

def main():
    """
    Función principal para ejecutar el scraper
    """
    # Rutas de los archivos
    input_json_path = os.path.join("datos", "json", "revistas.json")
    output_json_path = os.path.join("datos", "json", "Scimago.json")
    
    print(f"Iniciando procesamiento de revistas desde archivo JSON...")
    print(f"Archivo de entrada: {input_json_path}")
    print(f"Archivo de salida: {output_json_path}")
    
    # Procesar las revistas desde el archivo JSON
    process_journals_from_json(input_json_path, output_json_path)

# Punto de entrada principal
if __name__ == "__main__":
    import sys
    
    # Comprobar si se proporcionaron argumentos adicionales
    if len(sys.argv) > 1:
        # Si hay argumentos, verificar si son rutas personalizadas
        if sys.argv[1] == "--input" and len(sys.argv) >= 3:
            input_path = sys.argv[2]
            output_path = os.path.join("datos", "json", "Scimago.json")  # Salida por defecto
            
            # Si también hay ruta de salida personalizada
            if len(sys.argv) >= 5 and sys.argv[3] == "--output":
                output_path = sys.argv[4]
                
            print(f"Usando ruta de entrada personalizada: {input_path}")
            print(f"Usando ruta de salida personalizada: {output_path}")
            process_journals_from_json(input_path, output_path)
        else:
            print("Uso: python web_Scrapper.py [--input ruta_entrada.json] [--output ruta_salida.json]")
            print("Por defecto se usará 'datos/json/revistas.json' como entrada y 'datos/json/Scimago.json' como salida.")
            main()
    else:
        # Ejecutar con rutas predeterminadas
        main()