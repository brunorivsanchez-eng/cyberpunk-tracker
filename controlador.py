# controlador.py
# ==========================================
# LÓGICA DE COMBATE Y MECÁNICAS PURAS
# ==========================================

def procesar_ataque(personaje_obj, cantidad_danio, es_cabeza, es_melee, es_directo):
    """Aplica daño a un personaje individual."""
    personaje_obj.aplicar_impacto(cantidad_danio, es_cabeza, es_melee, es_directo)

def procesar_ataque_aoe(lista_objetivos, danio_bruto, tipo_ataque):
    """Aplica daño en área a múltiples personajes (solo los modelos)."""
    for personaje_obj in lista_objetivos:
        if tipo_ataque == "Cuerpo (SP -1)":
            personaje_obj.aplicar_impacto(danio_bruto, es_cabeza=False, es_melee=False, es_directo=False, reduccion_sp=1)
        elif tipo_ataque == "Cuerpo (SP -2)":
            personaje_obj.aplicar_impacto(danio_bruto, es_cabeza=False, es_melee=False, es_directo=False, reduccion_sp=2)
        elif tipo_ataque == "Directo":
            personaje_obj.aplicar_impacto(danio_bruto, es_cabeza=False, es_melee=False, es_directo=True)

def aplicar_dano_fijo(personaje_obj, cantidad):
    """Aplica daño directo al HP, ignorando armadura."""
    personaje_obj.aplicar_impacto(cantidad, es_cabeza=False, es_melee=False, es_directo=True)

def procesar_curacion(personaje_obj, cantidad):
    """Restaura HP al personaje."""
    personaje_obj.curar(cantidad)

def ajustar_stat_secundario(personaje_obj, atributo, cantidad):
    """Modifica estadísticas secundarias (Luck, Move)."""
    personaje_obj.modificar_stat_secundario(atributo, cantidad)

def ajustar_atributo_simple(personaje_obj, atributo, cantidad):
    """Modifica atributos numéricos simples (Ej. penalización de muerte)."""
    personaje_obj.modificar_atributo_simple(atributo, cantidad)

def ajustar_municion_arma(personaje_obj, nombre_arma, cantidad):
    """Suma o resta munición a un arma específica."""
    if hasattr(personaje_obj, "armas") and nombre_arma in personaje_obj.armas:
        arma = personaje_obj.armas[nombre_arma]
        arma["actual"] = max(0, min(arma["actual"] + cantidad, arma["max"]))

def recargar_arma_maxima(personaje_obj, nombre_arma):
    """Restaura la munición al máximo."""
    if hasattr(personaje_obj, "armas") and nombre_arma in personaje_obj.armas:
        arma = personaje_obj.armas[nombre_arma]
        arma["actual"] = arma["max"]

def resetear_personaje_logico(personaje_obj):
    """Restaura todos los atributos del modelo a sus valores máximos/iniciales."""
    personaje_obj.hp = personaje_obj.max_hp
    personaje_obj.body_sp = personaje_obj.max_body_sp
    personaje_obj.head_sp = personaje_obj.max_head_sp
    personaje_obj.luck = personaje_obj.max_luck
    personaje_obj.move = personaje_obj.max_move
    personaje_obj.death_penalty = 0
    
    if hasattr(personaje_obj, "debufos_permanentes_ids"):
        personaje_obj.debufos_permanentes_ids.clear()
            
    if hasattr(personaje_obj, "armas"):
        for nombre_arma, datos in personaje_obj.armas.items():
            datos["actual"] = datos["max"]