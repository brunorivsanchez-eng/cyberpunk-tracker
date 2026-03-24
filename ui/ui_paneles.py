# --- ui/ui_paneles.py ---
from PyQt6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget
from PyQt6.QtCore import Qt

class PanelJugadoresHeader(QFrame):
    """Encabezado para la sección de Jugadores."""
    def __init__(self, callback_accion_global):
        super().__init__()
        # Mantenemos el estilo oscuro y neón cian para PJs
        self.setStyleSheet("background-color: #1A1A1A; border: 1px solid #333333; border-radius: 5px;")
        layout = QHBoxLayout(self)
        
        lbl_titulo = QLabel("PLAYERS")
        lbl_titulo.setStyleSheet("""
            color: #00FFFF; 
            font-family: 'Orbitron', sans-serif; 
            font-size: 16px; 
            font-weight: bold; 
            border: none;
        """)
        layout.addWidget(lbl_titulo)
        
        layout.addStretch()
        
        # --- BOTÓN UNIFICADO DE ACCIÓN GLOBAL ---
        btn_accion = QPushButton("🌐 MULTI TARGET 🌐")
        btn_accion.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_accion.setFixedWidth(200)
        btn_accion.setStyleSheet("""
            QPushButton { 
                background-color: #002222; 
                color: #00FFFF; 
                border: 1px solid #008888; 
                padding: 5px 15px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #00FFFF; 
                color: black; 
            }
        """)
        # Enviamos es_npc=False al main
        btn_accion.clicked.connect(lambda: callback_accion_global(es_npc=False))
        layout.addWidget(btn_accion)


class PanelNPCsHeader(QFrame):
    """Encabezado para la sección de NPCs / Adversarios."""
    def __init__(self, callback_add, callback_accion_global):
        super().__init__()
        # Estilo oscuro y rojo para Adversarios
        self.setStyleSheet("background-color: #1A1A1A; border: 1px solid #333333; border-radius: 5px;")
        layout = QHBoxLayout(self)
        
        lbl_titulo = QLabel("NPCs")
        lbl_titulo.setStyleSheet("""
            color: #FF0000; 
            font-family: 'Orbitron', sans-serif; 
            font-size: 16px; 
            font-weight: bold; 
            border: none;
        """)
        layout.addWidget(lbl_titulo)
        
        layout.addStretch()
        
        # --- BOTÓN DEL BESTIARIO ---
        btn_add = QPushButton("📖 NEW ENEMY 📖")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { 
                background-color: #2C2C2C; 
                color: white; 
                border: 1px solid #555; 
                padding: 5px 15px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #FF0000; 
                color: white; 
                border: 1px solid #FF0000;
            }
        """)
        btn_add.clicked.connect(callback_add)
        layout.addWidget(btn_add)

        # --- BOTÓN UNIFICADO DE ACCIÓN GLOBAL ---
        btn_accion = QPushButton("🌐 MULTI TARGET 🌐")
        btn_accion.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_accion.setFixedWidth(200)
        btn_accion.setStyleSheet("""
            QPushButton { 
                background-color: #331111; 
                color: #FF4444; 
                border: 1px solid #880000; 
                padding: 5px 15px; 
                font-weight: bold; 
            }
            QPushButton:hover { 
                background-color: #FF0000; 
                color: black; 
            }
        """)
        # Enviamos es_npc=True al main
        btn_accion.clicked.connect(lambda: callback_accion_global(es_npc=True))
        layout.addWidget(btn_accion)