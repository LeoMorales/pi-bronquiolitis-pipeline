from collections import Counter

def get_colors_for_labels(labels, color_by_labels):
    """Retorna un arreglo de colores para las etiquetas del análisis espacial.
    Existen casos en que no se presentan todas las categorías (por ejemplo no hay
    diamonds o donuts) por lo cual es necesario mantener un control con los colores
    para respetarlos en el scatter y en el mapa.
    """
    counter_dict = Counter(labels)
    painting_order = list(color_by_labels.keys())
    
    actual_labels = []
    while painting_order:
        label = painting_order.pop()
        if counter_dict[label] > 0:
            actual_labels.append(label)
    
    return [color_by_labels[label_key] for label_key in actual_labels]
