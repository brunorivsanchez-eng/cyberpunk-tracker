import json
import os
from modelos import Personaje

# ==========================================
# GESTIÓN VISUAL Y DE INTERFAZ
# ==========================================

def actualizar_color_hp(personaje_obj, dicc_widgets):
    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)

    umbral_critico = personaje_obj.max_hp * 0.5
    es_npc = dicc_widgets.get("es_npc", False)

    if personaje_obj.hp <= umbral_critico:
        color_actual = "#FF0000"
    else:
        if es_npc:
            color_actual = "#9400D3"
        else:
            color_actual = "#15A315"

    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color_actual}; border-radius: 5px; }}"
        )

    if "nombre" in dicc_widgets:
        estilo_base = "font-family: 'Orbitron', sans-serif; font-size: 14px; font-weight: bold;"
        dicc_widgets["nombre"].setStyleSheet(f"color: {color_actual}; {estilo_base}")

# ==========================================
# LÓGICA DE COMBATE Y ATRIBUTOS
# ==========================================

def procesar_ataque(personaje_obj, entrada_widget, es_cabeza, es_melee, es_directo, dicc_widgets):
    texto = entrada_widget.text()
    if texto.isdigit():
        danio = int(texto)
        personaje_obj.aplicar_impacto(danio, es_cabeza, es_melee, es_directo)
        
        for attr in ["hp", "body_sp", "head_sp"]:
            if attr in dicc_widgets:
                dicc_widgets[attr].setValue(getattr(personaje_obj, attr))
        
        actualizar_color_hp(personaje_obj, dicc_widgets)
        entrada_widget.clear()

def procesar_curacion(personaje_obj, entrada_widget, dicc_widgets):
    texto = entrada_widget.text()
    if texto.isdigit():
        cantidad = int(texto)
        personaje_obj.curar(cantidad)
        
        if "hp" in dicc_widgets:
            dicc_widgets["hp"].setValue(personaje_obj.hp)
            
        actualizar_color_hp(personaje_obj, dicc_widgets)
        entrada_widget.clear()

def ajustar_stat_secundario(personaje_obj, atributo, cantidad, barra_widget):
    personaje_obj.modificar_stat_secundario(atributo, cantidad)
    nuevo_valor = getattr(personaje_obj, atributo)
    barra_widget.setValue(nuevo_valor)

def ajustar_atributo_simple(personaje_obj, atributo, cantidad, label_widget):
    personaje_obj.modificar_atributo_simple(atributo, cantidad)
    nuevo_valor = getattr(personaje_obj, atributo)
    label_widget.setText(str(nuevo_valor))
    
def aplicar_dano_fijo(personaje_obj, cantidad, dicc_widgets):
    """Aplica daño directo al HP, ignorando armadura."""
    personaje_obj.aplicar_impacto(cantidad, es_cabeza=False, es_melee=False, es_directo=True)
    
    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)
        
    actualizar_color_hp(personaje_obj, dicc_widgets)

# ==========================================
# LÓGICA DE ARMAMENTO
# ==========================================

def ajustar_municion_arma(personaje_obj, nombre_arma, cantidad, lbl_widget):
    """Ajusta munición asegurando los límites (0 a max)."""
    if hasattr(personaje_obj, "armas") and nombre_arma in personaje_obj.armas:
        arma = personaje_obj.armas[nombre_arma]
        nueva_municion = max(0, min(arma["actual"] + cantidad, arma["max"]))
        arma["actual"] = nueva_municion
        lbl_widget.setText(str(nueva_municion))

def recargar_arma_maxima(personaje_obj, nombre_arma, lbl_widget):
    if hasattr(personaje_obj, "armas") and nombre_arma in personaje_obj.armas:
        arma = personaje_obj.armas[nombre_arma]
        arma["actual"] = arma["max"]
        lbl_widget.setText(str(arma["actual"]))

# ==========================================
# CONTROL DE ESTADO
# ==========================================
    
def resetear_personaje(personaje_obj, dicc_widgets):
    """Restaura todos los atributos al máximo y actualiza la UI."""
    personaje_obj.hp = personaje_obj.max_hp
    personaje_obj.body_sp = personaje_obj.max_body_sp
    personaje_obj.head_sp = personaje_obj.max_head_sp
    personaje_obj.luck = personaje_obj.max_luck
    personaje_obj.move = personaje_obj.max_move
    personaje_obj.death_penalty = 0
    
    if hasattr(personaje_obj, 'max_bullets'):
        personaje_obj.bullets = personaje_obj.max_bullets

    if "hp" in dicc_widgets:
        dicc_widgets["hp"].setValue(personaje_obj.hp)
        actualizar_color_hp(personaje_obj, dicc_widgets)
        
    for attr in ["body_sp", "head_sp", "luck", "move"]:
        if attr in dicc_widgets:
            dicc_widgets[attr].setValue(getattr(personaje_obj, attr))
            
    if hasattr(personaje_obj, "armas"):
        for nombre_arma, datos in personaje_obj.armas.items():
            datos["actual"] = datos["max"]
            if "armas" in dicc_widgets and nombre_arma in dicc_widgets["armas"]:
                dicc_widgets["armas"][nombre_arma].setText(str(datos["actual"]))
        
    if "death_penalty" in dicc_widgets:
        dicc_widgets["death_penalty"].setText(str(personaje_obj.death_penalty))
        
    if "debufos" in dicc_widgets:
        for combo in dicc_widgets["debufos"]:
            combo.setCurrentIndex(0) 

# ==========================================
# PERSISTENCIA DE DATOS (JSON)
# ==========================================

def guardar_partida(pjs, npcs, ruta_archivo="campana.json"):
    datos = {"jugadores": [], "adversarios": []}
    
    for p in pjs:
        datos["jugadores"].append({
            "nombre": p.nombre,
            "max_hp": p.max_hp, "hp": p.hp,
            "max_body_sp": p.max_body_sp, "body_sp": p.body_sp,
            "max_head_sp": p.max_head_sp, "head_sp": p.head_sp,
            "max_luck": p.max_luck, "luck": p.luck,
            "max_move": p.max_move, "move": p.move,
            "death_penalty": p.death_penalty,
            "armas": getattr(p, "armas", {})
        })
        
    for p in npcs:
        datos["adversarios"].append({
            "nombre": p.nombre,
            "max_hp": p.max_hp, "hp": p.hp,
            "max_body_sp": p.max_body_sp, "body_sp": p.body_sp,
            "max_head_sp": p.max_head_sp, "head_sp": p.head_sp,
            "max_luck": p.max_luck, "luck": p.luck,
            "max_move": p.max_move, "move": p.move,
            "death_penalty": p.death_penalty,
            "armas": getattr(p, "armas", {}),
            "mejoras": getattr(p, "mejoras", [])
        })
        
    with open(ruta_archivo, 'w', encoding='utf-8') as f:
        json.dump(datos, f, indent=4, ensure_ascii=False)

def cargar_partida(ruta_archivo="campana.json"):
    if not os.path.exists(ruta_archivo):
        return None, None
        
    with open(ruta_archivo, 'r', encoding='utf-8') as f:
        datos = json.load(f)
        
    pjs_cargados = []
    for d in datos.get("jugadores", []):
        pj = Personaje(
            d["nombre"], d["max_hp"], d["max_body_sp"], 
            d["max_head_sp"], d["max_luck"], d["max_move"], 
            d.get("armas", {}), d.get("death_penalty", 0)
        )
        pj.hp = d["hp"]
        pj.body_sp = d["body_sp"]
        pj.head_sp = d["head_sp"]
        pj.luck = d["luck"]
        pj.move = d["move"]
        pjs_cargados.append(pj)
        
    npcs_cargados = []
    for d in datos.get("adversarios", []):
        npc = Personaje(
            d["nombre"], d["max_hp"], d["max_body_sp"], 
            d["max_head_sp"], d["max_luck"], d["max_move"], 
            d.get("armas", {}), d.get("death_penalty", 0),
            d.get("mejoras", [])
        )
        npc.hp = d["hp"]
        npc.body_sp = d["body_sp"]
        npc.head_sp = d["head_sp"]
        npc.luck = d["luck"]
        npc.move = d["move"]
        npcs_cargados.append(npc)
        
    return pjs_cargados, npcs_cargados