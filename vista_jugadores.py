import os
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QLabel, 
                             QPushButton, QLineEdit, QCheckBox, QComboBox, QScrollArea, QFrame, QHBoxLayout)

from ui.ui_tarjetas import PersonajeWidget

class TarjetaNPCNarrativa(QFrame):
    """Tarjeta que muestra a los NPCs sin números, pero CON estados alterados."""
    def __init__(self, npc_obj, estados_activos):
        super().__init__()
        self.setObjectName("ContenedorPersonaje")
        self.setStyleSheet("border: 1px solid #8B0000; margin-bottom: 2px;")
        layout = QHBoxLayout(self)
        
        # ====================================================================
        # LÓGICA DIRECTA: Facción para genéricos, Nombre real para únicos
        # ====================================================================
        nombre_completo = npc_obj.nombre
        faccion = getattr(npc_obj, 'faccion', None)
        
        if faccion and faccion.strip() != "":
            # TIENE FACCIÓN: Es genérico. Mostramos Facción + (Color/Icono)
            etiqueta_identificadora = ""
            if "(" in nombre_completo and ")" in nombre_completo:
                etiqueta_identificadora = nombre_completo[nombre_completo.rfind("("):]
            
            nombre_mostrar = f"{faccion} {etiqueta_identificadora}".strip().upper()
        else:
            # NO TIENE FACCIÓN: Es importante. Mostramos su nombre tal cual.
            nombre_mostrar = nombre_completo.upper()
        
        # Asignamos el nombre final a la tarjeta
        lbl_nombre = QLabel(nombre_mostrar)
        color = getattr(npc_obj, 'color_token_hex', "#FF0000")
        lbl_nombre.setStyleSheet(f"color: {color}; font-weight: bold; font-family: 'Orbitron'; font-size: 14px; border: none;")
        # ====================================================================
        
        porcentaje = (npc_obj.hp / npc_obj.max_hp) * 100 if npc_obj.max_hp > 0 else 0
        if porcentaje > 75: estado, color_est = "INTACTO", "#00FF00"
        elif porcentaje > 25: estado, color_est = "HERIDO", "#FFFF00"
        elif porcentaje > 0: estado, color_est = "MORIBUNDO", "#FF0000"
        else: estado, color_est = "ELIMINADO", "#555555"
            
        lbl_estado = QLabel(f"[{estado}]")
        lbl_estado.setStyleSheet(f"color: {color_est}; font-weight: bold; font-family: 'Consolas'; font-size: 14px; border: none;")
        
        if estados_activos:
            texto_estados = "⚠️ " + " | ".join(estados_activos)
            lbl_info = QLabel(texto_estados)
            lbl_info.setStyleSheet("color: #FFA500; font-weight: bold; border: none; font-size: 12px;")
        else:
            lbl_info = QLabel("Escaneo táctico: Sin alteraciones.")
            lbl_info.setStyleSheet("color: #444; font-style: italic; border: none; font-size: 10px;")

        layout.addWidget(lbl_nombre)
        layout.addWidget(lbl_estado)
        layout.addStretch()
        layout.addWidget(lbl_info)

class PantallaJugadores(QMainWindow):
    def __init__(self, cat_temp, cat_perm):
        super().__init__()
        self.setWindowTitle("Cyberpunk RED - Pantalla Jugadores")
        self.resize(1000, 800)
        self.cat_temp = cat_temp
        self.cat_perm = cat_perm

        dir_path = os.path.dirname(os.path.abspath(__file__))
        ruta_qss = os.path.join(dir_path, "estilos.qss")
        if os.path.exists(ruta_qss):
            with open(ruta_qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.setCentralWidget(self.scroll)

        self.widget_central = QWidget()
        self.layout_principal = QVBoxLayout(self.widget_central)
        self.scroll.setWidget(self.widget_central)

    def actualizar_desde_memoria(self, registro_personajes):
        while self.layout_principal.count():
            item = self.layout_principal.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        lbl_aliados = QLabel("─── ESCUADRA ───")
        lbl_aliados.setStyleSheet("color: #00FFFF; font-size: 16px; font-weight: bold; border: none; background: transparent;")
        self.layout_principal.addWidget(lbl_aliados)

        hay_npcs = False
        
        for personaje_obj, widget_master in registro_personajes:
            if not personaje_obj.es_npc:
                tarjeta = PersonajeWidget(personaje_obj, self.cat_temp, self.cat_perm, es_npc=False)

                # ==============================================================
                # ARREGLO: COPIAR LOS ESTADOS DEL MÁSTER AL JUGADOR
                # ==============================================================
                # Temporales
                if "debufos_temp" in widget_master.widgets_referencia and "debufos_temp" in tarjeta.widgets_referencia:
                    combos_m = widget_master.widgets_referencia["debufos_temp"]
                    combos_j = tarjeta.widgets_referencia["debufos_temp"]
                    # Si el máster añadió combos con el botón '+', hacemos lo mismo aquí
                    while len(combos_j) < len(combos_m) and "btn_add_temp" in tarjeta.widgets_referencia:
                        tarjeta.widgets_referencia["btn_add_temp"].click()
                    # Igualamos lo que dice cada menú
                    for cm, cj in zip(combos_m, combos_j):
                        cj.setCurrentIndex(cm.currentIndex())

                # Permanentes
                if "debufos_perm" in widget_master.widgets_referencia and "debufos_perm" in tarjeta.widgets_referencia:
                    combos_m = widget_master.widgets_referencia["debufos_perm"]
                    combos_j = tarjeta.widgets_referencia["debufos_perm"]
                    while len(combos_j) < len(combos_m) and "btn_add_perm" in tarjeta.widgets_referencia:
                        tarjeta.widgets_referencia["btn_add_perm"].click()
                    for cm, cj in zip(combos_m, combos_j):
                        cj.setCurrentIndex(cm.currentIndex())
                # ==============================================================

                for w in tarjeta.findChildren((QPushButton, QLineEdit, QCheckBox)): w.hide()
                for c in tarjeta.findChildren(QComboBox): 
                    c.setEnabled(False)
                    c.setStyleSheet("color: #FFA500; background: transparent; border: none;")
                self.layout_principal.addWidget(tarjeta)
            else:
                hay_npcs = True

        if hay_npcs:
            lbl_enemigos = QLabel("─── AMENAZAS DETECTADAS ───")
            lbl_enemigos.setStyleSheet("color: #FF0000; font-size: 16px; font-weight: bold; margin-top: 20px; border: none; background: transparent;")
            self.layout_principal.addWidget(lbl_enemigos)

            for personaje_obj, widget_master in registro_personajes:
                if personaje_obj.es_npc and personaje_obj.hp > 0: 
                    
                    estados_activos = []
                    if "debufos_temp" in widget_master.widgets_referencia:
                        for combo in widget_master.widgets_referencia["debufos_temp"]:
                            texto = combo.currentText()
                            if texto and texto != "---": estados_activos.append(texto)
                            
                    if "debufos_perm" in widget_master.widgets_referencia:
                        for combo in widget_master.widgets_referencia["debufos_perm"]:
                            texto = combo.currentText()
                            if texto and texto != "---": estados_activos.append(texto)
                            
                    tarjeta_npc = TarjetaNPCNarrativa(personaje_obj, estados_activos)
                    self.layout_principal.addWidget(tarjeta_npc)

        self.layout_principal.addStretch()