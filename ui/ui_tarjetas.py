# --- ui/ui_tarjetas.py ---
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QFrame, QLabel, QPushButton, 
                             QComboBox, QLineEdit, QProgressBar, 
                             QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal
import controlador

class NoScrollComboBox(QComboBox):
    def wheelEvent(self, event):
        event.ignore()

def construir_tooltip(titulo, descripcion, remedio=None, tratamiento=None, font_size=11, tabla_dv=None):
    """Genera un recuadro HTML estandarizado para la información flotante."""
    # Contenedor principal
    html = f"<div style='background-color: #1A1A1A; color: #FFD700; padding: 8px; border: 1px solid #555555; font-family: Arial; font-size: {font_size}px;'>"
    html += f"<b style='font-size: 13px;'>{titulo}</b><br>"
    
    if descripcion:
        html += f"<span style='color: #FFFFFF;'>{descripcion}</span>"
    
    # Textos médicos (para estados)
    if remedio or tratamiento:
        html += "<br><br>"
    if remedio:
        html += f"<span style='color: #00FFFF;'><b>Remedio Rápido:</b> {remedio}</span><br>"
    if tratamiento:
        html += f"<span style='color: #00FF00;'><b>Tratamiento:</b> {tratamiento}</span>"
        
    # NUEVO DISEÑO VERTICAL: Tabla de Valores de Dificultad (VD)
    if tabla_dv and any(v is not None for v in tabla_dv):
        # Convertimos nulos a "-"
        v = [str(val) if val is not None else "-" for val in tabla_dv]
        encabezados = ["0-6", "7-12", "13-25", "26-50", "51-100", "101-200", "201-400", "401-800"]
        
        html += "<br><br><b style='color:#00FFFF; font-size: 11px; font-family: Orbitron, sans-serif;'>DIFICULTAD DE DISPARO:</b><br>"
        # Estilo principal de la tabla (Borde exterior cian)
        html += "<table style='width: 150px; text-align:center; border: 1px solid #00FFFF; border-collapse: collapse; margin-top:5px; font-size:11px;'>"
        
        # Cabeceras de las dos columnas
        html += "<tr style='background-color: #002222; color: #00FFFF;'>"
        html += "<th style='border: 1px solid #008888; padding: 4px;'>Distancia (m)</th>"
        html += "<th style='border: 1px solid #008888; padding: 4px;'>VD</th>"
        html += "</tr>"
        
        # Filas de datos emparejadas hacia abajo
        for dist, valor in zip(encabezados, v):
            color_texto = "#FF4444" if valor == "-" else "#FFFFFF"
            html += "<tr style='background-color: #111111;'>"
            html += f"<td style='border: 1px solid #008888; padding: 4px; color: #CCCCCC;'>{dist}</td>"
            html += f"<td style='border: 1px solid #008888; padding: 4px; color: {color_texto}; font-weight: bold;'>{valor}</td>"
            html += "</tr>"
        
        html += "</table>"
        
    html += "</div>"
    return html

# =============================================================================
# CLASE BASE: LA PLANTILLA COMPARTIDA (TEMPLATE METHOD PATTERN)
# =============================================================================
class TarjetaBase(QFrame):
    solicitar_eliminacion = pyqtSignal(object) 
    
    def __init__(self, personaje_obj, cat_temporales, cat_permanentes):
        super().__init__()
        self.personaje_obj = personaje_obj
        self.cat_temporales = cat_temporales
        self.cat_permanentes = cat_permanentes
        self.widgets_referencia = {}
        self.guarda_estados_db = False 
        
        self.setObjectName("ContenedorPersonaje")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        self._aplicar_estilos_base()
        
        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(8, 8, 8, 8)
        self.layout_principal.setSpacing(5)
        
        self._construir_cabecera()
        self._construir_fila_hp()
        self._construir_stats_ampliados()
        
        self.sincronizar_interfaz()

    def _aplicar_estilos_base(self): pass
    def _agregar_botones_cabecera(self, layout): pass
    def _agregar_botones_hp(self, layout): pass
    def _agregar_elementos_col_der(self, layout): self._construir_fila_fuego(layout)
    def _agregar_columnas_extra(self, layout): pass
    def _obtener_color_identidad(self): return "#FFFFFF"
    
    def _obtener_stats_col_izq(self):
        return [
            ("BODY SP", "body_sp", "max_body_sp"),
            ("HEAD SP", "head_sp", "max_head_sp"),
        ]

    def _construir_cabecera(self):
        fila_cabecera = QHBoxLayout()
        
        lbl_nombre = QLabel(self.personaje_obj.nombre.upper())
        lbl_nombre.setObjectName("NombrePJ") 
        self.widgets_referencia["nombre"] = lbl_nombre 
        
        btn_reset = QPushButton("🔄RESET🔄")
        btn_reset.setFixedWidth(65)
        btn_reset.setObjectName("BtnReset") 
        btn_reset.clicked.connect(lambda checked: self._ui_resetear())
        
        fila_cabecera.addWidget(lbl_nombre)
        fila_cabecera.addStretch(1)
        fila_cabecera.addWidget(btn_reset)
        
        self._agregar_botones_cabecera(fila_cabecera)
        self.layout_principal.addLayout(fila_cabecera)

    def _construir_fila_hp(self):
        fila_hp = QHBoxLayout()
        
        lbl_hp = QLabel("HP")
        lbl_hp.setFixedWidth(60)
        lbl_hp.setObjectName("LblStatTit") 
        
        barra_hp = QProgressBar()
        barra_hp.setRange(0, self.personaje_obj.max_hp)
        barra_hp.setValue(self.personaje_obj.hp)
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
            ("Cuerpo", False, False, False), ("Cabeza", True, False, False),
            ("M. Cuerpo", False, True, False), ("M. Cabeza", True, True, False),
            ("⚡ Directo", False, False, True)
        ]

        for texto, cabeza, melee, directo in ataques:
            btn = QPushButton(texto)
            btn.clicked.connect(lambda checked, c=cabeza, m=melee, d=directo: self._ui_procesar_ataque(c, m, d))
            fila_hp.addWidget(btn)

        self._agregar_botones_hp(fila_hp) 
        fila_hp.addStretch(1)
        self.layout_principal.addLayout(fila_hp)

    def _construir_stats_ampliados(self):
        layout_stats = QHBoxLayout()
        layout_stats.setContentsMargins(0, 0, 0, 0)
        layout_stats.setSpacing(25)
        
        col_izq = QWidget()
        l_izq = QVBoxLayout(col_izq)
        l_izq.setContentsMargins(0, 0, 0, 0)
        
        # Generar las filas de barras (SP, MOVE, LUCK)
        for nom_ui, attr, attr_max in self._obtener_stats_col_izq():
            fila = QHBoxLayout()
            lbl = QLabel(nom_ui)
            lbl.setFixedWidth(60)
            lbl.setObjectName("LblStatTit") 
            
            val_max = getattr(self.personaje_obj, attr_max)
            
            barra = QProgressBar()
            barra.setRange(0, val_max if val_max > 0 else 1)
            barra.setValue(getattr(self.personaje_obj, attr))
            barra.setFormat(f"%v / {val_max}") 
            
            barra.setFixedWidth(115)
            barra.setObjectName(f"Barra{attr.replace('_', '').upper()}") 
            self.widgets_referencia[attr] = barra
            
            b_menos = QPushButton("-")
            b_menos.setFixedWidth(24)
            b_menos.setObjectName("BtnAjuste") 
            b_menos.clicked.connect(lambda checked, a=attr, c=-1: self._ui_ajustar_stat(a, c))
            
            b_mas = QPushButton("+")
            b_mas.setFixedWidth(24)
            b_mas.setObjectName("BtnAjuste") 
            b_mas.clicked.connect(lambda checked, a=attr, c=1: self._ui_ajustar_stat(a, c))

            fila.addWidget(lbl)
            fila.addWidget(barra)
            fila.addWidget(b_menos)
            fila.addWidget(b_mas)
            fila.addStretch(1)
            l_izq.addLayout(fila)

        col_der = QWidget()
        l_der = QVBoxLayout(col_der)
        l_der.setContentsMargins(0, 0, 0, 0)
        self._agregar_elementos_col_der(l_der) 
        l_der.addStretch(1)

        col_armas = self._construir_columna_armas()
        col_estados = self._construir_columna_estados()

        layout_stats.addWidget(col_izq)
        layout_stats.addWidget(col_der)
        layout_stats.addWidget(col_armas)
        layout_stats.addWidget(col_estados)
        self._agregar_columnas_extra(layout_stats) 
        layout_stats.addStretch(1)
        
        self.layout_principal.addLayout(layout_stats)
        
    def _construir_fila_dr(self, layout):
        """Crea la fila para la reducción de daño endurecido."""
        fila = QHBoxLayout()
        lbl = QLabel("🛡️ RED. DAÑO") # Texto simplificado
        lbl.setFixedWidth(85) # <--- ANCHO UNIFICADO
        lbl.setObjectName("LblStatTit") 
        
        valor_actual = getattr(self.personaje_obj, "reduccion_danio", 0)
        input_dr = QLineEdit(str(valor_actual))
        input_dr.setFixedWidth(40)
        input_dr.setAlignment(Qt.AlignmentFlag.AlignCenter)
        input_dr.setStyleSheet("color: #FFA500; font-weight: bold; background-color: #000000; border: 1px solid #555;")
        
        def actualizar_modelo(texto):
            if texto.isdigit():
                self.personaje_obj.reduccion_danio = int(texto)
            elif texto == "":
                self.personaje_obj.reduccion_danio = 0
                
        input_dr.textChanged.connect(actualizar_modelo)
        self.widgets_referencia["reduccion_danio"] = input_dr 
        
        fila.addWidget(lbl)
        fila.addWidget(input_dr)
        fila.addStretch(1)
        layout.addLayout(fila)

    def _construir_fila_move(self, layout):
        """Crea una fila estática para mostrar la capacidad de movimiento total."""
        fila = QHBoxLayout()
        lbl = QLabel("👟 MOVE")
        lbl.setFixedWidth(85) # <--- ANCHO UNIFICADO
        lbl.setObjectName("LblStatTit") 
        
        # Leemos solo el máximo de movimiento
        valor_move = getattr(self.personaje_obj, "max_move", 0)
        lbl_val = QLabel(f"{valor_move} cas.")
        lbl_val.setStyleSheet("color: #00FFFF; font-weight: bold; font-family: 'Orbitron', sans-serif;")
        
        fila.addWidget(lbl)
        fila.addWidget(lbl_val)
        fila.addStretch(1)
        layout.addLayout(fila)

    def _agregar_elementos_col_der(self, layout): 
        """Añade los elementos comunes de la columna derecha."""
        self._construir_fila_move(layout)  # 1. Indicador estático de Movimiento
        self._construir_fila_dr(layout)    # 2. Reducción de Daño
        self._construir_fila_fuego(layout) # 3. Mecánicas de Fuego

    def _construir_fila_fuego(self, layout):
        fila = QHBoxLayout()
        lbl_fuego = QLabel("🔥 FIRE") # Texto simplificado
        lbl_fuego.setFixedWidth(85) # <--- ANCHO UNIFICADO
        lbl_fuego.setObjectName("LblFuegoTit") 

        b5 = QPushButton("🔥")
        b5.setFixedWidth(38)
        b5.setObjectName("BtnFuego") 
        b5.clicked.connect(lambda checked: self._ui_dano_fijo(5))

        b10 = QPushButton("🔥🔥🔥")
        b10.setFixedWidth(50)
        b10.setObjectName("BtnFuego") 
        b10.clicked.connect(lambda checked: self._ui_dano_fijo(10))

        fila.addWidget(lbl_fuego)
        fila.addWidget(b5)
        fila.addWidget(b10)
        fila.addStretch(1)
        layout.addLayout(fila)

    def _construir_columna_armas(self):
        w = QWidget()
        l = QVBoxLayout(w)
        l.setContentsMargins(15, 0, 0, 0)
        lbl_tit = QLabel("MUNICIÓN")
        lbl_tit.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_tit.setObjectName("TituloColumnaArmas") 
        l.addWidget(lbl_tit)
        
        self.widgets_referencia["armas"] = {}
        if hasattr(self.personaje_obj, "armas") and self.personaje_obj.armas:
            for n_arma, datos in self.personaje_obj.armas.items():
                fila = QHBoxLayout()
                lbl_n = QLabel(n_arma)
                lbl_n.setFixedWidth(70)
                lbl_n.setWordWrap(True)
                lbl_n.setObjectName("LblNombreArma") 

                # --- RESTAURACIÓN DE TOOLTIP DE ARMAS ---
                # Mostrar el tooltip si el arma tiene un efecto especial o si tiene tabla de VD (armas a distancia)
                if ("efecto" in datos and datos["efecto"]) or ("dv_valores" in datos and any(datos["dv_valores"])):
                    efecto_str = f"Efecto: {datos['efecto']}" if datos.get("efecto") else ""
                    
                    texto_tooltip = construir_tooltip(
                        n_arma, 
                        efecto_str, 
                        font_size=12, 
                        tabla_dv=datos.get("dv_valores")
                    )
                    lbl_n.setToolTip(texto_tooltip)
                    lbl_n.setCursor(Qt.CursorShape.WhatsThisCursor)
                # ----------------------------------------

                fila.addWidget(lbl_n)
                
                if datos["max"] > 0:
                    lbl_v = QLabel(str(datos["actual"]))
                    lbl_v.setFixedWidth(25)
                    lbl_v.setObjectName("LblValArma") 
                    self.widgets_referencia["armas"][n_arma] = lbl_v
                    
                    b_10 = QPushButton("-10")
                    b_10.setFixedWidth(26)
                    b_10.setObjectName("BtnAjuste") 
                    b_10.clicked.connect(lambda checked, n=n_arma: self._ui_ejecutar_disparo(n, 10))
                    
                    b_1 = QPushButton("-1")
                    b_1.setFixedWidth(26)
                    b_1.setObjectName("BtnAjuste") 
                    b_1.clicked.connect(lambda checked, n=n_arma: self._ui_ejecutar_disparo(n, 1))
                    
                    b_max = QPushButton("MAX")
                    b_max.setFixedWidth(32)
                    b_max.setObjectName("BtnAjuste") 
                    b_max.clicked.connect(lambda checked, n=n_arma: self._ui_recargar_max(n))
                    
                    fila.addWidget(lbl_v)
                    fila.addWidget(b_10)
                    fila.addWidget(b_1)
                    fila.addWidget(b_max)
                else:
                    # --- NUEVO DISEÑO PARA ARMAS MELEE ---
                    fila.addStretch(1)
                    lbl_melee = QLabel("Cuerpo a Cuerpo")
                    lbl_melee.setObjectName("LblTextoGris") 
                    
                    b_atacar = QPushButton("⚔️ ATACAR")
                    b_atacar.setObjectName("BtnAjuste")
                    # Reutilizamos la función de disparo, pero enviamos 1 (que luego ignoraremos)
                    b_atacar.clicked.connect(lambda checked, n=n_arma: self._ui_ejecutar_disparo(n, 1))
                    
                    fila.addWidget(lbl_melee)
                    fila.addWidget(b_atacar)
                l.addLayout(fila)
        else:
            lbl_sin = QLabel("Sin armas equipadas")
            lbl_sin.setObjectName("LblTextoGris") 
            l.addWidget(lbl_sin)
        l.addStretch(1)
        return w

    def _construir_columna_estados(self):
        w = QWidget()
        l = QHBoxLayout(w)
        l.setContentsMargins(15, 0, 0, 0)
        self.widgets_referencia["debufos_temp"] = []
        self.widgets_referencia["debufos_perm"] = []

        if not hasattr(self.personaje_obj, "debufos_permanentes_ids"):
            self.personaje_obj.debufos_permanentes_ids = []

        # Sub-columna Temporales
        c_temp, l_temp = QWidget(), QVBoxLayout()
        c_temp.setLayout(l_temp)
        h_temp = QHBoxLayout()
        lbl_tit_t = QLabel("⚠️ TEMPORALES")
        lbl_tit_t.setObjectName("LblTitTemp") 
        h_temp.addWidget(lbl_tit_t)
        
        b_add_t = QPushButton("+"); b_add_t.setFixedSize(20,20); b_add_t.setObjectName("BtnAddRemove") 
        b_add_t.clicked.connect(lambda checked: self._agregar_combo_debufo(l_temp, self.cat_temporales, self.widgets_referencia["debufos_temp"], False))
        b_rem_t = QPushButton("-"); b_rem_t.setFixedSize(20,20); b_rem_t.setObjectName("BtnAddRemove") 
        b_rem_t.clicked.connect(lambda checked: self._remover_combo(l_temp, self.widgets_referencia["debufos_temp"], False))
        h_temp.addWidget(b_add_t); h_temp.addWidget(b_rem_t); h_temp.addStretch(1)
        l_temp.addLayout(h_temp)
        
        self.widgets_referencia["btn_add_temp"] = b_add_t
        l_temp.addStretch(1) 
        self._agregar_combo_debufo(l_temp, self.cat_temporales, self.widgets_referencia["debufos_temp"], False)

        # Sub-columna Permanentes
        c_perm, l_perm = QWidget(), QVBoxLayout()
        c_perm.setLayout(l_perm)
        h_perm = QHBoxLayout()
        lbl_tit_p = QLabel("🏥 CRÍTICAS")
        lbl_tit_p.setObjectName("LblTitPerm") 
        h_perm.addWidget(lbl_tit_p)
        
        b_add_p = QPushButton("+"); b_add_p.setFixedSize(20,20); b_add_p.setObjectName("BtnAddRemove") 
        b_add_p.clicked.connect(lambda checked: self._agregar_combo_debufo(l_perm, self.cat_permanentes, self.widgets_referencia["debufos_perm"], True))
        b_rem_p = QPushButton("-"); b_rem_p.setFixedSize(20,20); b_rem_p.setObjectName("BtnAddRemove") 
        b_rem_p.clicked.connect(lambda checked: self._remover_combo(l_perm, self.widgets_referencia["debufos_perm"], True))
        h_perm.addWidget(b_add_p); h_perm.addWidget(b_rem_p); h_perm.addStretch(1)
        l_perm.addLayout(h_perm)
        self.widgets_referencia["btn_add_perm"] = b_add_p
        
        l_perm.addStretch(1) 
        if self.guarda_estados_db and self.personaje_obj.debufos_permanentes_ids:
            for id_deb in list(self.personaje_obj.debufos_permanentes_ids):
                combo = self._agregar_combo_debufo(l_perm, self.cat_permanentes, self.widgets_referencia["debufos_perm"], True)
                idx = combo.findData(id_deb, Qt.ItemDataRole.UserRole)
                if idx >= 0: combo.setCurrentIndex(idx)
        else:
            self._agregar_combo_debufo(l_perm, self.cat_permanentes, self.widgets_referencia["debufos_perm"], True)

        l.addWidget(c_temp)
        l.addWidget(c_perm)
        return w

    def _agregar_combo_debufo(self, layout_destino, catalogo, referencias, es_perm):
        combo = NoScrollComboBox()
        combo.setFixedWidth(160)
        for idx, item in enumerate(catalogo):
            combo.addItem(item["nombre"], userData=item.get("id_debufo"))
            
            # --- RESTAURACIÓN DE TOOLTIP DE ESTADOS ---
            if item.get("tipo") == "Permanente" and item["nombre"] != "---":
                tooltip = construir_tooltip(
                    item['nombre'], 
                    item['descripcion'], 
                    remedio=item.get('remedio_rapido', 'N/D'), 
                    tratamiento=item.get('tratamiento', 'N/D')
                )
            else:
                tooltip = construir_tooltip(item['nombre'], item.get('descripcion', ''))
                
            combo.setItemData(idx, tooltip, Qt.ItemDataRole.ToolTipRole)
            # ------------------------------------------

        layout_destino.insertWidget(layout_destino.count() - 1, combo)
        referencias.append(combo)
        combo.currentIndexChanged.connect(lambda idx, cb=combo: self._actualizar_tooltip_modelo(cb, es_perm))
        self._actualizar_tooltip_modelo(combo, es_perm)
        return combo

    def _remover_combo(self, layout_destino, referencias, es_perm):
        if len(referencias) > 1:
            combo = referencias.pop()
            layout_destino.removeWidget(combo)
            combo.deleteLater()
            if es_perm and self.guarda_estados_db:
                self._actualizar_tooltip_modelo(referencias[0], es_perm)

    def _actualizar_tooltip_modelo(self, combo, es_perm):
        idx = combo.currentIndex()
        if idx >= 0:
            tooltip = combo.itemData(idx, Qt.ItemDataRole.ToolTipRole)
            combo.setToolTip(tooltip if tooltip else "")

        if es_perm and self.guarda_estados_db:
            self.personaje_obj.debufos_permanentes_ids.clear()
            for c in self.widgets_referencia["debufos_perm"]:
                id_deb = c.currentData(Qt.ItemDataRole.UserRole)
                if id_deb: self.personaje_obj.debufos_permanentes_ids.append(id_deb)

    
    # ------------------------------------------------------------------
    # CONTROLADORES DE EVENTOS
    # ------------------------------------------------------------------
    def sincronizar_interfaz(self):
        p, w = self.personaje_obj, self.widgets_referencia
        if "hp" in w: w["hp"].setValue(p.hp)
        for attr in ["body_sp", "head_sp", "luck", "move"]:
            if attr in w: w[attr].setValue(getattr(p, attr))
        if "death_penalty" in w: w["death_penalty"].setText(str(p.death_penalty))
        if hasattr(p, "armas") and "armas" in w:
            for n, d in p.armas.items():
                if n in w["armas"]: w["armas"][n].setText(str(d["actual"]))

        color_id = self._obtener_color_identidad()
        color_barra = "#FF0000" if p.hp <= (p.max_hp * 0.5) else color_id

        if "hp" in w: w["hp"].setStyleSheet(f"QProgressBar::chunk {{ background-color: {color_barra}; border-radius: 5px; }}")
        if "nombre" in w: w["nombre"].setStyleSheet(f"color: {color_id}; font-family: 'Orbitron', sans-serif; font-size: 14px; font-weight: bold; border: none;")

    def _ui_procesar_ataque(self, c, m, d):
        txt = self.input_dano.text()
        if txt.isdigit():
            controlador.procesar_ataque(self.personaje_obj, int(txt), c, m, d)
            self.sincronizar_interfaz()
            self.input_dano.clear()

    def _ui_ajustar_stat(self, a, c): controlador.ajustar_stat_secundario(self.personaje_obj, a, c); self.sincronizar_interfaz()
    def _ui_ajustar_simple(self, a, c): controlador.ajustar_atributo_simple(self.personaje_obj, a, c); self.sincronizar_interfaz()
    def _ui_dano_fijo(self, c): controlador.aplicar_dano_fijo(self.personaje_obj, c); self.sincronizar_interfaz()
    def _ui_ajustar_municion(self, a, c): controlador.ajustar_municion_arma(self.personaje_obj, a, c); self.sincronizar_interfaz()
    def _ui_recargar_max(self, a): controlador.recargar_arma_maxima(self.personaje_obj, a); self.sincronizar_interfaz()
    
    # ==================================================================
    def _ui_ejecutar_disparo(self, nombre_arma, cantidad):
        """
        Resta munición y, si es un NPC, genera la tirada de ataque 
        incluyendo el modificador situacional del cuadro de texto.
        """
        import controlador # Importación local para evitar circulares
        
        # 1. Obtener datos del arma
        arma_datos = self.personaje_obj.armas.get(nombre_arma)
        if not arma_datos:
            return

        es_npc = getattr(self.personaje_obj, 'es_npc', False)
        es_melee = (arma_datos["max"] == 0) # Si su máximo es 0, es cuerpo a cuerpo

        # 2. Validar falta de munición (SOLO SI NO ES MELEE)
        if not es_melee and arma_datos["actual"] < cantidad:
            # Solo informamos en el panel si es un NPC
            if es_npc and hasattr(self, 'lbl_resultado'):
                self.lbl_resultado.setText(f"<b style='color: #FF0000;'>⚠️ {nombre_arma.upper()} SIN BALAS</b>")
            return

        # 3. Restar munición lógicamente (SOLO SI NO ES MELEE)
        if not es_melee:
            controlador.ajustar_municion_arma(self.personaje_obj, nombre_arma, -cantidad)
            self.sincronizar_interfaz()

        # 4. Si NO es NPC o no tiene panel de resultados, terminamos aquí
        if not es_npc or not hasattr(self, 'lbl_resultado'):
            return

        # 5. --- LÓGICA EXCLUSIVA DE NPCs (Cálculo de Dados) ---
        
        # Capturamos el modificador del cuadro de texto (MOD ATK)
        mod_situacional = 0
        if hasattr(self, 'input_mod_ataque'):
            try:
                texto_mod = self.input_mod_ataque.text().strip()
                mod_situacional = int(texto_mod) if texto_mod else 0
            except ValueError:
                mod_situacional = 0 # Protección contra letras o símbolos

        # Extraemos estadísticas de combate
        base_combate = getattr(self.personaje_obj, 'base_combate', 0)
        dados_dano = arma_datos.get('dados_dano', 0) 
        es_autofuego = (cantidad == 10)

        # Generamos la tirada llamando al controlador con el nuevo parámetro
        texto_html = controlador.generar_tirada_ataque(
            nombre_arma=nombre_arma,
            base=base_combate,
            dados_dano=dados_dano,
            es_autofuego=es_autofuego,
            mod_situacional=mod_situacional # Envia el valor del cuadrito amarillo
        )
        
        # Actualizamos el recuadro negro del NPC
        self.lbl_resultado.setText(texto_html)
    # ==================================================================
    
    
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


# =============================================================================
# CLASE JUGADOR: EXPANDE LA BASE CON CURACIÓN, SUERTE Y MUERTE
# =============================================================================
class TarjetaJugador(TarjetaBase):
    def __init__(self, p_obj, c_temp, c_perm):
        self.guarda_estados_db = True 
        super().__init__(p_obj, c_temp, c_perm)

    def _obtener_color_identidad(self):
        return "#15A315" 

    def _obtener_stats_col_izq(self):
        stats = super()._obtener_stats_col_izq()
        stats.append(("LUCK", "luck", "max_luck"))
        return stats

    def _agregar_botones_hp(self, layout):
        btn_curar = QPushButton("💚 Curar")
        btn_curar.setObjectName("BtnCurar") 
        btn_curar.clicked.connect(lambda checked: self._ui_procesar_curacion())
        layout.addWidget(btn_curar)

    def _agregar_elementos_col_der(self, layout):
        super()._agregar_elementos_col_der(layout)
        
        fila_death = QHBoxLayout()
        lbl_tit = QLabel("💀☠️💀")
        lbl_tit.setFixedWidth(85) # <--- ANCHO UNIFICADO
        lbl_tit.setObjectName("LblStatTit") 
        
        lbl_val = QLabel(str(self.personaje_obj.death_penalty))
        lbl_val.setFixedWidth(25)
        lbl_val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_val.setObjectName("ValorDeathPenalty") 
        self.widgets_referencia["death_penalty"] = lbl_val
        
        b_menos = QPushButton("-"); b_menos.setFixedWidth(24); b_menos.setObjectName("BtnAjuste") 
        b_menos.clicked.connect(lambda checked: self._ui_ajustar_simple("death_penalty", -1))
        b_mas = QPushButton("+"); b_mas.setFixedWidth(24); b_mas.setObjectName("BtnAjuste") 
        b_mas.clicked.connect(lambda checked: self._ui_ajustar_simple("death_penalty", 1))
        
        fila_death.addWidget(lbl_tit); fila_death.addWidget(lbl_val)
        fila_death.addWidget(b_menos); fila_death.addWidget(b_mas)
        fila_death.addStretch(1)
        layout.addLayout(fila_death)

    def _ui_procesar_curacion(self):
        txt = self.input_dano.text()
        if txt.isdigit():
            controlador.procesar_curacion(self.personaje_obj, int(txt))
            self.sincronizar_interfaz()
            self.input_dano.clear()
            
# =============================================================================
# CLASE NPC: EXPANDE LA BASE CON ELIMINACIÓN, JEFES Y MEJORAS
# =============================================================================
class TarjetaNPC(TarjetaBase):
    def __init__(self, p_obj, c_temp, c_perm):
        super().__init__(p_obj, c_temp, c_perm)

    def _obtener_color_identidad(self):
        return getattr(self.personaje_obj, 'color_token_hex', "#9400D3")

    def _aplicar_estilos_base(self):
        if getattr(self.personaje_obj, 'es_boss', False):
            self.setStyleSheet("QFrame#ContenedorPersonaje { border: 2px solid #FF0000; background-color: #0A0000; }")

    def _agregar_botones_cabecera(self, layout):
        btn_cerrar = QPushButton("❌")
        btn_cerrar.setFixedSize(22, 22)
        btn_cerrar.setStyleSheet("color: #8B0000; font-weight: bold; background: transparent; border: 1px solid #8B0000; font-size: 10px;")
        btn_cerrar.clicked.connect(lambda checked: self.solicitar_eliminacion.emit(self.personaje_obj))
        layout.addWidget(btn_cerrar)
        
    def _agregar_elementos_col_der(self, layout):
        # 1. Llamar a la clase base para que dibuje la fila de fuego, daño y move primero
        super()._agregar_elementos_col_der(layout)
        
        # 2. Fila de Modificador de Combate
        fila_mod = QHBoxLayout()
        
        lbl_mod = QLabel("🎯 MOD. ATK")
        lbl_mod.setFixedWidth(85) # <--- ANCHO UNIFICADO
        lbl_mod.setObjectName("LblStatTit") 
        
        # Este es el cuadro donde escribirás el -2, +1, etc.
        self.input_mod_ataque = QLineEdit()
        self.input_mod_ataque.setPlaceholderText("0")
        self.input_mod_ataque.setFixedWidth(45)
        self.input_mod_ataque.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.input_mod_ataque.setStyleSheet("""
            QLineEdit {
                background-color: #0d0d0d;
                color: #FFFF00; 
                border: 1px solid #555;
                border-radius: 3px;
                font-weight: bold;
                font-family: 'Consolas';
            }
        """)
        
        fila_mod.addWidget(lbl_mod)
        fila_mod.addWidget(self.input_mod_ataque)
        fila_mod.addStretch(1)
        layout.addLayout(fila_mod)
        

        # 3. Construir la nueva fila de Iniciativa debajo
        fila_ini = QHBoxLayout()
        
        lbl_ini = QLabel("⚡ INIT")
        lbl_ini.setFixedWidth(85) # <--- ANCHO UNIFICADO
        lbl_ini.setObjectName("LblStatTit") 
        
    
        btn_ini = QPushButton("TIRAR DADOS")
        btn_ini.setFixedWidth(92) 
        btn_ini.setStyleSheet("color: #00FFFF; font-weight: bold; background-color: #1A1A1A; border: 1px solid #00FFFF; border-radius: 3px;")
        btn_ini.clicked.connect(lambda checked: self._ui_ejecutar_iniciativa())
        
        fila_ini.addWidget(lbl_ini)
        fila_ini.addWidget(btn_ini)
        fila_ini.addStretch(1)
        
        layout.addLayout(fila_ini)

    def _ui_ejecutar_iniciativa(self):
        """Llama al controlador para generar la iniciativa y la muestra en el panel."""
        import controlador
        base_ini = getattr(self.personaje_obj, 'base_iniciativa', 0)
        
        if hasattr(self, 'lbl_resultado'):
            texto_html = controlador.generar_tirada_iniciativa(base_ini)
            self.lbl_resultado.setText(texto_html)

    def _agregar_columnas_extra(self, layout):
        # 1. Columna de Mejoras (si el NPC tiene)
        if hasattr(self.personaje_obj, "mejoras") and self.personaje_obj.mejoras:
            c_mej = QWidget(); l_mej = QVBoxLayout(c_mej)
            l_mej.setContentsMargins(15, 0, 0, 0)
            lbl_tit = QLabel("🦾MEJORAS🦾")
            lbl_tit.setObjectName("TituloColumnaMejoras") 
            l_mej.addWidget(lbl_tit)
            
            for m in self.personaje_obj.mejoras:
                lbl_m = QLabel(f"• {m['nombre']}")
                lbl_m.setObjectName("LblTextoMejora") 

                # --- TOOLTIP DE MEJORAS ---
                texto_tooltip = construir_tooltip(m['nombre'], m.get('descripcion', ''), font_size=12)
                lbl_m.setToolTip(texto_tooltip)
                lbl_m.setCursor(Qt.CursorShape.WhatsThisCursor)
                # --------------------------

                l_mej.addWidget(lbl_m)
            l_mej.addStretch(1)
            layout.addWidget(c_mej)

        # 2. PANEL DE RESULTADOS DE COMBATE (Exclusivo de NPCs)
        self.frame_resultado = QFrame()
        self.frame_resultado.setFixedSize(220, 90) # Tamaño original amplio
        self.frame_resultado.setStyleSheet("""
            QFrame { background-color: #0d0d0d; border: 1px solid #333333; border-radius: 4px; }
        """)
        
        layout_res = QVBoxLayout(self.frame_resultado)
        layout_res.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_resultado = QLabel("<span style='color: #555555;'>ESPERANDO ACCIÓN...</span>")
        self.lbl_resultado.setWordWrap(True)
        self.lbl_resultado.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_resultado.setStyleSheet("border: none; font-family: 'Consolas', monospace; font-size: 11px;")
        layout_res.addWidget(self.lbl_resultado)
        
        layout.addWidget(self.frame_resultado)

    

# =============================================================================
# EL PATRÓN FÁBRICA (FACTORY PATTERN) PARA COMPATIBILIDAD CON MAIN.PY
# =============================================================================
def PersonajeWidget(personaje_obj, cat_temporales, cat_permanentes, es_npc=False):
    if es_npc:
        return TarjetaNPC(personaje_obj, cat_temporales, cat_permanentes)
    else:
        return TarjetaJugador(personaje_obj, cat_temporales, cat_permanentes)