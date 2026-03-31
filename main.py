import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QScrollArea, QFrame, QDialog)
from PyQt6.QtCore import Qt

# Importaciones de UI actualizadas
from ui.ui_tarjetas import PersonajeWidget
from ui.ui_paneles import PanelJugadoresHeader, PanelNPCsHeader
from ui.ui_dialogos import DialogoAccionGlobal, DialogoBestiario

import database 

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyberpunk Tracker")
        self.showMaximized()
        
        # --- CARGA DE ESTILOS ---
        dir_path = os.path.dirname(os.path.abspath(__file__))
        ruta_qss = os.path.join(dir_path, "estilos.qss")
        if os.path.exists(ruta_qss):
            with open(ruta_qss, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())

        # --- ESTRUCTURA PRINCIPAL ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        contenedor_central = QWidget()
        self.layout_lista = QVBoxLayout(contenedor_central)
        self.layout_lista.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Carga de datos
        pjs_cargados, _ = database.cargar_partida_db()
        self.cat_temporales, self.cat_permanentes = database.cargar_catalogos_debuffos()
        
        self.pjs = pjs_cargados if pjs_cargados is not None else []
        self.registro_personajes = [] 

        # --- SECCIÓN JUGADORES ---
        header_pjs = PanelJugadoresHeader(self.abrir_dialogo_accion_global)
        self.layout_lista.addWidget(header_pjs)
        
        for p in self.pjs:
            widget_pj = PersonajeWidget(p, self.cat_temporales, self.cat_permanentes, es_npc=False)
            self.registro_personajes.append((p, widget_pj))
            self.layout_lista.addWidget(widget_pj)

        # --- SECCIÓN ADVERSARIOS ---
        self.header_npcs = PanelNPCsHeader(self.generar_npc_dinamico, self.abrir_dialogo_accion_global)
        self.layout_lista.addWidget(self.header_npcs)

        self.layout_npcs_activos = QVBoxLayout()
        self.layout_lista.addLayout(self.layout_npcs_activos)

        self.contadores_npcs = {}

        scroll.setWidget(contenedor_central)
        self.setCentralWidget(scroll)

    # ==========================================
    # GESTIÓN DE NPCs Y COMBATE (BATCH PROCESSING)
    # ==========================================

    def generar_npc_dinamico(self):
        datos_bestiario = database.obtener_bestiario_completo()
        if not datos_bestiario: return

        dialogo = DialogoBestiario(datos_bestiario, self)
        if dialogo.exec() != QDialog.DialogCode.Accepted:
            return

        escuadra = dialogo.escuadra_preparada
        if not escuadra: return

        piscina_colores = [
            ("#0000FF", "Azul"), ("#00FF00", "Verde"), ("#6A0101", "Rojo"), 
            ("#FFFF00", "Amarillo"), ("#FF00FF", "Morado"), ("#00FFFF", "Cian"),
            ("#FFA500", "Naranja"), ("#FFC0CB", "Rosa")
        ]

        npcs_activos = len([p for p, w in self.registro_personajes if p.es_npc and not p.es_boss])

        for lote in escuadra:
            for _ in range(lote['cantidad']):
                nuevo_npc = database.instanciar_npc_dinamico(lote['id'])
                if not nuevo_npc: continue

                if lote['es_jefe']:
                    nuevo_npc.es_boss = True
                    nuevo_npc.color_token_hex = "#5B5B5B" 
                    nuevo_npc.nombre = f"{nuevo_npc.nombre} (☠️)" 
                else:
                    nuevo_npc.es_boss = False
                    indice = npcs_activos % len(piscina_colores)
                    hex_color, nom_color = piscina_colores[indice]
                    nuevo_npc.color_token_hex = hex_color
                    nuevo_npc.nombre = f"{nuevo_npc.nombre} ({nom_color})"
                    npcs_activos += 1 

                widget_npc = PersonajeWidget(nuevo_npc, self.cat_temporales, self.cat_permanentes, es_npc=True)
                widget_npc.solicitar_eliminacion.connect(lambda p=nuevo_npc, w=widget_npc: self._eliminar_npc_widget(p, w))
                
                self.registro_personajes.append((nuevo_npc, widget_npc))
                self.layout_npcs_activos.addWidget(widget_npc)

        QApplication.processEvents() 
        bar = self.centralWidget().verticalScrollBar()
        bar.setValue(bar.maximum())
        
    def abrir_dialogo_accion_global(self, es_npc):
        """Función unificada para abrir el diálogo de AoE y Estados."""
        registro_filtrado = [(p, w) for p, w in self.registro_personajes if p.es_npc == es_npc]
        dialogo = DialogoAccionGlobal(registro_filtrado, self.cat_temporales, self.cat_permanentes, self)
        titulo = "Acción Global - Adversarios" if es_npc else "Acción Global - Jugadores"
        dialogo.setWindowTitle(titulo)
        dialogo.exec()

    def _eliminar_npc_widget(self, personaje_obj, widget_obj):
        registro_a_borrar = None
        for p, w in self.registro_personajes:
            if p == personaje_obj:
                registro_a_borrar = (p, w)
                break
        
        if registro_a_borrar:
            self.registro_personajes.remove(registro_a_borrar)

        self.layout_npcs_activos.removeWidget(widget_obj)
        widget_obj.deleteLater()

    def closeEvent(self, event):
        database.guardar_partida_db(self.pjs, []) 
        database.cerrar_conexion_pool() 
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    fuente_base = app.font()
    if fuente_base.pointSize() <= 0:
        fuente_base.setPointSize(10)
    app.setFont(fuente_base)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())