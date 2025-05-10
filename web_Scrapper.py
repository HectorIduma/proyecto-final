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
            # Buscar patrón de texto "H index: 123"
            h_index_pattern = re.search(r'H index:\s*(\d+)', journal_soup.text)
            if h_index_pattern:
                h_index = h_index_pattern.group(1)
        
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
        
        # 3. Editorial
        publisher = None
        publisher_selectors = [
            'div.journalpublisher', 
            '.cellpublisher', 
            'label:contains("Publisher:")',
            '.publisher'
        ]
        
        for selector in publisher_selectors:
            try:
                element = None
                if ':contains' in selector:
                    # Tratamiento especial para selectores de tipo contains
                    label = selector.split(':contains("')[0]
                    text = selector.split(':contains("')[1].rstrip('")')
                    labels = journal_soup.find_all(label)
                    for lab in labels:
                        if text in lab.text:
                            element = lab.find_next()
                            break
                else:
                    element = journal_soup.select_one(selector)
                
                if element and element.text.strip():
                    publisher = element.text.strip()
                    break
            except Exception as e:
                print(f"Error al buscar publisher con selector {selector}: {e}")
        
        # Si no se encontró por selectores, buscar en texto
        if not publisher:
            publisher_pattern = re.search(r'Publisher:\s*([^\n]+)', journal_soup.text)
            if publisher_pattern:
                publisher = publisher_pattern.group(1).strip()
        
        # 4. ISSN
        issn = None
        issn_element = journal_soup.find('div', class_='issn')
        if not issn_element:
            issn_element = journal_soup.select_one('.journalissn')
        if not issn_element:
            issn_pattern = re.search(r'ISSN:\s*([\d\-X]+)', journal_soup.text)
            if issn_pattern:
                issn = issn_pattern.group(1).strip()
        else:
            issn = issn_element.text.strip()
        
        # 5. Tipo de publicación
        pub_type = None
        type_selectors = ['div.publicationtype', '.celltype', '.type']
        
        for selector in type_selectors:
            element = journal_soup.select_one(selector)
            if element and element.text.strip():
                pub_type = element.text.strip()
                break
        
        if not pub_type:
            type_pattern = re.search(r'Type:\s*([^\n]+)', journal_soup.text)
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
    # Revista a buscar
    journal_title = "2d materials"
    print(f"Iniciando búsqueda para '{journal_title}'...")
    
    # Ejecutar el scraper
    info = scrape_scimago(journal_title)

    # Verificar si se obtuvieron datos
    if info:
        # Crear directorio si no existe
        output_path = os.path.join("datos", "json", "Scimago.json")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Guardar datos en formato JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=4, ensure_ascii=False)
        
        print(f"Información guardada exitosamente en {output_path}")
        
        # Mostrar contenido del JSON
        print("\nContenido del archivo JSON:")
        print(json.dumps(info, indent=4, ensure_ascii=False))
    else:
        print("No se pudo obtener información. El archivo JSON no se ha generado.")

# Punto de entrada principal
if __name__ == "__main__":
    main()