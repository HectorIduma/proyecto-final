
class Revista:
    def __init__(self, title, url, h_index, subject_area, publisher,
                issn, publication_type, search_url, widget_url, widget_html=None):
        self.title = title
        self.url = url
        self.h_index = h_index
        self.subject_area = subject_area
        self.publisher = publisher
        self.issn = issn
        self.publication_type = publication_type
        self.search_url = search_url
        self.widget_url = widget_url
        self.widget_html = widget_html

    def to_dict(self):
        return {
            "title": self.title,
            "url": self.url,
            "h_index": self.h_index,
            "subject_area": self.subject_area,
            "publisher": self.publisher,
            "issn": self.issn,
            "publication_type": self.publication_type,
            "search_url": self.search_url,
            "widget_url": self.widget_url,
            "widget_html": self.widget_html,
        }
    
    def __str__(self):
        return f"Revista({self.title}, {self.url}, {self.h_index}, {self.subject_area}, {self.publisher}, {self.issn}, {self.publication_type}, {self.search_url}, {self.widget_url})"

class sistema_de_busqueda:
    def __init__(self):
        self.revista = []
    
    def agregar_revista(self, revista):
        self.revista.append(revista)
    
    def buscar_por_area(self, area_buscada):
        revistas_encontradas = []
        for revista in self.revista:
            if area_buscada in [a.strip() for a in revista.subject_area.split(",")]:
                revistas_encontradas.append(revista.to_dict())
        return revistas_encontradas
    
    def buscar_por_titulo(self, titulo_buscado):
        revistas_encontradas = []
        for revista in self.revista:
            if titulo_buscado.lower() in revista.title.lower():
                revistas_encontradas.append(revista.to_dict())
        return revistas_encontradas
    
    def buscar_por_letra(self, letra_buscada):
        revistas_encontradas = []
        for revista in self.revista:
            if revista.title.strip().lower().startswith(letra_buscada.lower()):
                revistas_encontradas.append(revista.to_dict())
        return revistas_encontradas


    
if __name__ == '__main__':
    sistema = sistema_de_busqueda()