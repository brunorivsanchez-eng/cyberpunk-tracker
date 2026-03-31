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

    def aplicar_impacto(self, danio_bruto, es_cabeza=False, es_melee=False, es_directo=False, reduccion_sp=1):
        if es_directo:
            danio_final = max(0, danio_bruto - self.reduccion_danio)
            self.hp = max(0, self.hp - danio_final)
            return

        sp_actual = self.head_sp if es_cabeza else self.body_sp
        proteccion = sp_actual // 2 if es_melee else sp_actual
        
        danio_que_pasa = max(0, danio_bruto - proteccion)
        
        if es_cabeza:
            danio_que_pasa *= 2
            
        danio_final = max(0, danio_que_pasa - self.reduccion_danio)
        self.hp = max(0, self.hp - danio_final)
        
        if danio_bruto > 0:
            if es_cabeza:
                self.head_sp = max(0, self.head_sp - reduccion_sp)
            else:
                self.body_sp = max(0, self.body_sp - reduccion_sp)

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