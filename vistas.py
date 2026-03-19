from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QProgressBar, QLineEdit, QPushButton, 
                             QFrame, QSizePolicy, QComboBox)
from PyQt6.QtCore import Qt
import controlador

class PersonajeWidget(QFrame):
    def __init__(self, personaje_obj, es_npc=False):
            super().__init__()
            self.setObjectName("ContenedorPersonaje")
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            
            layout_principal = QVBoxLayout(self)
            layout_principal.setContentsMargins(8, 8, 8, 8)
            layout_principal.setSpacing(5)
            
            # --- CABECERA: NOMBRE Y BOTÓN RESET ---
            fila_cabecera = QHBoxLayout()
            
            lbl_nombre = QLabel(personaje_obj.nombre.upper())
            lbl_nombre.setObjectName("NombrePJ")
            
            btn_reset = QPushButton("🔄 RESET")
            btn_reset.setFixedWidth(65)
            btn_reset.setStyleSheet("background-color: #8B0000; color: white; font-weight: bold; border-radius: 4px;")
            
            fila_cabecera.addWidget(lbl_nombre)
            fila_cabecera.addStretch(1)
            fila_cabecera.addWidget(btn_reset)
            
            layout_principal.addLayout(fila_cabecera)

            self.widgets_referencia = {}
            self.widgets_referencia["nombre"] = lbl_nombre 
            # --- NUEVA LÍNEA: Guardamos el estado NPC en el diccionario ---
            self.widgets_referencia["es_npc"] = es_npc 
            
            btn_reset.clicked.connect(lambda checked, p=personaje_obj, w=self.widgets_referencia: 
                                    controlador.resetear_personaje(p, w))
            # --- FILA 1: HP Y COMBATE ---
            fila_hp = QHBoxLayout()
            
            lbl_hp = QLabel("HP")
            lbl_hp.setFixedWidth(60)
            lbl_hp.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")
            
            barra_hp = QProgressBar()
            barra_hp.setRange(0, personaje_obj.max_hp)
            barra_hp.setValue(personaje_obj.hp)
            barra_hp.setFormat("%v / %m") 
            barra_hp.setFixedWidth(225)
            barra_hp.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            self.widgets_referencia["hp"] = barra_hp
            
            controlador.actualizar_color_hp(personaje_obj, self.widgets_referencia)
            
            input_dano = QLineEdit()
            input_dano.setFixedWidth(38)
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
                                    controlador.procesar_ataque(personaje_obj, input_dano, c, m, d, self.widgets_referencia))
                fila_hp.addWidget(btn)

            if not es_npc:
                btn_curar = QPushButton("💚 Curar")
                btn_curar.setStyleSheet("background-color: #2E7D32; color: white;") 
                btn_curar.clicked.connect(lambda checked: 
                                        controlador.procesar_curacion(personaje_obj, input_dano, self.widgets_referencia))
                fila_hp.addWidget(btn_curar)

            fila_hp.addStretch(1)
            layout_principal.addLayout(fila_hp)

            # --- FILA 2: ESTADÍSTICAS AMPLIADAS (Layout Puro) ---
            layout_stats_ampliado = QHBoxLayout()
            layout_stats_ampliado.setContentsMargins(0, 0, 0, 0)
            layout_stats_ampliado.setSpacing(25)
            
            # COLUMNA IZQUIERDA: SP Y SUERTE
            columna_izquierda = QWidget()
            layout_col_izq = QVBoxLayout(columna_izquierda)
            layout_col_izq.setContentsMargins(0, 0, 0, 0)
            layout_col_izq.setSpacing(4)

            stats_secundarios = [
                ("BODY SP", "body_sp", "max_body_sp", "#4444FF"),
                ("HEAD SP", "head_sp", "max_head_sp", "#44FFFF")
            ]
            if not es_npc:
                stats_secundarios.append(("LUCK", "luck", "max_luck", "#FFCC00"))

            for nombre_ui, attr, attr_max, color in stats_secundarios:
                fila = QHBoxLayout()
                
                lbl = QLabel(nombre_ui)
                lbl.setFixedWidth(60)
                lbl.setStyleSheet("color: white; font-weight: bold; font-family: 'Arial', sans-serif; font-size: 11px;")
                
                barra = QProgressBar()
                barra.setRange(0, getattr(personaje_obj, attr_max))
                barra.setValue(getattr(personaje_obj, attr))
                barra.setFormat("%v / %m") 
                barra.setStyleSheet(f"QProgressBar::chunk {{ background-color: {color}; }}")
                barra.setFixedWidth(115)
                self.widgets_referencia[attr] = barra
                
                btn_menos = QPushButton("-")
                btn_menos.setObjectName("BtnAjuste")
                btn_menos.setFixedWidth(24)
                btn_menos.clicked.connect(lambda checked, p=personaje_obj, a=attr, cant=-1, b=barra: 
                                        controlador.ajustar_stat_secundario(p, a, cant, b))
                
                btn_mas = QPushButton("+")
                btn_mas.setObjectName("BtnAjuste")
                btn_mas.setFixedWidth(24)
                btn_mas.clicked.connect(lambda checked, p=personaje_obj, a=attr, cant=1, b=barra: 
                                        controlador.ajustar_stat_secundario(p, a, cant, b))

                fila.addWidget(lbl)
                fila.addWidget(barra)
                fila.addWidget(btn_menos)
                fila.addWidget(btn_mas)
                fila.addStretch(1)
                layout_col_izq.addLayout(fila)

            # COLUMNA 2 DERECHA: BALAS, MUERTE Y FUEGO
            columna_derecha = QWidget()
            layout_col_der = QVBoxLayout(columna_derecha)
            layout_col_der.setContentsMargins(0, 0, 0, 0)
            layout_col_der.setSpacing(4)

            # --- COLUMNA 2: MUERTE Y FUEGO ---
            columna_derecha = QWidget()
            layout_col_der = QVBoxLayout(columna_derecha)
            layout_col_der.setContentsMargins(0, 0, 0, 0)
            layout_col_der.setSpacing(4)

            if not es_npc:
                # Fila Muerte
                fila_death = QHBoxLayout()
                lbl_death_tit = QLabel("💀☠️💀")
                lbl_death_tit.setFixedWidth(60)
                lbl_death_tit.setStyleSheet("color: white; font-weight: bold; font-size: 11px;")

                lbl_val_death = QLabel(str(personaje_obj.death_penalty))
                lbl_val_death.setFixedWidth(25)
                lbl_val_death.setStyleSheet("color: #ECECD2; font-weight: bold; font-size: 13px; font-family: 'Orbitron';")
                lbl_val_death.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.widgets_referencia["death_penalty"] = lbl_val_death

                btn_menos_d = QPushButton("-")
                btn_menos_d.setObjectName("BtnAjuste")
                btn_menos_d.setFixedWidth(24)
                btn_menos_d.clicked.connect(lambda checked, p=personaje_obj, c=-1, l=lbl_val_death: 
                                            controlador.ajustar_atributo_simple(p, "death_penalty", c, l))
                
                btn_mas_d = QPushButton("+")
                btn_mas_d.setObjectName("BtnAjuste")
                btn_mas_d.setFixedWidth(24)
                btn_mas_d.clicked.connect(lambda checked, p=personaje_obj, c=1, l=lbl_val_death: 
                                        controlador.ajustar_atributo_simple(p, "death_penalty", c, l))

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
            lbl_fuego_tit.setStyleSheet("color: #FF4500; font-weight: bold; font-size: 11px;")

            btn_fuego_5 = QPushButton("🔥")
            btn_fuego_5.setObjectName("BtnAjuste")
            btn_fuego_5.setFixedWidth(38)
            btn_fuego_5.setStyleSheet("background-color: #8B0000; color: white; font-size: 10px;")
            btn_fuego_5.clicked.connect(lambda checked, p=personaje_obj, c=5, w=self.widgets_referencia: 
                                        controlador.aplicar_dano_fijo(p, c, w))

            btn_fuego_10 = QPushButton("🔥🔥🔥")
            btn_fuego_10.setObjectName("BtnAjuste")
            btn_fuego_10.setFixedWidth(50)
            btn_fuego_10.setStyleSheet("background-color: #8B0000; color: white; font-size: 10px;")
            btn_fuego_10.clicked.connect(lambda checked, p=personaje_obj, c=10, w=self.widgets_referencia: 
                                        controlador.aplicar_dano_fijo(p, c, w))

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
            lbl_armas_tit.setStyleSheet("color: #FF00FF; font-weight: bold; font-family: 'Arial', sans-serif; font-size: 11px;")
            layout_col_armas.addWidget(lbl_armas_tit)

            self.widgets_referencia["armas"] = {}

            if hasattr(personaje_obj, "armas") and personaje_obj.armas:
                for nombre_arma, datos_arma in personaje_obj.armas.items():
                    fila_arma = QHBoxLayout()
                    
                    lbl_nombre_arma = QLabel(nombre_arma)
                    lbl_nombre_arma.setFixedWidth(70)
                    lbl_nombre_arma.setStyleSheet("color: white; font-size: 10px;")
                    
                    lbl_val_arma = QLabel(str(datos_arma["actual"]))
                    lbl_val_arma.setFixedWidth(25)
                    lbl_val_arma.setStyleSheet("color: white; font-weight: bold; font-size: 12px;")
                    lbl_val_arma.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    self.widgets_referencia["armas"][nombre_arma] = lbl_val_arma

                    btn_menos_10 = QPushButton("-10")
                    btn_menos_10.setObjectName("BtnAjuste")
                    btn_menos_10.setFixedWidth(26)
                    btn_menos_10.clicked.connect(lambda checked, p=personaje_obj, n=nombre_arma, c=-10, l=lbl_val_arma: 
                                                controlador.ajustar_municion_arma(p, n, c, l))
                                                
                    btn_menos_1 = QPushButton("-1")
                    btn_menos_1.setObjectName("BtnAjuste")
                    btn_menos_1.setFixedWidth(26)
                    btn_menos_1.clicked.connect(lambda checked, p=personaje_obj, n=nombre_arma, c=-1, l=lbl_val_arma: 
                                                controlador.ajustar_municion_arma(p, n, c, l))

                    btn_max = QPushButton("MAX")
                    btn_max.setObjectName("BtnAjuste")
                    btn_max.setFixedWidth(32)
                    btn_max.clicked.connect(lambda checked, p=personaje_obj, n=nombre_arma, l=lbl_val_arma: 
                                            controlador.recargar_arma_maxima(p, n, l))

                    fila_arma.addWidget(lbl_nombre_arma)
                    fila_arma.addWidget(lbl_val_arma)
                    fila_arma.addWidget(btn_menos_10)
                    fila_arma.addWidget(btn_menos_1)
                    fila_arma.addWidget(btn_max)
                    fila_arma.addStretch(1)
                    layout_col_armas.addLayout(fila_arma)
            else:
                lbl_sin_armas = QLabel("Sin armas equipadas")
                lbl_sin_armas.setStyleSheet("color: #777777; font-size: 10px; font-style: italic;")
                layout_col_armas.addWidget(lbl_sin_armas)

            layout_col_armas.addStretch(1)

            # --- COLUMNA 4: ESTADOS Y DEBUFOS MULTIPLES ---
            columna_estados = QWidget()
            layout_col_est = QVBoxLayout(columna_estados)
            layout_col_est.setContentsMargins(15, 0, 0, 0)
            layout_col_est.setSpacing(4)

            lbl_estados_tit = QLabel("⚠️ DEBUFOS ACTIVOS ⚠️")
            lbl_estados_tit.setStyleSheet("color: #FFD700; font-weight: bold; font-family: 'Arial', sans-serif; font-size: 11px;")
            layout_col_est.addWidget(lbl_estados_tit)

            lista_estados = [
                "", 
                "Brazo roto: -2 a todas las acciones",
                "Pierna rota: Movimiento a la mitad",
                "Cegado: -4 a visión/ataques",
                "Sordera: Falla chequeos de alerta",
                "Envenenado: -1 HP por turno",
                "Inconsciente: Incapaz de actuar"
            ]

            self.widgets_referencia["debufos"] = []

            for _ in range(3):
                combo = QComboBox()
                combo.setFixedWidth(300)
                combo.addItems(lista_estados)
                layout_col_est.addWidget(combo)
                self.widgets_referencia["debufos"].append(combo)

            layout_col_est.addStretch(1)

            # --- ENSAMBLAJE FINAL DE COLUMNAS (Añadidas Columna 3 y 4) ---
            layout_stats_ampliado.addWidget(columna_izquierda)
            layout_stats_ampliado.addWidget(columna_derecha)
            layout_stats_ampliado.addWidget(columna_armas)
            layout_stats_ampliado.addWidget(columna_estados)
            
            layout_stats_ampliado.addStretch(1) 
            
            layout_principal.addLayout(layout_stats_ampliado)
            layout_principal.addStretch(1)