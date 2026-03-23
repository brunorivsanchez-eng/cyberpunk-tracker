from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, 
                             QLabel, QPushButton, QCheckBox, 
                             QLineEdit, QComboBox, QScrollArea, 
                             QWidget, QGridLayout, QFrame,
                             QTreeWidget, QTreeWidgetItem, QHeaderView,
                             QTreeWidgetItemIterator, QSpinBox, QListWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import controlador

class DialogoAoE(QDialog):
    def __init__(self, registro_personajes, parent=None):
        super().__init__(parent)
        self.setFixedWidth(420)
        self.registro_personajes = registro_personajes 

        self.setStyleSheet("background-color: #121212;")
        
        layout_principal = QVBoxLayout(self)
        
        # --- SECCIÓN 1: Configuración del Daño ---
        layout_config = QHBoxLayout()
        
        lbl_danio = QLabel("Daño:")
        lbl_danio.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        
        self.input_danio = QLineEdit()
        self.input_danio.setPlaceholderText("Ej. 15")
        self.input_danio.setFixedWidth(60)
        self.input_danio.setStyleSheet("background-color: #2C2C2C; color: white; border: 1px solid #444444; border-radius: 4px; padding: 2px;")
        
        lbl_tipo = QLabel("Modo AoE:")
        lbl_tipo.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Cuerpo (SP -1)", "Cuerpo (SP -2)", "Directo"])
        self.combo_tipo.setStyleSheet("background-color: #2C2C2C; color: white; border: 1px solid #444444; border-radius: 4px; padding: 2px;")
        
        layout_config.addWidget(lbl_danio)
        layout_config.addWidget(self.input_danio)
        layout_config.addSpacing(15)
        layout_config.addWidget(lbl_tipo)
        layout_config.addWidget(self.combo_tipo)
        layout_config.addStretch(1)
        
        layout_principal.addLayout(layout_config)
        
        # --- SECCIÓN 2: Selección de Objetivos ---
        lbl_objetivos = QLabel("Seleccionar Objetivos:")
        lbl_objetivos.setStyleSheet("color: #FF00FF; font-weight: bold; margin-top: 10px; background: transparent;")
        layout_principal.addWidget(lbl_objetivos)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        contenedor_scroll = QWidget()
        contenedor_scroll.setStyleSheet("background-color: #1E1E1E; border-radius: 6px;")
        self.layout_checks = QVBoxLayout(contenedor_scroll)
        
        self.checkboxes = []
        
        for personaje_obj, dicc_widgets in self.registro_personajes:
            chk = QCheckBox(f"{'[NPC]' if personaje_obj.es_npc else '[PJ]'} {personaje_obj.nombre}")
            chk.setStyleSheet("QCheckBox { color: white; font-weight: bold; background: transparent; padding: 4px; }")
            chk.setChecked(False)
            self.checkboxes.append((chk, personaje_obj, dicc_widgets))
            self.layout_checks.addWidget(chk)
            
        self.layout_checks.addStretch(1)
        scroll.setWidget(contenedor_scroll)
        layout_principal.addWidget(scroll)
        
        # --- SECCIÓN 3: Botones de Acción ---
        layout_botones = QHBoxLayout()
        
        btn_seleccionar_todos = QPushButton("Todos")
        btn_seleccionar_todos.setStyleSheet("background-color: #333333; color: #00FF00; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_seleccionar_todos.clicked.connect(self.seleccionar_todos)
        
        btn_aplicar = QPushButton("💥 APLICAR DAÑO 💥")
        btn_aplicar.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_aplicar.clicked.connect(self.aplicar_aoe)
        
        layout_botones.addWidget(btn_seleccionar_todos)
        layout_botones.addWidget(btn_aplicar)
        
        layout_principal.addLayout(layout_botones)

    def seleccionar_todos(self):
        estado = not all(chk.isChecked() for chk, _, _ in self.checkboxes)
        for chk, _, _ in self.checkboxes:
            chk.setChecked(estado)

    def aplicar_aoe(self):
        texto_danio = self.input_danio.text()
        if not texto_danio.isdigit(): return 
            
        danio = int(texto_danio)
        tipo = self.combo_tipo.currentText()
        
        objetivos_afectados = []
        for chk, personaje_obj, widget_npc in self.checkboxes:
            if chk.isChecked():
                objetivos_afectados.append((personaje_obj, widget_npc))
                
        if objetivos_afectados:
            # 1. Extraer solo los modelos para el controlador
            solo_modelos = [p for p, w in objetivos_afectados]
            controlador.procesar_ataque_aoe(solo_modelos, danio, tipo)
            
            # 2. Ordenar a cada WIDGET que se sincronice a sí mismo
            # Esto respetará el color del token y la vida crítica individualmente
            for p, widget_npc in objetivos_afectados:
                widget_npc.sincronizar_interfaz()
                
            self.accept()


class DialogoAoEEstados(QDialog):
    def __init__(self, registro_personajes, cat_temporales, cat_permanentes, parent=None):
        super().__init__(parent)
        self.setFixedWidth(450)
        self.setStyleSheet("background-color: #121212;")
        
        self.registro_personajes = registro_personajes
        self.cat_temporales = cat_temporales
        self.cat_permanentes = cat_permanentes
        
        layout_principal = QVBoxLayout(self)
        
        # --- SECCIÓN 1: Configuración del Estado ---
        layout_config = QHBoxLayout()
        
        lbl_tipo = QLabel("Tipo:")
        lbl_tipo.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Temporal", "Permanente"])
        self.combo_tipo.setStyleSheet("background-color: #2C2C2C; color: white; border: 1px solid #444444; border-radius: 4px; padding: 2px;")
        
        lbl_efecto = QLabel("Efecto:")
        lbl_efecto.setStyleSheet("color: white; font-weight: bold; background: transparent;")
        
        self.combo_efecto = QComboBox()
        self.combo_efecto.setFixedWidth(200)
        self.combo_efecto.setStyleSheet("background-color: #2C2C2C; color: white; border: 1px solid #444444; border-radius: 4px; padding: 2px;")
        
        layout_config.addWidget(lbl_tipo)
        layout_config.addWidget(self.combo_tipo)
        layout_config.addSpacing(15)
        layout_config.addWidget(lbl_efecto)
        layout_config.addWidget(self.combo_efecto)
        layout_config.addStretch(1)
        
        layout_principal.addLayout(layout_config)
        
        self.combo_tipo.currentTextChanged.connect(self.actualizar_lista_efectos)
        self.actualizar_lista_efectos(self.combo_tipo.currentText()) 
        
        # --- SECCIÓN 2: Selección de Objetivos ---
        lbl_objetivos = QLabel("Seleccionar Objetivos:")
        lbl_objetivos.setStyleSheet("color: #00FFFF; font-weight: bold; margin-top: 10px; background: transparent;")
        layout_principal.addWidget(lbl_objetivos)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        contenedor_scroll = QWidget()
        contenedor_scroll.setStyleSheet("background-color: #1E1E1E; border-radius: 6px;")
        self.layout_checks = QVBoxLayout(contenedor_scroll)
        
        self.checkboxes = []
        
        for personaje_obj, dicc_widgets in self.registro_personajes:
            chk = QCheckBox(f"{'[NPC]' if personaje_obj.es_npc else '[PJ]'} {personaje_obj.nombre}")
            chk.setStyleSheet("QCheckBox { color: white; font-weight: bold; background: transparent; padding: 4px; }")
            chk.setChecked(False)
            self.checkboxes.append((chk, personaje_obj, dicc_widgets))
            self.layout_checks.addWidget(chk)
            
        self.layout_checks.addStretch(1)
        scroll.setWidget(contenedor_scroll)
        layout_principal.addWidget(scroll)
        
        # --- SECCIÓN 3: Botones de Acción ---
        layout_botones = QHBoxLayout()
        
        btn_seleccionar_todos = QPushButton("Todos")
        btn_seleccionar_todos.setStyleSheet("background-color: #333333; color: #00FF00; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_seleccionar_todos.clicked.connect(self.seleccionar_todos)
        
        btn_aplicar = QPushButton("⚠️ APLICAR ESTADO ⚠️")
        btn_aplicar.setStyleSheet("background-color: #B8860B; color: black; font-weight: bold; padding: 6px; border-radius: 4px;")
        btn_aplicar.clicked.connect(self.aplicar_estado)
        
        layout_botones.addWidget(btn_seleccionar_todos)
        layout_botones.addWidget(btn_aplicar)
        
        layout_principal.addLayout(layout_botones)

    def actualizar_lista_efectos(self, tipo_seleccionado):
        self.combo_efecto.clear()
        catalogo = self.cat_permanentes if tipo_seleccionado == "Permanente" else self.cat_temporales
        
        for item in catalogo:
            if item["nombre"] != "---": 
                self.combo_efecto.addItem(item["nombre"], userData=item.get("id_debufo"))

    def seleccionar_todos(self):
        estado = not all(chk.isChecked() for chk, _, _ in self.checkboxes)
        for chk, _, _ in self.checkboxes:
            chk.setChecked(estado)

    def aplicar_estado(self):
        id_debufo = self.combo_efecto.currentData(Qt.ItemDataRole.UserRole)
        es_permanente = (self.combo_tipo.currentText() == "Permanente")
        
        if id_debufo is None: return 
            
        for chk, personaje_obj, widget_npc in self.checkboxes:
            if chk.isChecked():
                # Accedemos a las referencias a través del widget guardado
                w = widget_npc.widgets_referencia
                clave_btn = "btn_add_perm" if es_permanente else "btn_add_temp"
                clave_lista = "debufos_perm" if es_permanente else "debufos_temp"
                
                if clave_btn in w and clave_lista in w:
                    w[clave_btn].click()
                    combo_nuevo = w[clave_lista][-1]
                    idx = combo_nuevo.findData(id_debufo, Qt.ItemDataRole.UserRole)
                    if idx >= 0:
                        combo_nuevo.setCurrentIndex(idx)
                        
        self.accept()

class DialogoBestiario(QDialog):
    def __init__(self, datos_bestiario, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Constructor de Encuentros Tácticos")
        self.setFixedSize(850, 500) # Más ancho para soportar las 3 columnas
        self.setStyleSheet("background-color: #121212; color: white;")
        self.datos = datos_bestiario
        
        # Lista final que se enviará a main.py
        self.escuadra_preparada = [] 

        layout_principal = QHBoxLayout(self)

        # --- COLUMNA 1: CATÁLOGO Y BÚSQUEDA ---
        col1 = QVBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar amenaza...")
        self.input_busqueda.setStyleSheet("background-color: #1E1E1E; padding: 5px; border: 1px solid #333;")
        self.input_busqueda.textChanged.connect(self.filtrar_arbol)
        col1.addWidget(self.input_busqueda)

        self.arbol = QTreeWidget()
        self.arbol.setHeaderLabels(["Catálogo", "Facción"])
        self.arbol.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.arbol.setStyleSheet("QTreeWidget { background-color: #1A1A1A; border: 1px solid #333; }")
        self.arbol.itemSelectionChanged.connect(self.actualizar_vista_previa)
        col1.addWidget(self.arbol)
        layout_principal.addLayout(col1, 2)

        # --- COLUMNA 2: CONFIGURACIÓN Y VISTA PREVIA ---
        col2 = QVBoxLayout()
        col2.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        lbl_titulo_prev = QLabel("DATOS TÁCTICOS")
        lbl_titulo_prev.setStyleSheet("color: #FFD700; font-weight: bold;")
        col2.addWidget(lbl_titulo_prev)

        self.frame_prev = QFrame()
        self.frame_prev.setStyleSheet("background-color: #1E1E1E; border: 1px solid #444;")
        layout_prev = QVBoxLayout(self.frame_prev)
        self.lbl_prev_nombre = QLabel("Seleccione un objetivo...")
        self.lbl_prev_nombre.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF0000;")
        self.lbl_prev_stats = QLabel("\nHP: --\nSP Cabeza: --\nSP Cuerpo: --")
        layout_prev.addWidget(self.lbl_prev_nombre)
        layout_prev.addWidget(self.lbl_prev_stats)
        col2.addWidget(self.frame_prev)

        # Controles
        layout_opciones = QHBoxLayout()
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 10)
        self.spin_cantidad.setStyleSheet("background-color: #2C2C2C; padding: 4px;")
        layout_opciones.addWidget(QLabel("Cantidad:"))
        layout_opciones.addWidget(self.spin_cantidad)
        col2.addLayout(layout_opciones)

        self.chk_jefe = QCheckBox("Marcar como ☠️ Jefe")
        self.chk_jefe.setStyleSheet("color: #FF0000; font-weight: bold;")
        col2.addWidget(self.chk_jefe)
        
        col2.addStretch()

        self.btn_add_escuadra = QPushButton("➕ AÑADIR A ESCUADRA")
        self.btn_add_escuadra.setEnabled(False)
        self.btn_add_escuadra.setStyleSheet("background-color: #2E8B57; color: white; padding: 10px; font-weight: bold;")
        self.btn_add_escuadra.clicked.connect(self.agregar_a_escuadra)
        col2.addWidget(self.btn_add_escuadra)
        
        layout_principal.addLayout(col2, 1)

        # --- COLUMNA 3: ÁREA DE PREPARACIÓN (CARRITO) ---
        col3 = QVBoxLayout()
        col3.addWidget(QLabel("ESCUADRA LISTA PARA DESPLIEGUE"))
        
        self.lista_escuadra_ui = QListWidget()
        self.lista_escuadra_ui.setStyleSheet("background-color: #1A1A1A; border: 1px solid #555;")
        col3.addWidget(self.lista_escuadra_ui)

        self.btn_desplegar = QPushButton("⚡ DESPLEGAR ENCUENTRO ⚡")
        self.btn_desplegar.setEnabled(False)
        self.btn_desplegar.setStyleSheet("background-color: #440000; color: white; padding: 15px; font-weight: bold;")
        self.btn_desplegar.clicked.connect(self.accept)
        col3.addWidget(self.btn_desplegar)

        layout_principal.addLayout(col3, 1)

        self.poblar_arbol()

    def poblar_arbol(self):
        # Mismo código de antes
        self.arbol.clear()
        tiers = {}
        for npc in self.datos:
            t = f"Tier {npc['tier']}"
            if t not in tiers:
                tiers[t] = QTreeWidgetItem(self.arbol, [t])
            hijo = QTreeWidgetItem(tiers[t], [npc['nombre'], npc['faccion']])
            hijo.setData(0, Qt.ItemDataRole.UserRole, npc)
        self.arbol.expandAll()

    def filtrar_arbol(self, texto):
        # Mismo código de antes
        texto = texto.lower()
        iterador = QTreeWidgetItemIterator(self.arbol)
        while iterador.value():
            item = iterador.value()
            if item.childCount() == 0:
                coincide = texto in item.text(0).lower() or texto in item.text(1).lower()
                item.setHidden(not coincide)
                if coincide and item.parent(): item.parent().setHidden(False)
            iterador += 1

    def actualizar_vista_previa(self):
        items = self.arbol.selectedItems()
        if not items or items[0].childCount() > 0:
            self.btn_add_escuadra.setEnabled(False)
            return
        npc = items[0].data(0, Qt.ItemDataRole.UserRole)
        self.lbl_prev_nombre.setText(npc['nombre'].upper())
        self.lbl_prev_stats.setText(f"❤️ HP Máx: {npc['hp']}\n🛡️ SP Cabeza: {npc['head']}\n🛡️ SP Cuerp: {npc['body']}")
        self.btn_add_escuadra.setEnabled(True)

    def agregar_a_escuadra(self):
        items = self.arbol.selectedItems()
        if not items: return
        npc = items[0].data(0, Qt.ItemDataRole.UserRole)
        cant = self.spin_cantidad.value()
        es_jefe = self.chk_jefe.isChecked()

        # Guardar en memoria
        self.escuadra_preparada.append({
            "id": npc['id'], "nombre": npc['nombre'], 
            "cantidad": cant, "es_jefe": es_jefe
        })

        # Mostrar en UI
        etiqueta = f"{cant}x {npc['nombre']}" + (" [☠️ JEFE]" if es_jefe else "")
        self.lista_escuadra_ui.addItem(etiqueta)
        self.btn_desplegar.setEnabled(True)
        
        # Resetear controles
        self.spin_cantidad.setValue(1)
        self.chk_jefe.setChecked(False)