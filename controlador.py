# controlador.py
import random

# ==========================================
# LÓGICA DE COMBATE Y MECÁNICAS PURAS
# ==========================================

def procesar_impacto_unificado(personaje_obj, dano_base, mitad_sp, ignora_sp, cabeza, craneo, sin_abrasion, explosivo):
    """
    Punto de entrada desde la UI unificada. Enruta los parámetros de los checkboxes 
    al método interno de cálculo matemático del modelo.
    """
    personaje_obj.procesar_impacto(
        dano_base=dano_base,
        mitad_sp=mitad_sp,
        ignora_sp=ignora_sp,
        cabeza=cabeza,
        craneo=craneo,
        sin_abrasion=sin_abrasion,
        explosivo=explosivo
    )

def procesar_ataque_aoe(lista_objetivos, danio_bruto, tipo_ataque):
    """Aplica daño en área a múltiples personajes adaptado a la nueva lógica."""
    for personaje_obj in lista_objetivos:
        if tipo_ataque == "Cuerpo (SP -1)":
            # Normal: daño_base, mitad_sp, ignora_sp, cabeza, craneo, sin_abrasion, explosivo
            personaje_obj.procesar_impacto(danio_bruto, False, False, False, False, False, False)
        elif tipo_ataque == "Cuerpo (SP -2)":
            # Explosivo
            personaje_obj.procesar_impacto(danio_bruto, False, False, False, False, False, True)
        elif tipo_ataque == "Directo":
            # Ignora SP y No Abrasa
            personaje_obj.procesar_impacto(danio_bruto, False, True, False, False, True, False)

def aplicar_dano_fijo(personaje_obj, cantidad):
    """Aplica daño directo al HP (como botones de fuego), ignorando armadura y sin abrasión."""
    personaje_obj.procesar_impacto(cantidad, False, True, False, False, True, False)

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


# =============================================================================
# MOTOR DE COMBATE: TIRADAS DE DADOS Y REGLAS
# =============================================================================
def generar_tirada_ataque(nombre_arma, base, dados_dano, es_autofuego=False, mod_situacional=0):
    """
    Calcula la tirada de ataque y daño siguiendo las reglas de Cyberpunk Red.
    Incluye un modificador situacional (heridas, puntería, etc.) enviado desde la UI.
    Devuelve un string en formato HTML estructurado para el panel de la tarjeta.
    """
    # 1. Lógica de Ataque (1d10 explosivo)
    dado_base = random.randint(1, 10)
    dado_final = dado_base
    
    color_ataque = "#FFFFFF" # Blanco por defecto
    texto_dado = str(dado_base)
    etiqueta_critico = ""

    # Regla de Crítico (10 explosivo)
    if dado_base == 10:
        dado_extra = random.randint(1, 10)
        dado_final += dado_extra
        color_ataque = "#00FF00" # Verde Brillante
        texto_dado = f"10 + {dado_extra}"
        etiqueta_critico = " <b style='color: #00FF00;'>[CRÍTICO]</b>"
    
    # Regla de Pifia (1 explosivo)
    elif dado_base == 1:
        dado_extra = random.randint(1, 10)
        dado_final -= dado_extra
        color_ataque = "#FF0000" # Rojo Brillante
        texto_dado = f"1 - {dado_extra}"
        etiqueta_critico = " <b style='color: #FF0000;'>[PIFIA]</b>"

    # CÁLCULO FINAL DE ATAQUE: Base + Dado + Modificador Situacional
    resultado_ataque = base + dado_final + mod_situacional
    
    # Formateo del texto del modificador para el desglose visual
    txt_mod = ""
    if mod_situacional > 0:
        txt_mod = f" + {mod_situacional}"
    elif mod_situacional < 0:
        txt_mod = f" - {abs(mod_situacional)}"

    # Línea de Ataque en HTML
    linea_ataque = (
        f"<span style='color: #DDDDDD;'>ATAQUE: </span>"
        f"<b style='color: {color_ataque}; font-size: 13px;'>{resultado_ataque}</b> "
        f"<small style='color: #AAAAAA;'>(Base {base} + Dado {texto_dado}{txt_mod}){etiqueta_critico}</small>"
    )

    # 2. Lógica de Daño (Nd6)
    linea_dano = ""
    if not es_autofuego and dados_dano > 0:
        tiradas_d6 = [random.randint(1, 6) for _ in range(dados_dano)]
        suma_dano = sum(tiradas_d6)
        seises = tiradas_d6.count(6)
        
        texto_tiradas = ", ".join(map(str, tiradas_d6))
        
        color_dano = "#FFFFFF"
        etiqueta_herida = ""
        
        # Regla de Herida Crítica (2 o más seises)
        if seises >= 2:
            color_dano = "#00FF00" 
            etiqueta_herida = f" <b style='color: #00FF00;'>+5</b> <i style='color: #00FF00;'>[HERIDA CRÍTICA]</i>"

        linea_dano = (
            f"<br><span style='color: #DDDDDD;'>DAÑO: </span>"
            f"<b style='color: {color_dano}; font-size: 13px;'>{suma_dano}</b> "
            f"<small style='color: #AAAAAA;'>({texto_tiradas})</small>{etiqueta_herida}"
        )

    # 3. Ensamblaje Final
    header = f"<b style='color: #FFFFFF; font-size: 12px;'>{nombre_arma.upper()}</b>"
    if es_autofuego:
        header += " <b style='color: #FFA500;'>(Fuego Automático)</b>"

    return f"{header}<br>{linea_ataque}{linea_dano}"

def generar_tirada_iniciativa(base_iniciativa):
    """
    Calcula la tirada de iniciativa (1d10 explosivo + Base).
    Devuelve un string en formato HTML para el panel de UI.
    """
    dado_base = random.randint(1, 10)
    dado_final = dado_base
    color_dado = "#FFFFFF"
    texto_dado = str(dado_base)
    etiqueta_critico = ""

    if dado_base == 10:
        dado_extra = random.randint(1, 10)
        dado_final += dado_extra
        color_dado = "#00FF00" 
        texto_dado = f"10 + {dado_extra}"
        etiqueta_critico = " <b style='color: #00FF00;'>[CRÍTICO]</b>"
    elif dado_base == 1:
        dado_extra = random.randint(1, 10)
        dado_final -= dado_extra
        color_dado = "#FF0000" 
        texto_dado = f"1 - {dado_extra}"
        etiqueta_critico = " <b style='color: #FF0000;'>[PIFIA]</b>"

    resultado_total = base_iniciativa + dado_final
    
    html = (
        f"<b style='color: #00FFFF; font-size: 13px;'>⚡ INICIATIVA: {resultado_total}</b><br>"
        f"<span style='color: #AAAAAA; font-size: 11px;'>(Base {base_iniciativa} + Dado "
        f"<span style='color: {color_dado};'>{texto_dado}</span>){etiqueta_critico}</span>"
    )
    
    return html