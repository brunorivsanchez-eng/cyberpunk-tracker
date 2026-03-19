import json
import os
from modelos import Personaje

def actualizar_color_hp(personaje_obj, dicc_widgets):
    """
    Actualiza el valor de la barra de HP y modifica dinámicamente su color 
    y el del nombre según el porcentaje de vida restante y si es NPC o Jugador.
    """
    # 1. Actualización numérica de la barra
    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)

    # 2. Cálculo del umbral (50% o menos)
    umbral_critico = personaje_obj.max_hp * 0.5
    es_npc = dicc_widgets.get("es_npc", False)

    # 3. Determinación del código hexadecimal de color
    if personaje_obj.hp <= umbral_critico:
        color_actual = "#FF0000"  # Rojo: Peligro (aplica para todos)
    else:
        if es_npc:
            color_actual = "#9400D3"  # Morado: NPC saludable
        else:
            color_actual = "#15A315"  # Verde: PC saludable

    # 4. Aplicación de estilos visuales a la barra de vida
    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color_actual}; border-radius: 5px; }}"
        )

    # 5. Aplicación de estilos visuales al nombre
    if "nombre" in dicc_widgets:
        estilo_base = "font-family: 'Orbitron', sans-serif; font-size: 14px; font-weight: bold;"
        dicc_widgets["nombre"].setStyleSheet(f"color: {color_actual}; {estilo_base}")

def procesar_ataque(personaje_obj, entrada_widget, es_cabeza, es_melee, es_directo, dicc_widgets):
    texto = entrada_widget.text()
    if texto.isdigit():
        danio = int(texto)
        personaje_obj.aplicar_impacto(danio, es_cabeza, es_melee, es_directo)
        
        for attr in ["hp", "body_sp", "head_sp"]:
            if attr in dicc_widgets:
                dicc_widgets[attr].setValue(getattr(personaje_obj, attr))
        
        # Actualización de colores
        actualizar_color_hp(personaje_obj, dicc_widgets)
            
        entrada_widget.clear()

def procesar_curacion(personaje_obj, entrada_widget, dicc_widgets):
    texto = entrada_widget.text()
    if texto.isdigit():
        cantidad = int(texto)
        personaje_obj.curar(cantidad)
        
        if "hp" in dicc_widgets:
            dicc_widgets["hp"].setValue(personaje_obj.hp)
            
        # Actualización de colores
        actualizar_color_hp(personaje_obj, dicc_widgets)
            
        entrada_widget.clear()

def ajustar_stat_secundario(personaje_obj, atributo, cantidad, barra_widget):
    personaje_obj.modificar_stat_secundario(atributo, cantidad)
    nuevo_valor = getattr(personaje_obj, atributo)
    barra_widget.setValue(nuevo_valor)

def ajustar_atributo_simple(personaje_obj, atributo, cantidad, label_widget):
    """
    Controlador para los botones de +1 y -1 de los contadores simples (balas, penalizador de muerte).
    Actualiza el valor en el modelo y el texto del label.
    """
    personaje_obj.modificar_atributo_simple(atributo, cantidad)
    nuevo_valor = getattr(personaje_obj, atributo)
    # Actualizar el texto del widget de texto con el nuevo valor
    label_widget.setText(str(nuevo_valor))
    
def aplicar_dano_fijo(personaje_obj, cantidad, dicc_widgets):
    """
    Aplica una cantidad fija de daño directo al HP (ignorando armadura)
    y actualiza la interfaz visual del personaje.
    """
    # Se envía el daño con la bandera es_directo=True
    personaje_obj.aplicar_impacto(cantidad, es_cabeza=False, es_melee=False, es_directo=True)
    
    # Se actualiza el valor de la barra
    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)
        
    # Se evalúa si el color debe cambiar a crítico
    actualizar_color_hp(personaje_obj, dicc_widgets)
 
def ajustar_municion_arma(personaje_obj, nombre_arma, cantidad, lbl_widget):
    """Suma o resta munición a un arma específica sin exceder su máximo ni bajar de 0."""
    if hasattr(personaje_obj, "armas") and nombre_arma in personaje_obj.armas:
        arma = personaje_obj.armas[nombre_arma]
        nueva_municion = max(0, min(arma["actual"] + cantidad, arma["max"]))
        arma["actual"] = nueva_municion
        lbl_widget.setText(str(nueva_municion))

def recargar_arma_maxima(personaje_obj, nombre_arma, lbl_widget):
    """Restaura la munición de un arma específica a su valor máximo."""
    if hasattr(personaje_obj, "armas") and nombre_arma in personaje_obj.armas:
        arma = personaje_obj.armas[nombre_arma]
        arma["actual"] = arma["max"]
        lbl_widget.setText(str(arma["actual"]))

    
def resetear_personaje(personaje_obj, dicc_widgets):
    """
    Restaura todos los atributos del personaje a sus valores máximos o por defecto,
    y actualiza todos los componentes visuales vinculados.
    """
    # 1. Restauración del Modelo
    personaje_obj.hp = personaje_obj.max_hp
    personaje_obj.body_sp = personaje_obj.max_body_sp
    personaje_obj.head_sp = personaje_obj.max_head_sp
    personaje_obj.luck = personaje_obj.max_luck
    personaje_obj.death_penalty = 0
    
    if hasattr(personaje_obj, 'max_bullets'):
        personaje_obj.bullets = personaje_obj.max_bullets

    # 2. Restauración de la Interfaz Visual
    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)
        actualizar_color_hp(personaje_obj, dicc_widgets)
        
    for attr in ["body_sp", "head_sp", "luck"]:
        if attr in dicc_widgets:
            dicc_widgets[attr].setValue(getattr(personaje_obj, attr))
            
    if hasattr(personaje_obj, "armas"):
        for nombre_arma, datos in personaje_obj.armas.items():
            datos["actual"] = datos["max"]
            # Actualizar la interfaz si el arma está registrada en los widgets
            if "armas" in dicc_widgets and nombre_arma in dicc_widgets["armas"]:
                dicc_widgets["armas"][nombre_arma].setText(str(datos["actual"]))
        
    if "death_penalty" in dicc_widgets:
        dicc_widgets["death_penalty"].setText(str(personaje_obj.death_penalty))
        
    if "debufos" in dicc_widgets:
        for combo in dicc_widgets["debufos"]:
            combo.setCurrentIndex(0) # Retorna el selector al texto en blanco
    
def guardar_partida(pjs, npcs, ruta_archivo="campana.json"):
    """
    Serializa el estado actual de los personajes y NPCs en un archivo JSON.
    """
    datos = {"jugadores": [], "adversarios": []}
    
    # 1. Extracción de datos de Jugadores
    for p in pjs:
        datos["jugadores"].append({
            "nombre": p.nombre,
            "max_hp": p.max_hp, "hp": p.hp,
            "max_body_sp": p.max_body_sp, "body_sp": p.body_sp,
            "max_head_sp": p.max_head_sp, "head_sp": p.head_sp,
            "max_luck": p.max_luck, "luck": p.luck,
            "death_penalty": p.death_penalty,
            "armas": p.armas
        })
        
    # 2. Extracción de datos de NPCs
    for p in npcs:
        datos["adversarios"].append({
            "nombre": p.nombre,
            "max_hp": p.max_hp, "hp": p.hp,
            "max_body_sp": p.max_body_sp, "body_sp": p.body_sp,
            "max_head_sp": p.max_head_sp, "head_sp": p.head_sp,
            "max_luck": p.max_luck, "luck": p.luck,
            "death_penalty": p.death_penalty,
            "armas": p.armas
        })
        
    # 3. Escritura en disco
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def cargar_partida(ruta_archivo="campana.json"):
    """
    Lee el archivo JSON y reconstruye los objetos Personaje.
    Retorna dos listas: (pjs_cargados, npcs_cargados). Si no hay archivo, retorna (None, None).
    """
    if not os.path.exists(ruta_archivo):
        return None, None
        
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        datos = json.load(f)
        
    pjs_cargados = []
    for d in datos.get("jugadores", []):
        # Se instancia el objeto base con los valores máximos
        pj = Personaje(d["nombre"], d["max_hp"], d["max_body_sp"], d["max_head_sp"], d["max_luck"], d.get("armas", {}), d.get("death_penalty", 0))
        # Se sobrescriben los valores actuales con el estado guardado
        pj.hp = d["hp"]
        pj.body_sp = d["body_sp"]
        pj.head_sp = d["head_sp"]
        pj.luck = d["luck"]
        pjs_cargados.append(pj)
        
    npcs_cargados = []
    for d in datos.get("adversarios", []):
        npc = Personaje(d["nombre"], d["max_hp"], d["max_body_sp"], d["max_head_sp"], d["max_luck"], d.get("armas", {}), d.get("death_penalty", 0))
        npc.hp = d["hp"]
        npc.body_sp = d["body_sp"]
        npc.head_sp = d["head_sp"]
        npc.luck = d["luck"]
        npcs_cargados.append(npc)
        
    return pjs_cargados, npcs_cargados