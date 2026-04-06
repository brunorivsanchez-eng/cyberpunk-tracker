import math

class Personaje:
    def __init__(self, nombre, max_hp, max_body_sp, max_head_sp, max_luck, move, 
                 armas=None, death_penalty=0, mejoras=None, id_db=None, es_npc=False):
        
        self.id_db = id_db  # <- NUEVO: Almacena el ID (id_jugador o id_npc) de la base de datos
        self.es_npc = es_npc # <- NUEVO: Identifica estructuralmente el origen del objeto
        self.nombre = nombre
        
        # Barras y Estadísticas
        self.max_hp = max_hp
        self.hp = max_hp
        self.reduccion_danio = 0
        self.max_body_sp = max_body_sp
        self.body_sp = max_body_sp
        self.max_head_sp = max_head_sp
        self.head_sp = max_head_sp
        self.max_luck = max_luck
        self.luck = max_luck
        self.move = int(move)
        self.max_move = int(move)
        
        # Otros
        self.death_penalty = int(death_penalty)
        self.armas = armas if armas is not None else {}
        self.mejoras = mejoras if mejoras is not None else []

    import math

# (Dentro de tu class Personaje:)

    def procesar_impacto(self, dano_base, mitad_sp, ignora_sp, cabeza, craneo, sin_abrasion, explosivo):
        """
        Ejecuta la lógica de mitigación, multiplicación y abrasión de manera desacoplada.
        Muta directamente los estados (hp, body_sp, head_sp) de la instancia.
        """
        # 1. Determinar zona de impacto
        es_cabeza = cabeza or craneo
        sp_actual = self.head_sp if es_cabeza else self.body_sp

        # 2. Calcular SP Efectivo (Filtro de Penetración)
        if ignora_sp:
            sp_efectivo = 0
        elif mitad_sp:
            sp_efectivo = math.ceil(sp_actual / 2)
        else:
            sp_efectivo = sp_actual

        # 3. Calcular Traspaso
        dano_penetrante = dano_base - sp_efectivo

        # Condición de salida: Si la armadura absorbe todo el daño, no hay efectos.
        if dano_penetrante <= 0:
            return

        # 4. Multiplicador de Zona Escalar
        multiplicador = 1
        if craneo:
            multiplicador = 4
        elif cabeza:
            multiplicador = 2
        
        dano_multiplicado = dano_penetrante * multiplicador

        # 5. Reducción Plana de Daño (Definida por la UI)
        reduccion = getattr(self, "reduccion_danio", 0)
        dano_final = max(0, dano_multiplicado - reduccion)

        # 6. Mutación de Puntos de Golpe (HP)
        self.hp = max(0, self.hp - dano_final)

        # 7. Abrasión de Armadura (Condicionada al traspaso previo)
        if not sin_abrasion:
            desgaste = 2 if explosivo else 1
            if es_cabeza:
                self.head_sp = max(0, self.head_sp - desgaste)
            else:
                self.body_sp = max(0, self.body_sp - desgaste)

    def curar(self, cantidad):
        self.hp = min(self.max_hp, self.hp + cantidad)

    def modificar_stat_secundario(self, atributo, cantidad_relativa):
        valor_actual = getattr(self, atributo)
        valor_maximo = getattr(self, f"max_{atributo}")
        
        nuevo_valor = max(0, min(valor_maximo, valor_actual + cantidad_relativa))
        setattr(self, atributo, nuevo_valor)

    def modificar_atributo_simple(self, atributo, cantidad_relativa):
        if not hasattr(self, atributo):
             print(f"Error: El atributo '{atributo}' no existe.")
             return
        valor_actual = getattr(self, atributo)
        nuevo_valor = max(0, min(99, valor_actual + cantidad_relativa))
        setattr(self, atributo, nuevo_valor)