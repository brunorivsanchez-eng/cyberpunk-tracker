# --- ui/ui_paneles.py ---
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, 
                             QPushButton, QComboBox, QWidget) # <-- Asegúrate de incluir QFrame
from PyQt6.QtCore import Qt
import database

class PanelJugadoresHeader(QWidget):
    def __init__(self, callback_aoe, callback_estados, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        separador = QLabel("JUGADORES")
        separador.setObjectName("TituloSeccion")
        
        btn_aoe = QPushButton("💥 DAÑO AoE 💥")
        btn_aoe.setObjectName("BtnAoEDanio")
        btn_aoe.setFixedWidth(150)
        btn_aoe.clicked.connect(lambda: callback_aoe(es_npc=False))
        
        btn_estados = QPushButton("⚠️ ESTADOS AoE ⚠️")
        btn_estados.setObjectName("BtnAoEEstados")
        btn_estados.setFixedWidth(150)
        btn_estados.clicked.connect(lambda: callback_estados(es_npc=False))
        
        layout.addWidget(separador)
        layout.addStretch(1)
        layout.addWidget(btn_aoe)
        layout.addWidget(btn_estados)

class PanelNPCsHeader(QFrame):
    def __init__(self, callback_add, callback_aoe, callback_estados):
        super().__init__()
        self.setStyleSheet("background-color: #1A1A1A; border: 1px solid #333333; border-radius: 5px;")
        layout = QHBoxLayout(self)
        
        lbl_titulo = QLabel("ADVERSARIOS / NPCs")
        lbl_titulo.setStyleSheet("color: #FF0000; font-family: 'Orbitron', sans-serif; font-size: 16px; font-weight: bold; border: none;")
        layout.addWidget(lbl_titulo)
        
        layout.addStretch()
        
        # --- BOTÓN DEL BESTIARIO ---
        btn_add = QPushButton("📖 ABRIR BESTIARIO")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet("""
            QPushButton { background-color: #2C2C2C; color: white; border: 1px solid #555; padding: 5px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #FF0000; color: white; border: 1px solid #FF0000;}
        """)
        # Aquí conectamos usando exactamente el nombre del parámetro: callback_add
        btn_add.clicked.connect(callback_add)
        layout.addWidget(btn_add)

        # --- BOTÓN AoE DAÑO ---
        btn_aoe = QPushButton("💥DAÑO AoE💥")
        btn_aoe.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_aoe.setStyleSheet("""
            QPushButton { background-color: #4A0000; color: white; border: 1px solid #880000; padding: 5px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #FF0000; color: black; }
        """)
        btn_aoe.clicked.connect(lambda: callback_aoe(es_npc=True))
        layout.addWidget(btn_aoe)

        # --- BOTÓN AoE ESTADOS ---
        btn_estados_aoe = QPushButton("☣️ESTADOS☣️")
        btn_estados_aoe.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_estados_aoe.setStyleSheet("""
            QPushButton { background-color: #4A4A00; color: white; border: 1px solid #888800; padding: 5px 15px; font-weight: bold; }
            QPushButton:hover { background-color: #FFFF00; color: black; }
        """)
        btn_estados_aoe.clicked.connect(lambda: callback_estados(es_npc=True))
        layout.addWidget(btn_estados_aoe)