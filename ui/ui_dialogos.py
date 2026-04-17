# --- ui/ui_dialogos.py ---
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QCheckBox, QLineEdit, QComboBox, 
                             QScrollArea, QWidget, QFrame, QTreeWidget, 
                             QTreeWidgetItem, QHeaderView, QTreeWidgetItemIterator, 
                             QSpinBox, QListWidget, QTabWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
import controlador

# ==============================================================================
# CLASE BASE: GESTIÓN DE SELECCIÓN DE OBJETIVOS
# ==============================================================================
class DialogoBaseSeleccion(QDialog):
    """Clase base para cualquier diálogo que requiera seleccionar múltiples personajes."""
    def __init__(self, registro_personajes, parent=None):
        super().__init__(parent)
        self.registro_personajes = registro_personajes
        self.checkboxes = []
        self.setStyleSheet("background-color: #121212; color: white;")
        
    def crear_lista_seleccion(self, color_titulo="#FF00FF"):
        """Genera el área de scroll con los checkboxes de los personajes."""
        layout = QVBoxLayout()
        
        lbl = QLabel("Seleccionar Objetivos:")
        lbl.setStyleSheet(f"color: {color_titulo}; font-weight: bold; margin-top: 10px; background: transparent;")
        layout.addWidget(lbl)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: 1px solid #333; background-color: transparent; }")
        
        contenedor = QWidget()
        contenedor.setStyleSheet("background-color: #1E1E1E;")
        self.layout_checks = QVBoxLayout(contenedor)
        
        for p_obj, w_ref in self.registro_personajes:
            chk = QCheckBox(f"{'[NPC]' if p_obj.es_npc else '[PJ]'} {p_obj.nombre}")
            chk.setStyleSheet("QCheckBox { color: white; padding: 4px; }")
            self.checkboxes.append((chk, p_obj, w_ref))
            self.layout_checks.addWidget(chk)
            
        self.layout_checks.addStretch(1)
        scroll.setWidget(contenedor)
        layout.addWidget(scroll)
        return layout

    def obtener_seleccionados(self):
        return [(p, w) for chk, p, w in self.checkboxes if chk.isChecked()]

    def seleccionar_todos(self):
        estado = not all(chk.isChecked() for chk, _, _ in self.checkboxes)
        for chk, _, _ in self.checkboxes:
            chk.setChecked(estado)

# ==============================================================================
# EL UNIFICADOR: DIÁLOGO DE ACCIÓN GLOBAL (DAÑO + ESTADOS)
# ==============================================================================
class DialogoAccionGlobal(DialogoBaseSeleccion):
    def __init__(self, registro_personajes, cat_temp, cat_perm, parent=None):
        super().__init__(registro_personajes, parent)
        self.setWindowTitle("Consola de Acción Global")
        self.setFixedWidth(500)
        self.cat_temp = cat_temp
        self.cat_perm = cat_perm

        layout_principal = QVBoxLayout(self)

        # 1. Selector de Objetivos (Parte superior)
        layout_principal.addLayout(self.crear_lista_seleccion("#00FFFF"))

        # 2. Pestañas de Acción
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #444; }
            QTabBar::tab { background: #222; color: #888; padding: 8px; }
            QTabBar::tab:selected { background: #444; color: white; font-weight: bold; }
        """)
        
        self.tab_danio = self._crear_tab_danio()
        self.tab_estados = self._crear_tab_estados()
        
        self.tabs.addTab(self.tab_danio, "💥 DAÑO 💥")
        self.tabs.addTab(self.tab_estados, "☣️ ESTADOS ☣️")
        layout_principal.addWidget(self.tabs)

        # 3. Botones Globales
        btns = QHBoxLayout()
        btn_all = QPushButton("ALL")
        btn_all.clicked.connect(self.seleccionar_todos)
        btn_cerrar = QPushButton("Cerrar")
        btn_cerrar.clicked.connect(self.reject)
        
        btns.addWidget(btn_all)
        btns.addWidget(btn_cerrar)
        layout_principal.addLayout(btns)

    def _crear_tab_danio(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        form = QHBoxLayout()
        self.input_danio = QLineEdit()
        self.input_danio.setPlaceholderText("Pts")
        self.input_danio.setFixedWidth(50)
        self.combo_tipo = QComboBox()
        self.combo_tipo.addItems(["Cuerpo (SP -1)", "Cuerpo (SP -2)", "Directo"])
        
        form.addWidget(QLabel("Daño:"))
        form.addWidget(self.input_danio)
        form.addWidget(QLabel("Tipo:"))
        form.addWidget(self.combo_tipo)
        layout.addLayout(form)
        
        btn = QPushButton("APLICAR DAÑO A SELECCIONADOS")
        btn.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self.ejecutar_danio)
        layout.addWidget(btn)
        return tab

    def _crear_tab_estados(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        self.combo_st_tipo = QComboBox()
        self.combo_st_tipo.addItems(["Temporal", "Permanente"])
        self.combo_st_tipo.currentTextChanged.connect(self._actualizar_efectos)
        
        self.combo_st_efecto = QComboBox()
        self._actualizar_efectos("Temporal")

        layout.addWidget(QLabel("Tipo de Estado:"))
        layout.addWidget(self.combo_st_tipo)
        layout.addWidget(QLabel("Efecto:"))
        layout.addWidget(self.combo_st_efecto)
        
        btn = QPushButton("APLICAR ESTADO A SELECCIONADOS")
        btn.setStyleSheet("background-color: #B8860B; color: black; font-weight: bold; padding: 8px;")
        btn.clicked.connect(self.ejecutar_estado)
        layout.addWidget(btn)
        return tab

    def _actualizar_efectos(self, tipo):
        self.combo_st_efecto.clear()
        cat = self.cat_perm if tipo == "Permanente" else self.cat_temp
        for item in cat:
            if item["nombre"] != "---":
                self.combo_st_efecto.addItem(item["nombre"], userData=item.get("id_debufo"))

    def ejecutar_danio(self):
        txt = self.input_danio.text()
        if not txt.isdigit(): return
        
        objetivos = self.obtener_seleccionados()
        if not objetivos: return
        
        controlador.procesar_ataque_aoe([p for p, w in objetivos], int(txt), self.combo_tipo.currentText())
        for p, w in objetivos: w.sincronizar_interfaz()
        self.accept()

    def ejecutar_estado(self):
        id_debufo = self.combo_st_efecto.currentData()
        es_perm = (self.combo_st_tipo.currentText() == "Permanente")
        objetivos = self.obtener_seleccionados()
        
        for p, w in objetivos:
            refs = w.widgets_referencia
            clave_btn = "btn_add_perm" if es_perm else "btn_add_temp"
            clave_lista = "debufos_perm" if es_perm else "debufos_temp"
            
            if clave_btn in refs:
                refs[clave_btn].click()
                combo = refs[clave_lista][-1]
                idx = combo.findData(id_debufo)
                if idx >= 0: combo.setCurrentIndex(idx)
        self.accept()

# ==============================================================================
# CONSTRUCTOR DE ENCUENTROS (BESTIARIO MODULAR)
# ==============================================================================
class DialogoBestiario(QDialog):
    def __init__(self, lista_chasis, lista_facciones, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Constructor de Encuentros Modulares")
        # Hacemos la ventana más grande para que quepa la información cómodamente
        self.setFixedSize(1000, 550) 
        self.setStyleSheet("background-color: #121212; color: white;")
        
        self.lista_chasis = lista_chasis
        self.lista_facciones = lista_facciones
        self.escuadra_preparada = [] 

        layout_principal = QHBoxLayout(self)

        # --- COLUMNA 1: CATÁLOGO DE CHASIS ---
        col1 = QVBoxLayout()
        self.input_busqueda = QLineEdit()
        self.input_busqueda.setPlaceholderText("🔍 Buscar chasis base...")
        self.input_busqueda.setStyleSheet("background-color: #1E1E1E; padding: 5px; border: 1px solid #333;")
        self.input_busqueda.textChanged.connect(self.filtrar_arbol)
        col1.addWidget(self.input_busqueda)

        self.arbol = QTreeWidget()
        self.arbol.setHeaderLabels(["Chasis Base"])
        self.arbol.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.arbol.setStyleSheet("QTreeWidget { background-color: #1A1A1A; border: 1px solid #333; }")
        self.arbol.itemSelectionChanged.connect(self.actualizar_vista_previa)
        col1.addWidget(self.arbol)
        layout_principal.addLayout(col1, 2)

        # --- COLUMNA 2: CONFIGURACIÓN Y SUPER VISTA PREVIA ---
        col2 = QVBoxLayout()
        col2.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # 1. Selector de Facción
        col2.addWidget(QLabel("Facción / Loadout:"))
        self.combo_faccion = QComboBox()
        self.combo_faccion.setStyleSheet("""
            QComboBox { background-color: #2C2C2C; border: 1px solid #555; padding: 5px; font-weight: bold;}
            QComboBox::drop-down { border-left: 1px solid #555; }
        """)
        for faccion in self.lista_facciones:
            self.combo_faccion.addItem(faccion['nombre'], userData=faccion['id_faccion'])
        self.combo_faccion.currentIndexChanged.connect(self.actualizar_vista_previa)
        col2.addWidget(self.combo_faccion)

        # 2. Vista Previa Estilizada (Panel de Escaneo)
        self.frame_prev = QFrame()
        self.frame_prev.setStyleSheet("background-color: #0A0A0A; border: 1px solid #00FFFF; border-radius: 5px; margin-top: 10px;")
        layout_prev = QVBoxLayout(self.frame_prev)
        
        self.lbl_prev_nombre = QLabel("--- ESCANER KIROSHI OFFLINE ---")
        self.lbl_prev_nombre.setWordWrap(True)
        self.lbl_prev_nombre.setStyleSheet("font-size: 14px; font-weight: bold; color: #00FFFF; border: none;")
        
        self.lbl_prev_stats = QLabel("\n\n")
        self.lbl_prev_stats.setStyleSheet("font-family: 'Consolas'; color: #CCCCCC; border: none; font-size: 12px;")
        
        self.lbl_prev_equipo = QLabel("")
        self.lbl_prev_equipo.setWordWrap(True)
        self.lbl_prev_equipo.setStyleSheet("color: #FFA500; font-size: 11px; border: none; margin-top: 5px;")
        
        layout_prev.addWidget(self.lbl_prev_nombre)
        layout_prev.addWidget(self.lbl_prev_stats)
        layout_prev.addWidget(self.lbl_prev_equipo)
        col2.addWidget(self.frame_prev)

        # 3. Controles de Despliegue
        fila_controles = QHBoxLayout()
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 10)
        self.spin_cantidad.setStyleSheet("""
            QSpinBox { background-color: #2C2C2C; color: white; border: 1px solid #555; padding: 4px; font-weight: bold; font-size: 14px; }
            QSpinBox::up-button, QSpinBox::down-button { background-color: #444; width: 20px; border-left: 1px solid #222; }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover { background-color: #FF0000; }
        """)
        
        self.chk_jefe = QCheckBox("☠️ Jefe")
        self.chk_jefe.setStyleSheet("""
            QCheckBox { color: #FF0000; font-weight: bold; font-size: 12px; margin-left: 10px;}
            QCheckBox::indicator { width: 15px; height: 15px; border: 1px solid #888; background: #2C2C2C; border-radius: 3px; }
            QCheckBox::indicator:checked { background: #FF0000; border: 1px solid #FFF; }
        """)
        
        fila_controles.addWidget(QLabel("Cant:"))
        fila_controles.addWidget(self.spin_cantidad)
        fila_controles.addWidget(self.chk_jefe)
        fila_controles.addStretch()
        col2.addLayout(fila_controles)

        # 4. Botón Agregar
        self.btn_add = QPushButton("➕ AÑADIR A ESCUADRA")
        self.btn_add.setEnabled(False)
        self.btn_add.setStyleSheet("""
            QPushButton { background-color: #2E8B57; color: white; padding: 10px; font-weight: bold; margin-top: 10px;}
            QPushButton:hover { background-color: #3CB371; }
            QPushButton:disabled { background-color: #1A4D30; color: #555; }
        """)
        self.btn_add.clicked.connect(self.agregar_a_escuadra)
        col2.addWidget(self.btn_add)
        layout_principal.addLayout(col2, 2) # Damos más espacio a la columna central

        # --- COLUMNA 3: CARRITO ---
        col3 = QVBoxLayout()
        self.lista_ui = QListWidget()
        self.lista_ui.setStyleSheet("background-color: #1A1A1A; border: 1px solid #555; font-size: 12px;")
        self.lista_ui.itemSelectionChanged.connect(self.verificar_seleccion_carrito)
        
        col3.addWidget(QLabel("ESCUADRA LISTA:"))
        col3.addWidget(self.lista_ui)

        self.btn_eliminar_carrito = QPushButton("🗑️ Eliminar Seleccionado")
        self.btn_eliminar_carrito.setEnabled(False)
        self.btn_eliminar_carrito.setStyleSheet("""
            QPushButton { background-color: #551111; color: white; padding: 5px; font-weight: bold; border: 1px solid #880000; }
            QPushButton:hover { background-color: #880000; }
            QPushButton:disabled { background-color: #220000; color: #555; border: none; }
        """)
        self.btn_eliminar_carrito.clicked.connect(self.eliminar_de_escuadra)
        col3.addWidget(self.btn_eliminar_carrito)

        self.btn_desplegar = QPushButton("⚡ DESPLEGAR ⚡")
        self.btn_desplegar.setEnabled(False)
        self.btn_desplegar.setStyleSheet("""
            QPushButton { background-color: #8B0000; color: white; padding: 15px; font-weight: bold; }
            QPushButton:hover { background-color: #FF0000; }
            QPushButton:disabled { background-color: #330000; color: #555; }
        """)
        self.btn_desplegar.clicked.connect(self.accept)
        col3.addWidget(self.btn_desplegar)
        layout_principal.addLayout(col3, 1)

        self._poblar_arbol()

    def _poblar_arbol(self):
        self.arbol.clear()
        tiers = {}
        for chasis in self.lista_chasis:
            t = f"Rango/Tier {chasis['tier']}"
            if t not in tiers: 
                tiers[t] = QTreeWidgetItem(self.arbol, [t])
                # Colorear los Tiers para que sea más fácil leerlos
                if chasis['tier'] == 3: tiers[t].setForeground(0, QColor("#FF4444"))
                elif chasis['tier'] == 2: tiers[t].setForeground(0, QColor("#FFA500"))
            
            h = QTreeWidgetItem(tiers[t], [chasis['nombre']])
            h.setData(0, Qt.ItemDataRole.UserRole, chasis)
        self.arbol.expandAll()

    def filtrar_arbol(self, texto):
        texto = texto.lower()
        it = QTreeWidgetItemIterator(self.arbol)
        while it.value():
            item = it.value()
            if item.childCount() == 0:
                coincide = texto in item.text(0).lower()
                item.setHidden(not coincide)
                if coincide and item.parent(): item.parent().setHidden(False)
            it += 1

    def actualizar_vista_previa(self):
        """Muestra el escáner completo: Stats del Chasis + Equipo de la Facción."""
        items = self.arbol.selectedItems()
        if not items or items[0].childCount() > 0:
            self.btn_add.setEnabled(False)
            self.lbl_prev_nombre.setText("--- ESCANER KIROSHI OFFLINE ---")
            self.lbl_prev_stats.setText("\n\n")
            self.lbl_prev_equipo.setText("")
            return
            
        chasis = items[0].data(0, Qt.ItemDataRole.UserRole)
        id_faccion = self.combo_faccion.currentData()
        nombre_faccion = self.combo_faccion.currentText()
        
        # 1. Mostrar Stats Físicos (Del Chasis)
        self.lbl_prev_nombre.setText(f"🎯 {nombre_faccion} ({chasis['nombre']})".upper())
        
        stats_texto = (
            f"❤️ HP Máxima: {chasis['max_hp']} \n"
            f"🛡️ SP Corporal: {chasis['max_body_sp']} | 🛡️ SP Cabeza: {chasis['max_head_sp']}\n"
            f"⚔️ Base Ataque: {chasis['base_combate']} | ⚡ Iniciativa: {chasis['base_iniciativa']}\n"
            f"👟 Movimiento: {chasis['max_move']} casillas"
        )
        self.lbl_prev_stats.setText(stats_texto)

        # 2. Consultar el Equipo en tiempo real (De la Facción)
        import database # Lo importamos aquí localmente para la consulta rápida
        armas, cromo = database.obtener_preview_equipo(id_faccion, chasis['tier'])
        
        txt_armas = "🔫 ARMAS: " + (", ".join(armas) if armas else "Desarmado")
        txt_cromo = "🦾 CROMO: " + (", ".join(cromo) if cromo else "Puro Carne")
        
        self.lbl_prev_equipo.setText(f"{txt_armas}\n\n{txt_cromo}")
        
        self.btn_add.setEnabled(True)

    def agregar_a_escuadra(self):
        items = self.arbol.selectedItems()
        if not items: return
        
        chasis = items[0].data(0, Qt.ItemDataRole.UserRole)
        id_faccion = self.combo_faccion.currentData()
        nombre_faccion = self.combo_faccion.currentText()
        
        cant = self.spin_cantidad.value()
        jefe = self.chk_jefe.isChecked()
        
        nombre_compuesto = f"{nombre_faccion} ({chasis['nombre']})"
        
        self.escuadra_preparada.append({
            "id_chasis": chasis['id_base'], 
            "id_faccion": id_faccion,
            "cantidad": cant, 
            "es_jefe": jefe
        })
        
        self.lista_ui.addItem(f"{cant}x {nombre_compuesto}" + (" [☠️]" if jefe else ""))
        if len(self.escuadra_preparada) > 0: self.btn_desplegar.setEnabled(True)

    def verificar_seleccion_carrito(self):
        self.btn_eliminar_carrito.setEnabled(bool(self.lista_ui.selectedItems()))

    def eliminar_de_escuadra(self):
        items = self.lista_ui.selectedItems()
        if not items: return
        fila = self.lista_ui.row(items[0])
        del self.escuadra_preparada[fila]
        self.lista_ui.takeItem(fila)
        if len(self.escuadra_preparada) == 0: self.btn_desplegar.setEnabled(False)