from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QFrame, QLabel, QPushButton, 
                             QComboBox, QLineEdit, QProgressBar, 
                             QSizePolicy,)
from PyQt6.QtCore import (Qt , pyqtSignal)
import controlador

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

class PersonajeWidget(QFrame):
    solicitar_eliminacion = pyqtSignal(object) # object recibirá el personaje_obj
    def __init__(self, personaje_obj, cat_temporales, cat_permanentes, es_npc=False):
        super().__init__()
        self.personaje_obj = personaje_obj
        self.es_npc = es_npc
        self.widgets_referencia = {}
        
        self.setObjectName("ContenedorPersonaje")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # --- NUEVO: BORDE DORADO SI ES BOSS ---
        # En ui/ui_tarjetas.py -> __init__
        if es_npc and getattr(personaje_obj, 'es_boss', False):
            self.setStyleSheet("""
                QFrame#ContenedorPersonaje { 
                    border: 2px solid #FF0000;  /* Borde Rojo Neón para el Boss */
                    background-color: #0A0000;  /* Fondo casi negro con tinte rojo */
                }
            """)
        # ----------------------------------------
        
        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(8, 8, 8, 8)
        layout_principal.setSpacing(5)
        
        # --- CABECERA: NOMBRE Y BOTÓN RESET ---
        fila_cabecera = QHBoxLayout()
        
        lbl_nombre = QLabel(personaje_obj.nombre.upper())
        lbl_nombre.setObjectName("NombrePJ")
        self.widgets_referencia["nombre"] = lbl_nombre 
        
        btn_reset = QPushButton("🔄RESET🔄")
        btn_reset.setFixedWidth(65)
        btn_reset.setObjectName("BtnReset")
        btn_reset.clicked.connect(lambda checked: self._ui_resetear())
        
        fila_cabecera.addWidget(lbl_nombre)
        fila_cabecera.addStretch(1)
        fila_cabecera.addWidget(btn_reset)
        # --- NUEVO: BOTÓN 'X' PARA ELIMINAR NPC ---
        if es_npc:
            btn_cerrar = QPushButton("❌")
            btn_cerrar.setFixedSize(22, 22)
            btn_cerrar.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #8B0000;
                    border: 1px solid #8B0000;
                    border-radius: 4px;
                    font-weight: bold;
                    font-size: 10px;
                }
                QPushButton:hover {
                    background-color: #8B0000;
                    color: white;
                }
            """)
            # Emitir la señal de borrado pasándole el personaje actual
            # Añade el espacio entre lambda y checked
            btn_cerrar.clicked.connect(lambda checked: self.solicitar_eliminacion.emit(personaje_obj))
            fila_cabecera.addWidget(btn_cerrar)
        # ----------------------------------------
        layout_principal.addLayout(fila_cabecera)

        # --- FILA 1: HP Y COMBATE ---
        fila_hp = QHBoxLayout()
        
        lbl_hp = QLabel("HP")
        lbl_hp.setFixedWidth(60)
        lbl_hp.setObjectName("LblStatTit")
        
        barra_hp = QProgressBar()
        barra_hp.setRange(0, personaje_obj.max_hp)
        barra_hp.setValue(personaje_obj.hp)
        barra_hp.setFormat("%v / %m") 
        barra_hp.setFixedWidth(225)
        barra_hp.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.widgets_referencia["hp"] = barra_hp
        
        self.input_dano = QLineEdit()
        self.input_dano.setFixedWidth(38)
        self.input_dano.setPlaceholderText("0")
        
        fila_hp.addWidget(lbl_hp)
        fila_hp.addWidget(barra_hp)
        fila_hp.addWidget(self.input_dano)

        ataques = [
            ("Cuerpo", False, False, False),
            ("Cabeza", True, False, False),
            ("M. Cuerpo", False, True, False),
            ("M. Cabeza", True, True, False),
            ("⚡ Directo", False, False, True)
        ]

        for texto, cabeza, melee, directo in ataques:
            btn = QPushButton(texto)
            btn.clicked.connect(lambda checked, c=cabeza, m=melee, d=directo: self._ui_procesar_ataque(c, m, d))
            fila_hp.addWidget(btn)

        if not es_npc:
            btn_curar = QPushButton("💚 Curar")
            btn_curar.setObjectName("BtnCurar")
            btn_curar.clicked.connect(lambda checked: self._ui_procesar_curacion())
            fila_hp.addWidget(btn_curar)

        fila_hp.addStretch(1)
        layout_principal.addLayout(fila_hp)

        # --- FILA 2: ESTADÍSTICAS AMPLIADAS ---
        layout_stats_ampliado = QHBoxLayout()
        layout_stats_ampliado.setContentsMargins(0, 0, 0, 0)
        layout_stats_ampliado.setSpacing(25)
        
        # COLUMNA IZQUIERDA: SP Y SUERTE
        columna_izquierda = QWidget()
        layout_col_izq = QVBoxLayout(columna_izquierda)
        layout_col_izq.setContentsMargins(0, 0, 0, 0)
        layout_col_izq.setSpacing(5)

        stats_secundarios = [
            ("BODY SP", "body_sp", "max_body_sp"),
            ("HEAD SP", "head_sp", "max_head_sp"),
            ("MOVE", "move", "max_move")
        ]
        if not es_npc:
            stats_secundarios.append(("LUCK", "luck", "max_luck"))

        for nombre_ui, attr, attr_max in stats_secundarios:
            fila = QHBoxLayout()
            
            lbl = QLabel(nombre_ui)
            lbl.setFixedWidth(60)
            lbl.setObjectName("LblStatTit")
            
            barra = QProgressBar()
            barra.setRange(0, getattr(personaje_obj, attr_max))
            barra.setValue(getattr(personaje_obj, attr))
            barra.setFormat("%v / %m") 
            barra.setObjectName(f"Barra{attr.replace('_', '').upper()}")
            barra.setFixedWidth(115)
            self.widgets_referencia[attr] = barra
            
            btn_menos = QPushButton("-")
            btn_menos.setObjectName("BtnAjuste")
            btn_menos.setFixedWidth(24)
            btn_menos.clicked.connect(lambda checked, a=attr, cant=-1: self._ui_ajustar_stat(a, cant))
            
            btn_mas = QPushButton("+")
            btn_mas.setObjectName("BtnAjuste")
            btn_mas.setFixedWidth(24)
            btn_mas.clicked.connect(lambda checked, a=attr, cant=1: self._ui_ajustar_stat(a, cant))

            fila.addWidget(lbl)
            fila.addWidget(barra)
            fila.addWidget(btn_menos)
            fila.addWidget(btn_mas)
            fila.addStretch(1)
            layout_col_izq.addLayout(fila)

        # --- COLUMNA 2: MUERTE Y FUEGO ---
        columna_derecha = QWidget()
        layout_col_der = QVBoxLayout(columna_derecha)
        layout_col_der.setContentsMargins(0, 0, 0, 0)
        layout_col_der.setSpacing(4)

        if not es_npc:
            fila_death = QHBoxLayout()
            lbl_death_tit = QLabel("💀☠️💀")
            lbl_death_tit.setFixedWidth(60)
            lbl_death_tit.setObjectName("LblStatTit")

            lbl_val_death = QLabel(str(personaje_obj.death_penalty))
            lbl_val_death.setFixedWidth(25)
            lbl_val_death.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl_val_death.setObjectName("ValorDeathPenalty")
            self.widgets_referencia["death_penalty"] = lbl_val_death

            btn_menos_d = QPushButton("-")
            btn_menos_d.setObjectName("BtnAjuste")
            btn_menos_d.setFixedWidth(24)
            btn_menos_d.clicked.connect(lambda checked, c=-1: self._ui_ajustar_simple("death_penalty", c))
            
            btn_mas_d = QPushButton("+")
            btn_mas_d.setObjectName("BtnAjuste")
            btn_mas_d.setFixedWidth(24)
            btn_mas_d.clicked.connect(lambda checked, c=1: self._ui_ajustar_simple("death_penalty", c))

            fila_death.addWidget(lbl_death_tit)
            fila_death.addWidget(lbl_val_death)
            fila_death.addWidget(btn_menos_d)
            fila_death.addWidget(btn_mas_d)
            fila_death.addStretch(1)
            layout_col_der.addLayout(fila_death)

        # Fila Fuego
        fila_fuego = QHBoxLayout()
        lbl_fuego_tit = QLabel("🔥Fire🔥")
        lbl_fuego_tit.setFixedWidth(60)
        lbl_fuego_tit.setObjectName("LblFuegoTit")

        btn_fuego_5 = QPushButton("🔥")
        btn_fuego_5.setObjectName("BtnFuego")
        btn_fuego_5.setFixedWidth(38)
        btn_fuego_5.clicked.connect(lambda checked, c=5: self._ui_dano_fijo(c))

        btn_fuego_10 = QPushButton("🔥🔥🔥")
        btn_fuego_10.setObjectName("BtnFuego")
        btn_fuego_10.setFixedWidth(50)
        btn_fuego_10.clicked.connect(lambda checked, c=10: self._ui_dano_fijo(c))

        fila_fuego.addWidget(lbl_fuego_tit)
        fila_fuego.addWidget(btn_fuego_5)
        fila_fuego.addWidget(btn_fuego_10)
        fila_fuego.addStretch(1)
        layout_col_der.addLayout(fila_fuego)
        layout_col_der.addStretch(1)

        # --- COLUMNA 3: MUNICIÓN DINÁMICA ---
        columna_armas = QWidget()
        layout_col_armas = QVBoxLayout(columna_armas)
        layout_col_armas.setContentsMargins(15, 0, 0, 0)
        layout_col_armas.setSpacing(4)

        lbl_armas_tit = QLabel("MUNICIÓN")
        lbl_armas_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_armas_tit.setObjectName("TituloColumnaArmas")
        layout_col_armas.addWidget(lbl_armas_tit)

        self.widgets_referencia["armas"] = {}

        if hasattr(personaje_obj, "armas") and personaje_obj.armas:
            for nombre_arma, datos_arma in personaje_obj.armas.items():
                fila_arma = QWidget()
                layout_fila_arma = QHBoxLayout(fila_arma)
                layout_fila_arma.setContentsMargins(0, 0, 0, 0)
                layout_fila_arma.setSpacing(2) 
                
                lbl_nombre_arma = QLabel(nombre_arma)
                lbl_nombre_arma.setFixedWidth(70) 
                lbl_nombre_arma.setWordWrap(True) 
                lbl_nombre_arma.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                lbl_nombre_arma.setObjectName("LblNombreArma")

                if "efecto" in datos_arma and datos_arma["efecto"]:
                    texto_tooltip = f"""
                    <div style='background-color: #1E1E1E; color: #FFD700; padding: 5px; border: 1px solid #555555; font-family: Arial; font-size: 12px;'>
                        <b>{nombre_arma}</b><br>
                        <span style='color: #FFFFFF;'>Efecto: {datos_arma['efecto']}</span>
                    </div>
                    """
                    lbl_nombre_arma.setToolTip(texto_tooltip)
                    lbl_nombre_arma.setCursor(Qt.CursorShape.WhatsThisCursor)

                layout_fila_arma.addWidget(lbl_nombre_arma)

                if datos_arma["max"] > 0:
                    lbl_val_arma = QLabel(str(datos_arma["actual"]))
                    lbl_val_arma.setFixedWidth(25)
                    lbl_val_arma.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignCenter)
                    lbl_val_arma.setObjectName("LblValArma")
                    
                    self.widgets_referencia["armas"][nombre_arma] = lbl_val_arma

                    btn_menos_10 = QPushButton("-10")
                    btn_menos_10.setObjectName("BtnAjuste")
                    btn_menos_10.setFixedWidth(26)
                    btn_menos_10.clicked.connect(lambda checked, n=nombre_arma, c=-10: self._ui_ajustar_municion(n, c))
                                                 
                    btn_menos_1 = QPushButton("-1")
                    btn_menos_1.setObjectName("BtnAjuste")
                    btn_menos_1.setFixedWidth(26)
                    btn_menos_1.clicked.connect(lambda checked, n=nombre_arma, c=-1: self._ui_ajustar_municion(n, c))

                    btn_max = QPushButton("MAX")
                    btn_max.setObjectName("BtnAjuste")
                    btn_max.setFixedWidth(32)
                    btn_max.clicked.connect(lambda checked, n=nombre_arma: self._ui_recargar_max(n))

                    layout_fila_arma.addWidget(lbl_val_arma)
                    layout_fila_arma.addWidget(btn_menos_10)
                    layout_fila_arma.addWidget(btn_menos_1)
                    layout_fila_arma.addWidget(btn_max)
                    layout_fila_arma.addStretch(1)
                else:
                    layout_fila_arma.addStretch(1) 
                    lbl_melee = QLabel("Cuerpo a Cuerpo")
                    lbl_melee.setAlignment(Qt.AlignmentFlag.AlignCenter) 
                    lbl_melee.setObjectName("LblTextoGris")
                    layout_fila_arma.addWidget(lbl_melee)
                    layout_fila_arma.addStretch(1) 
                
                layout_col_armas.addWidget(fila_arma)
        else:
            lbl_sin_armas = QLabel("Sin armas equipadas")
            lbl_sin_armas.setObjectName("LblTextoGris")
            layout_col_armas.addWidget(lbl_sin_armas)

        layout_col_armas.addStretch(1)

        # --- COLUMNA 4: ESTADOS Y HERIDAS CRÍTICAS ---
        columna_estados = QWidget()
        layout_col_est_principal = QHBoxLayout(columna_estados) 
        layout_col_est_principal.setContentsMargins(15, 0, 0, 0)
        layout_col_est_principal.setSpacing(10)

        self.widgets_referencia["debufos_temp"] = []
        self.widgets_referencia["debufos_perm"] = []

        if not hasattr(personaje_obj, "debufos_permanentes_ids"):
            personaje_obj.debufos_permanentes_ids = []

        # Funciones auxiliares UI para estados
        def actualizar_tooltip_y_modelo(combo_box, es_permanente):
            idx = combo_box.currentIndex()
            if idx >= 0:
                tooltip = combo_box.itemData(idx, Qt.ItemDataRole.ToolTipRole)
                combo_box.setToolTip(tooltip if tooltip else "")
            
            if es_permanente and not personaje_obj.es_npc:
                personaje_obj.debufos_permanentes_ids.clear()
                for c in self.widgets_referencia["debufos_perm"]:
                    id_deb = c.currentData(Qt.ItemDataRole.UserRole)
                    if id_deb:
                        personaje_obj.debufos_permanentes_ids.append(id_deb)

        def remover_combo(layout_destino, lista_referencias, es_permanente):
            if len(lista_referencias) > 1:
                combo_removido = lista_referencias.pop()
                layout_destino.removeWidget(combo_removido)
                combo_removido.deleteLater()
                if es_permanente and not personaje_obj.es_npc:
                    actualizar_tooltip_y_modelo(lista_referencias[0], es_permanente)

        def agregar_combo_debufo(layout_destino, lista_catalogo, lista_referencias, es_permanente):
            combo = NoScrollComboBox()
            combo.setFixedWidth(160)
            
            for index, item in enumerate(lista_catalogo):
                combo.addItem(item["nombre"], userData=item.get("id_debufo"))
                
                if item.get("tipo") == "Permanente" and item["nombre"] != "---":
                    tooltip = f"""
                    <div style='background-color: #1E1E1E; color: #FFD700; padding: 5px; border: 1px solid #555555; font-family: Arial; font-size: 11px;'>
                        <b>{item['nombre']}</b><br>
                        <span style='color: #FFFFFF;'>{item['descripcion']}</span><br><br>
                        <span style='color: #00FFFF;'><b>Remedio Rápido:</b> {item.get('remedio_rapido', 'N/D')}</span><br>
                        <span style='color: #00FF00;'><b>Tratamiento:</b> {item.get('tratamiento', 'N/D')}</span>
                    </div>
                    """
                else:
                    tooltip = f"""
                    <div style='background-color: #1E1E1E; color: #FFD700; padding: 5px; border: 1px solid #555555; font-family: Arial; font-size: 11px;'>
                        <b>{item['nombre']}</b><br>
                        <span style='color: #FFFFFF;'>{item['descripcion']}</span>
                    </div>
                    """
                combo.setItemData(index, tooltip, Qt.ItemDataRole.ToolTipRole)

            posicion_insercion = layout_destino.count() - 1
            layout_destino.insertWidget(posicion_insercion, combo)
            lista_referencias.append(combo)

            combo.currentIndexChanged.connect(lambda idx, cb=combo: actualizar_tooltip_y_modelo(cb, es_permanente))
            actualizar_tooltip_y_modelo(combo, es_permanente)
            return combo

        # SUB-COLUMNA A: ESTADOS TEMPORALES
        col_temp = QWidget()
        layout_temp = QVBoxLayout(col_temp)
        layout_temp.setContentsMargins(0, 0, 0, 0)
        layout_temp.setSpacing(4)
        
        header_temp = QWidget()
        h_layout_temp = QHBoxLayout(header_temp)
        h_layout_temp.setContentsMargins(0, 0, 0, 0)
        
        lbl_tit_temp = QLabel("⚠️ TEMPORALES")
        lbl_tit_temp.setObjectName("LblTitTemp")
        
        btn_add_temp = QPushButton("+")
        btn_add_temp.setFixedSize(20, 20)
        btn_add_temp.setObjectName("BtnAddRemove")
        btn_add_temp.clicked.connect(lambda checked, l=layout_temp, c=cat_temporales, ref=self.widgets_referencia["debufos_temp"]: agregar_combo_debufo(l, c, ref, False))
        self.widgets_referencia["btn_add_temp"] = btn_add_temp
        
        btn_remove_temp = QPushButton("-")
        btn_remove_temp.setFixedSize(20, 20)
        btn_remove_temp.setObjectName("BtnAddRemove")
        btn_remove_temp.clicked.connect(lambda checked, l=layout_temp, ref=self.widgets_referencia["debufos_temp"]: remover_combo(l, ref, False))
        
        h_layout_temp.addWidget(lbl_tit_temp)
        h_layout_temp.addWidget(btn_add_temp)
        h_layout_temp.addWidget(btn_remove_temp)
        h_layout_temp.addStretch(1)
        
        layout_temp.addWidget(header_temp)
        layout_temp.addStretch(1) 

        agregar_combo_debufo(layout_temp, cat_temporales, self.widgets_referencia["debufos_temp"], False)

        # SUB-COLUMNA B: HERIDAS CRÍTICAS
        col_perm = QWidget()
        layout_perm = QVBoxLayout(col_perm)
        layout_perm.setContentsMargins(0, 0, 0, 0)
        layout_perm.setSpacing(4)
        
        header_perm = QWidget()
        h_layout_perm = QHBoxLayout(header_perm)
        h_layout_perm.setContentsMargins(0, 0, 0, 0)
        
        lbl_tit_perm = QLabel("🏥 CRÍTICAS")
        lbl_tit_perm.setObjectName("LblTitPerm")
        
        btn_add_perm = QPushButton("+")
        btn_add_perm.setFixedSize(20, 20)
        btn_add_perm.setObjectName("BtnAddRemove")
        btn_add_perm.clicked.connect(lambda checked, l=layout_perm, c=cat_permanentes, ref=self.widgets_referencia["debufos_perm"]: agregar_combo_debufo(l, c, ref, True))
        self.widgets_referencia["btn_add_perm"] = btn_add_perm
        
        btn_remove_perm = QPushButton("-")
        btn_remove_perm.setFixedSize(20, 20)
        btn_remove_perm.setObjectName("BtnAddRemove")
        btn_remove_perm.clicked.connect(lambda checked, l=layout_perm, ref=self.widgets_referencia["debufos_perm"]: remover_combo(l, ref, True))
        
        h_layout_perm.addWidget(lbl_tit_perm)
        h_layout_perm.addWidget(btn_add_perm)
        h_layout_perm.addWidget(btn_remove_perm)
        h_layout_perm.addStretch(1)
        
        layout_perm.addWidget(header_perm)
        layout_perm.addStretch(1) 

        if not personaje_obj.es_npc and personaje_obj.debufos_permanentes_ids:
            ids_a_cargar = list(personaje_obj.debufos_permanentes_ids)
            for id_deb in ids_a_cargar:
                combo = agregar_combo_debufo(layout_perm, cat_permanentes, self.widgets_referencia["debufos_perm"], True)
                idx = combo.findData(id_deb, Qt.ItemDataRole.UserRole)
                if idx >= 0:
                    combo.setCurrentIndex(idx)
        else:
            agregar_combo_debufo(layout_perm, cat_permanentes, self.widgets_referencia["debufos_perm"], True)

        layout_col_est_principal.addWidget(col_temp)
        layout_col_est_principal.addWidget(col_perm)
        
        # --- COLUMNA 5: MEJORAS / CYBERWARE ESTÁTICO ---
        if es_npc and hasattr(personaje_obj, "mejoras") and personaje_obj.mejoras:
            contenedor_mejoras_final = QWidget()
            layout_mej_final_horizontal = QHBoxLayout(contenedor_mejoras_final)
            layout_mej_final_horizontal.setContentsMargins(15, 0, 0, 0)
            layout_mej_final_horizontal.setSpacing(15)

            todas_las_mejoras = personaje_obj.mejoras
            columnas_agrupadas = [todas_las_mejoras[i:i + 5] for i in range(0, len(todas_las_mejoras), 5)]

            for num_col, sublista in enumerate(columnas_agrupadas):
                col_widget_vertical = QWidget()
                layout_v_individual = QVBoxLayout(col_widget_vertical)
                layout_v_individual.setContentsMargins(0, 0, 0, 0)
                layout_v_individual.setSpacing(4)
                layout_v_individual.setAlignment(Qt.AlignmentFlag.AlignTop) 

                if num_col == 0:
                    lbl_mej_tit = QLabel("🦾MEJORAS🦾")
                    lbl_mej_tit.setObjectName("TituloColumnaMejoras")
                    layout_v_individual.addWidget(lbl_mej_tit)
                else:
                    layout_v_individual.addSpacing(15)

                for mejora in sublista:
                    nombre_buff = mejora["nombre"]
                    desc_buff = mejora["descripcion"]
                    
                    lbl_mejora = QLabel(f"• {nombre_buff}")
                    lbl_mejora.setObjectName("LblTextoMejora")
                    lbl_mejora.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
                    
                    texto_tooltip = f"""
                    <div style='background-color: #1E1E1E; color: #FFD700; padding: 5px; border: 1px solid #555555; font-family: Arial; font-size: 12px;'>
                        <b>{nombre_buff}</b><br>
                        <span style='color: #FFFFFF;'>{desc_buff}</span>
                    </div>
                    """
                    lbl_mejora.setToolTip(texto_tooltip)
                    lbl_mejora.setCursor(Qt.CursorShape.WhatsThisCursor)
                    layout_v_individual.addWidget(lbl_mejora)

                layout_v_individual.addStretch(1)
                layout_mej_final_horizontal.addWidget(col_widget_vertical)

            layout_mej_final_horizontal.addStretch(1)

        # --- ENSAMBLAJE FINAL DE COLUMNAS ---
        layout_stats_ampliado.addWidget(columna_izquierda)
        layout_stats_ampliado.addWidget(columna_derecha)
        layout_stats_ampliado.addWidget(columna_armas)
        layout_stats_ampliado.addWidget(columna_estados)
        
        if es_npc and hasattr(personaje_obj, "mejoras") and personaje_obj.mejoras:
            layout_stats_ampliado.addWidget(contenedor_mejoras_final)
            
        layout_stats_ampliado.addStretch(1)
        layout_principal.addLayout(layout_stats_ampliado)
        
        self.sincronizar_interfaz()

    # =======================================================
    # MÉTODOS ENVOLVENTES (Lógica Visual -> Controlador)
    # =======================================================

    # --- ui/ui_tarjetas.py (Modificar dentro de PersonajeWidget) ---

    # --- ui/ui_tarjetas.py (Dentro de PersonajeWidget) ---

    def sincronizar_interfaz(self):
        """Actualiza la UI: Solo la barra de vida cambia a rojo al estar herido."""
        p = self.personaje_obj
        w = self.widgets_referencia

        # 1. Actualización de valores numéricos
        if "hp" in w: w["hp"].setValue(p.hp)
        for attr in ["body_sp", "head_sp", "luck", "move"]:
            if attr in w: w[attr].setValue(getattr(p, attr))
        if "death_penalty" in w: w["death_penalty"].setText(str(p.death_penalty))
        if hasattr(p, "armas") and "armas" in w:
            for n_arma, datos in p.armas.items():
                if n_arma in w["armas"]: w["armas"][n_arma].setText(str(datos["actual"]))

        # =======================================================
        # LÓGICA DE COLOR SEPARADA (Identidad vs Estado)
        # =======================================================
        umbral_critico = p.max_hp * 0.5
        
        # Color de Identidad (El color del token o verde para PJs)
        if self.es_npc:
            color_identidad = getattr(p, 'color_token_hex', "#9400D3") 
        else:
            color_identidad = "#15A315" # Verde Jugador

        # Color de Estado (Solo para la barra de vida)
        color_barra = "#FF0000" if p.hp <= umbral_critico else color_identidad

        # 2. Aplicar color a la BARRA (Cambia según la vida)
        if "hp" in w:
            w["hp"].setStyleSheet(f"""
                QProgressBar::chunk {{ 
                    background-color: {color_barra}; 
                    border-radius: 5px; 
                }}
            """)

        # 3. Aplicar color al NOMBRE (Se queda siempre con el color del token)
        if "nombre" in w:
            w["nombre"].setStyleSheet(f"""
                color: {color_identidad}; 
                font-family: 'Orbitron', sans-serif; 
                font-size: 14px; 
                font-weight: bold;
                border: none;
            """)
    def _ui_procesar_ataque(self, cabeza, melee, directo):
        texto = self.input_dano.text() 
        if texto.isdigit():
            controlador.procesar_ataque(self.personaje_obj, int(texto), cabeza, melee, directo)
            self.sincronizar_interfaz()
            self.input_dano.clear()

    def _ui_procesar_curacion(self):
        texto = self.input_dano.text()
        if texto.isdigit():
            controlador.procesar_curacion(self.personaje_obj, int(texto))
            self.sincronizar_interfaz()
            self.input_dano.clear()

    def _ui_ajustar_stat(self, atributo, cantidad):
        controlador.ajustar_stat_secundario(self.personaje_obj, atributo, cantidad)
        self.sincronizar_interfaz()

    def _ui_ajustar_simple(self, atributo, cantidad):
        controlador.ajustar_atributo_simple(self.personaje_obj, atributo, cantidad)
        self.sincronizar_interfaz()

    def _ui_dano_fijo(self, cantidad):
        controlador.aplicar_dano_fijo(self.personaje_obj, cantidad)
        self.sincronizar_interfaz()

    def _ui_ajustar_municion(self, arma, cantidad):
        controlador.ajustar_municion_arma(self.personaje_obj, arma, cantidad)
        self.sincronizar_interfaz()

    def _ui_recargar_max(self, arma):
        controlador.recargar_arma_maxima(self.personaje_obj, arma)
        self.sincronizar_interfaz()

    def _ui_resetear(self):
        controlador.resetear_personaje_logico(self.personaje_obj)
        for tipo in ["debufos_temp", "debufos_perm"]:
            if tipo in self.widgets_referencia:
                lista = self.widgets_referencia[tipo]
                while len(lista) > 1:
                    c = lista.pop()
                    c.setParent(None)
                    c.deleteLater()
                if lista: lista[0].setCurrentIndex(0)
        self.sincronizar_interfaz()