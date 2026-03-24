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
# CONSTRUCTOR DE ENCUENTROS (BESTIARIO)
# ==============================================================================
# ==============================================================================
# CONSTRUCTOR DE ENCUENTROS (BESTIARIO)
# ==============================================================================
class DialogoBestiario(QDialog):
    def __init__(self, datos_bestiario, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Constructor de Encuentros Tácticos")
        self.setFixedSize(850, 500)
        self.setStyleSheet("background-color: #121212; color: white;")
        self.datos = datos_bestiario
        self.escuadra_preparada = [] 

        layout_principal = QHBoxLayout(self)

        # --- COLUMNA 1: CATÁLOGO ---
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

        # --- COLUMNA 2: CONFIGURACIÓN ---
        col2 = QVBoxLayout()
        col2.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        self.frame_prev = QFrame()
        self.frame_prev.setStyleSheet("background-color: #1E1E1E; border: 1px solid #444;")
        layout_prev = QVBoxLayout(self.frame_prev)
        self.lbl_prev_nombre = QLabel("Seleccione objetivo...")
        self.lbl_prev_nombre.setStyleSheet("font-size: 14px; font-weight: bold; color: #FF0000;")
        self.lbl_prev_stats = QLabel("\nHP: --\nSP: --")
        layout_prev.addWidget(self.lbl_prev_nombre)
        layout_prev.addWidget(self.lbl_prev_stats)
        col2.addWidget(self.frame_prev)

        # --- CORRECCIÓN 3: Estilo del QSpinBox (Flechas de Cantidad) ---
        self.spin_cantidad = QSpinBox()
        self.spin_cantidad.setRange(1, 10)
        self.spin_cantidad.setStyleSheet("""
            QSpinBox {
                background-color: #2C2C2C;
                color: white;
                border: 1px solid #555;
                padding: 4px;
                font-weight: bold;
                font-size: 14px;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #444;
                width: 20px;
                border-left: 1px solid #222;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #FF0000;
            }
        """)
        
        # --- CORRECCIÓN 2: Estilo del Checkbox (Hacer visible la cajita) ---
        self.chk_jefe = QCheckBox("Marcar como ☠️ Jefe")
        self.chk_jefe.setStyleSheet("""
            QCheckBox {
                color: #FF0000; 
                font-weight: bold;
                font-size: 12px;
            }
            QCheckBox::indicator {
                width: 15px;
                height: 15px;
                border: 1px solid #888;
                background: #2C2C2C;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background: #FF0000;
                border: 1px solid #FFF;
            }
        """)
        
        col2.addWidget(QLabel("Cantidad:"))
        col2.addWidget(self.spin_cantidad)
        col2.addWidget(self.chk_jefe)
        col2.addStretch()

        self.btn_add = QPushButton("➕ AÑADIR A ESCUADRA")
        self.btn_add.setEnabled(False)
        self.btn_add.setStyleSheet("""
            QPushButton { background-color: #2E8B57; color: white; padding: 10px; font-weight: bold; }
            QPushButton:hover { background-color: #3CB371; }
            QPushButton:disabled { background-color: #1A4D30; color: #555; }
        """)
        self.btn_add.clicked.connect(self.agregar_a_escuadra)
        col2.addWidget(self.btn_add)
        layout_principal.addLayout(col2, 1)

        # --- COLUMNA 3: CARRITO ---
        col3 = QVBoxLayout()
        self.lista_ui = QListWidget()
        self.lista_ui.setStyleSheet("background-color: #1A1A1A; border: 1px solid #555; font-size: 12px;")
        
        # Conectar la selección de la lista para activar el botón de eliminar
        self.lista_ui.itemSelectionChanged.connect(self.verificar_seleccion_carrito)
        
        col3.addWidget(QLabel("ESCUADRA LISTA:"))
        col3.addWidget(self.lista_ui)

        # --- CORRECCIÓN 1: Botón para eliminar del carrito ---
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
        for npc in self.datos:
            t = f"Tier {npc['tier']}"
            if t not in tiers: tiers[t] = QTreeWidgetItem(self.arbol, [t])
            h = QTreeWidgetItem(tiers[t], [npc['nombre'], npc['faccion']])
            h.setData(0, Qt.ItemDataRole.UserRole, npc)
        self.arbol.expandAll()

    def filtrar_arbol(self, texto):
        texto = texto.lower()
        it = QTreeWidgetItemIterator(self.arbol)
        while it.value():
            item = it.value()
            if item.childCount() == 0:
                coincide = texto in item.text(0).lower() or texto in item.text(1).lower()
                item.setHidden(not coincide)
                if coincide and item.parent(): item.parent().setHidden(False)
            it += 1

    def actualizar_vista_previa(self):
        items = self.arbol.selectedItems()
        if not items or items[0].childCount() > 0:
            self.btn_add.setEnabled(False)
            return
        npc = items[0].data(0, Qt.ItemDataRole.UserRole)
        self.lbl_prev_nombre.setText(npc['nombre'].upper())
        self.lbl_prev_stats.setText(f"❤️ HP: {npc['hp']}\n🛡️ SP C: {npc['body']}\n🛡️ SP H: {npc['head']}")
        self.btn_add.setEnabled(True)

    def agregar_a_escuadra(self):
        items = self.arbol.selectedItems()
        if not items: return
        npc = items[0].data(0, Qt.ItemDataRole.UserRole)
        cant, jefe = self.spin_cantidad.value(), self.chk_jefe.isChecked()
        
        # Guardamos la data en la memoria de la clase
        self.escuadra_preparada.append({"id": npc['id'], "nombre": npc['nombre'], "cantidad": cant, "es_jefe": jefe})
        
        # Actualizamos la UI visualmente
        self.lista_ui.addItem(f"{cant}x {npc['nombre']}" + (" [☠️]" if jefe else ""))
        
        # Habilitamos el botón de despliegue si hay al menos 1 elemento
        if len(self.escuadra_preparada) > 0:
            self.btn_desplegar.setEnabled(True)

    def verificar_seleccion_carrito(self):
        """Activa o desactiva el botón de eliminar según si hay un elemento seleccionado en el carrito."""
        if self.lista_ui.selectedItems():
            self.btn_eliminar_carrito.setEnabled(True)
        else:
            self.btn_eliminar_carrito.setEnabled(False)

    def eliminar_de_escuadra(self):
        """Elimina el elemento seleccionado tanto de la UI como de la memoria del programa."""
        items_seleccionados = self.lista_ui.selectedItems()
        if not items_seleccionados: return
        
        item = items_seleccionados[0]
        fila = self.lista_ui.row(item)
        
        # Eliminamos de la memoria interna
        del self.escuadra_preparada[fila]
        
        # Eliminamos de la interfaz visual
        self.lista_ui.takeItem(fila)
        
        # Si el carrito se quedó vacío, bloqueamos el botón de desplegar
        if len(self.escuadra_preparada) == 0:
            self.btn_desplegar.setEnabled(False)