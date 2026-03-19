import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QProgressBar, QLineEdit, 
                             QPushButton, QScrollArea, QFrame)
from PyQt6.QtCore import Qt
from modelos import Personaje
import controlador

ESTILO_CYBERPUNK = """
    QMainWindow { background-color: #121212; }
    
    QFrame#ContenedorPersonaje {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        border-radius: 15px;
    }
    
    QLabel#NombrePJ {
        color: #00FF00;
        font-family: 'Orbitron', sans-serif;
        font-size: 18px;
        font-weight: bold;
    }
    
    QProgressBar {
        border: 1px solid #444444;
        border-radius: 8px;
        background-color: #2C2C2C;
        text-align: center;
        color: white;
        font-weight: bold;
        height: 25px;
    }
    
    QProgressBar::chunk { border-radius: 7px; }

    QLineEdit {
        background-color: #2C2C2C;
        color: white;
        border: 1px solid #444444;
        border-radius: 5px;
        padding: 2px;
    }

    QPushButton {
        background-color: #333333;
        color: #00FF00;
        border-radius: 5px;
        font-weight: bold;
        padding: 5px;
    }
    QPushButton:hover { background-color: #444444; }
    
    QPushButton#BtnAjuste {
        font-size: 14px;
        background-color: #2C2C2C;
        border: 1px solid #555555;
    }
    QPushButton#BtnAjuste:hover { background-color: #555555; }
"""

class PersonajeWidget(QFrame):
    def __init__(self, personaje_obj):
        super().__init__()
        self.setObjectName("ContenedorPersonaje")
        layout_principal = QVBoxLayout(self)
        
        lbl_nombre = QLabel(personaje_obj.nombre.upper())
        lbl_nombre.setObjectName("NombrePJ")
        layout_principal.addWidget(lbl_nombre)

        self.barras = {}

        # --- PANEL DE COMBATE (HP) ---
        fila_hp = QHBoxLayout()
        
        lbl_hp = QLabel("HP (Combate)")
        lbl_hp.setFixedWidth(80)
        lbl_hp.setStyleSheet("color: white; font-weight: bold;")
        
        barra_hp = QProgressBar()
        barra_hp.setRange(0, personaje_obj.max_hp)
        barra_hp.setValue(personaje_obj.hp)
        barra_hp.setFormat("%v / %m") 
        
        # Eliminamos el if/else de aquí. El color lo manejará una función nueva.
        controlador.actualizar_color_hp(personaje_obj, barra_hp)

        self.barras["hp"] = barra_hp
        
        input_dano = QLineEdit()
        input_dano.setFixedWidth(50)
        input_dano.setPlaceholderText("0")
        
        fila_hp.addWidget(lbl_hp)
        fila_hp.addWidget(barra_hp)
        fila_hp.addWidget(input_dano)

        ataques = [
            ("Cuerpo", False, False, False),
            ("Cabeza", True, False, False),
            ("M. Cuerpo", False, True, False),
            ("M. Cabeza", True, True, False),
            ("⚡ Directo", False, False, True)
        ]

        for texto, cabeza, melee, directo in ataques:
            btn = QPushButton(texto)
            btn.clicked.connect(lambda checked, c=cabeza, m=melee, d=directo: 
                                controlador.procesar_ataque(personaje_obj, input_dano, c, m, d, self.barras))
            fila_hp.addWidget(btn)

        btn_curar = QPushButton("💚 Curar")
        btn_curar.setStyleSheet("background-color: #2E7D32; color: white;") 
        btn_curar.clicked.connect(lambda checked: 
                                  controlador.procesar_curacion(personaje_obj, input_dano, self.barras))
        fila_hp.addWidget(btn_curar)

        layout_principal.addLayout(fila_hp)

        # --- PANEL DE ATRIBUTOS SECUNDARIOS (SP y Suerte) ---
        stats_secundarios = [
            ("BODY SP", "body_sp", "max_body_sp", "#4444FF"),
            ("HEAD SP", "head_sp", "max_head_sp", "#44FFFF"),
            ("LUCK", "luck", "max_luck", "#FFCC00")
        ]

        for nombre_ui, attr, attr_max, color in stats_secundarios:
            fila = QHBoxLayout()
            actual = getattr(personaje_obj, attr)
            maximo = getattr(personaje_obj, attr_max)

            lbl = QLabel(nombre_ui)
            lbl.setFixedWidth(80)
            lbl.setStyleSheet("color: white; font-weight: bold;")
            
            barra = QProgressBar()
            barra.setRange(0, maximo)
            barra.setValue(actual)
            barra.setFormat("%v / %m") 
            barra.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
            self.barras[attr] = barra
            
            # Botón Decrementar (-1)
            btn_menos = QPushButton("-")
            btn_menos.setObjectName("BtnAjuste")
            btn_menos.setFixedWidth(30)
            btn_menos.clicked.connect(lambda checked, p=personaje_obj, a=attr, cant=-1, b=barra: 
                                      controlador.ajustar_stat_secundario(p, a, cant, b))
            
            # Botón Incrementar (+1)
            btn_mas = QPushButton("+")
            btn_mas.setObjectName("BtnAjuste")
            btn_mas.setFixedWidth(30)
            btn_mas.clicked.connect(lambda checked, p=personaje_obj, a=attr, cant=1, b=barra: 
                                      controlador.ajustar_stat_secundario(p, a, cant, b))

            fila.addWidget(lbl)
            fila.addWidget(barra)
            fila.addWidget(btn_menos)
            fila.addWidget(btn_mas)
            
            fila.addStretch(1) 
            
            layout_principal.addLayout(fila)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cyberpunk Pro Tracker - Interfaz Optimizada")
        self.resize(1050, 600)
        self.setStyleSheet(ESTILO_CYBERPUNK)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        contenedor_central = QWidget()
        self.layout_lista = QVBoxLayout(contenedor_central)
        self.layout_lista.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        personajes = [
            Personaje("V", 100, 10, 10, 5),
            Personaje("Jony", 80, 5, 5, 10)
        ]

        for p in personajes:
            self.layout_lista.addWidget(PersonajeWidget(p))

        scroll.setWidget(contenedor_central)
        self.setCentralWidget(scroll)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = MainWindow()
    ventana.show()
    sys.exit(app.exec())