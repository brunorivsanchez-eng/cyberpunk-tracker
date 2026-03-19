import sys
import os
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel
from PyQt6.QtCore import Qt
from modelos import Personaje
from vistas import PersonajeWidget
import controlador

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyberpunk Pro Tracker")
        self.resize(1150, 600) 
        
        # Carga de Estilos QSS
        dir_path = os.path.dirname(os.path.abspath(__file__))
        ruta_qss = os.path.join(dir_path, "estilos.qss")
        if os.path.exists(ruta_qss):
            with open(ruta_qss, "r") as f:
                self.setStyleSheet(f.read())

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        contenedor_central = QWidget()
        self.layout_lista = QVBoxLayout(contenedor_central)
        self.layout_lista.setAlignment(Qt.AlignmentFlag.AlignTop)
        
       # --- NUEVA LÓGICA: Intento de Carga desde JSON ---
        pjs_cargados, npcs_cargados = controlador.cargar_partida()
        
        if pjs_cargados is not None and npcs_cargados is not None:
            # Si el archivo existe, usamos los datos guardados
            self.pjs = pjs_cargados
            self.npcs = npcs_cargados
        else:
            # Si es la primera vez que se abre, usamos las plantillas quemadas en código
            self.pjs = [
                Personaje("Dumy", 60, 11, 11, 6, armas={"Pistola": {"actual": 12, "max": 12}}, death_penalty=0),

            ]
            self.npcs = [
                Personaje("DumyNpc", 30, 4, 4, 0, armas={"Rifle Asalto": {"actual": 25, "max": 25}}, death_penalty=0),
                
            ]

        # 1. Renderizado de Jugadores
        for p in self.pjs:
            self.layout_lista.addWidget(PersonajeWidget(p, es_npc=False))

        separador = QLabel("ADVERSARIOS / NPCs")
        separador.setStyleSheet("color: #555555; font-size: 18px; font-weight: bold; margin-top: 15px; margin-bottom: 5px;")
        self.layout_lista.addWidget(separador)

        # 2. Renderizado de NPCs
        for npc in self.npcs:
            self.layout_lista.addWidget(PersonajeWidget(npc, es_npc=True))

        scroll.setWidget(contenedor_central)
        self.setCentralWidget(scroll)

    # --- NUEVA FUNCIÓN: Intercepción del evento de cierre ---
    def closeEvent(self, event):
        """
        Este método es nativo de PyQt6. Se ejecuta automáticamente cuando 
        el usuario presiona la 'X' para cerrar la ventana.
        """
        controlador.guardar_partida(self.pjs, self.npcs)
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())