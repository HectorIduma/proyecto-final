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
        
        # 1. H-index
        h_index = None
        h_index_element = journal_soup.find('span', class_='hindexnumber')
        if h_index_element:
            h_index = h_index_element.text.strip()
        else:
            # Buscar en la celda de H index
            h_cell = journal_soup.select_one('.cellh')
            if h_cell:
                h_index = h_cell.text.strip()
            else:
                # Buscar patrón de texto "H index: 123"
                h_index_pattern = re.search(r'H index:\s*(\d+)', journal_soup.text)
                if h_index_pattern:
                    h_index = h_index_pattern.group(1)
                else:
                    # Buscar texto de H index con regex más flexible
                    h_index_flex = re.search(r'[Hh][\s\-]*index:?\s*(\d+)', journal_soup.text)
                    if h_index_flex:
                        h_index = h_index_flex.group(1)
        
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
        
        # 5. Tipo de publicación
        pub_type = None
        type_selectors = ['div.publicationtype', '.celltype', '.type']
        
        for selector in type_selectors:
            element = journal_soup.select_one(selector)
            if element and element.text.strip():
                pub_type = element.text.strip()
                break
        
        # Si no se encuentra, buscar etiquetas con "Type"
        if not pub_type:
            type_labels = journal_soup.find_all(['label', 'div', 'span'], string=re.compile(r'Type:', re.IGNORECASE))
            for label in type_labels:
                next_elem = label.find_next()
                if next_elem and next_elem.text.strip():
                    pub_type = next_elem.text.strip()
                    break
                # O extraer del texto después de "Type:"
                if ':' in label.text:
                    type_text = label.text.split(':', 1)[1].strip()
                    if type_text:
                        pub_type = type_text
                        break
        
        # Si aún no se encuentra, buscar en el texto completo
        if not pub_type:
            type_pattern = re.search(r'Type:?\s*([^\n]+)', journal_soup.text)
            if type_pattern:
                pub_type = type_pattern.group(1).strip()
        
        # Crear diccionario con los datos encontrados
        data = {
            "title": journal_title,
            "url": journal_url,
            "h_index": h_index,
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

def main():
    """
    Función principal para ejecutar el scraper
    """
    # Revista a buscar (se puede modificar o pasar como argumento)
    journal_title = "2d materials"
    print(f"Iniciando búsqueda para '{journal_title}'...")
    
    # Ejecutar el scraper
    info = scrape_scimago(journal_title)

    # Verificar si se obtuvieron datos
    if info:
        # Crear directorio si no existe
        output_path = os.path.join("datos", "json", "Scimago.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Cargar datos existentes o crear lista vacía si no existe el archivo
        existing_data = []
        if os.path.exists(output_path):
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    # Si no es una lista, conviértelo en una lista que contenga ese elemento
                    if not isinstance(existing_data, list):
                        existing_data = [existing_data]
                print(f"Archivo existente cargado con {len(existing_data)} revistas.")
            except json.JSONDecodeError:
                print("El archivo JSON existente está corrupto. Creando uno nuevo.")
                existing_data = []
            except Exception as e:
                print(f"Error al cargar archivo existente: {e}")
                existing_data = []
        
        # Comprobar si la revista ya existe en los datos
        journal_exists = False
        for i, journal in enumerate(existing_data):
            if journal.get('title') == info['title']:
                # Actualizar datos de revista existente
                existing_data[i] = info
                journal_exists = True
                print(f"Revista '{info['title']}' actualizada en el archivo existente.")
                break
        
        # Si la revista no existe, añadirla a la lista
        if not journal_exists:
            existing_data.append(info)
            print(f"Revista '{info['title']}' añadida al archivo.")
        
        # Guardar lista actualizada en el archivo JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, indent=4, ensure_ascii=False)
        
        print(f"Información guardada exitosamente en {output_path}")
        print(f"Total de revistas en el archivo: {len(existing_data)}")
        
        # Mostrar último contenido añadido
        print("\nÚltima revista añadida/actualizada:")
        print(json.dumps(info, indent=4, ensure_ascii=False))
    else:
        print("No se pudo obtener información. El archivo JSON no ha sido modificado.")

# Punto de entrada principal
if __name__ == "__main__":
    import sys
    
    # Comprobar si se proporcionó un nombre de revista como argumento
    if len(sys.argv) > 1:
        # Unir todos los argumentos como nombre de la revista
        journal_title = " ".join(sys.argv[1:])
        print(f"Usando nombre de revista desde argumentos: '{journal_title}'")
        
        # Ejecutar el scraper para la revista especificada
        info = scrape_scimago(journal_title)

        # Verificar si se obtuvieron datos
        if info:
            # Crear directorio si no existe
            output_path = os.path.join("datos", "json", "Scimago.json")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Cargar datos existentes o crear lista vacía si no existe el archivo
            existing_data = []
            if os.path.exists(output_path):
                try:
                    with open(output_path, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                        # Si no es una lista, conviértelo en una lista que contenga ese elemento
                        if not isinstance(existing_data, list):
                            existing_data = [existing_data]
                    print(f"Archivo existente cargado con {len(existing_data)} revistas.")
                except json.JSONDecodeError:
                    print("El archivo JSON existente está corrupto. Creando uno nuevo.")
                    existing_data = []
                except Exception as e:
                    print(f"Error al cargar archivo existente: {e}")
                    existing_data = []
            
            # Comprobar si la revista ya existe en los datos
            journal_exists = False
            for i, journal in enumerate(existing_data):
                if journal.get('title').lower() == info['title'].lower():
                    # Actualizar datos de revista existente
                    existing_data[i] = info
                    journal_exists = True
                    print(f"Revista '{info['title']}' actualizada en el archivo existente.")
                    break
            
            # Si la revista no existe, añadirla a la lista
            if not journal_exists:
                existing_data.append(info)
                print(f"Revista '{info['title']}' añadida al archivo.")
            
            # Guardar lista actualizada en el archivo JSON
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(existing_data, f, indent=4, ensure_ascii=False)
            
            print(f"Información guardada exitosamente en {output_path}")
            print(f"Total de revistas en el archivo: {len(existing_data)}")
        else:
            print("No se pudo obtener información. El archivo JSON no ha sido modificado.")
    else:
        # Ejecutar la función main por defecto
        main()