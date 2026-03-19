def actualizar_color_hp(personaje_obj, barra_widget):
    """Evalúa la vida actual y cambia el color de la barra."""
    mitad_hp = personaje_obj.max_hp // 2
    
    if personaje_obj.hp <= mitad_hp:
        # Rojo (Peligro)
        barra_widget.setStyleSheet("QProgressBar::chunk { background-color: #FF4444; }") 
    else:
        # Verde menos brillante (Saludable)
        barra_widget.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }") 

def procesar_ataque(personaje_obj, entrada_widget, es_cabeza, es_melee, es_directo, dicc_widgets):
    texto = entrada_widget.text()
    if texto.isdigit():
        danio = int(texto)
        personaje_obj.aplicar_impacto(danio, es_cabeza, es_melee, es_directo)
        
        for attr in ["hp", "body_sp", "head_sp"]:
            if attr in dicc_widgets:
                dicc_widgets[attr].setValue(getattr(personaje_obj, attr))
        
        # --- NUEVO: Actualizar el color de la barra HP después del daño ---
        if "hp" in dicc_widgets:
            actualizar_color_hp(personaje_obj, dicc_widgets["hp"])
            
        entrada_widget.clear()

def procesar_curacion(personaje_obj, entrada_widget, dicc_widgets):
    texto = entrada_widget.text()
    if texto.isdigit():
        cantidad = int(texto)
        personaje_obj.curar(cantidad)
        
        if "hp" in dicc_widgets:
            dicc_widgets["hp"].setValue(personaje_obj.hp)
            # --- NUEVO: Actualizar el color de la barra HP después de curar ---
            actualizar_color_hp(personaje_obj, dicc_widgets["hp"])
            
        entrada_widget.clear()

def ajustar_stat_secundario(personaje_obj, atributo, cantidad, barra_widget):
    personaje_obj.modificar_stat_secundario(atributo, cantidad)
    nuevo_valor = getattr(personaje_obj, atributo)
    barra_widget.setValue(nuevo_valor)