class Personaje:
    def __init__(self, nombre, max_hp, max_body_sp, max_head_sp, max_luck, armas=None, death_penalty=0):
        self.nombre = nombre
        self.max_hp = max_hp
        self.hp = max_hp
        self.max_body_sp = max_body_sp
        self.body_sp = max_body_sp
        self.max_head_sp = max_head_sp
        self.head_sp = max_head_sp
        self.max_luck = max_luck
        self.luck = max_luck
        
        # --- NUEVA ESTRUCTURA: Diccionario de armas ---
        self.armas = armas if armas is not None else {}
        
        self.death_penalty = death_penalty
        self.death_penalty = int(death_penalty)

    def aplicar_impacto(self, danio_bruto, es_cabeza=False, es_melee=False, es_directo=False):
        if es_directo:
            self.hp = max(0, self.hp - danio_bruto)
            return

        sp_actual = self.head_sp if es_cabeza else self.body_sp
        proteccion = sp_actual // 2 if es_melee else sp_actual
        
        danio_que_pasa = max(0, danio_bruto - proteccion)
        
        if es_cabeza:
            danio_que_pasa *= 2
            
        self.hp = max(0, self.hp - danio_que_pasa)
        
        if danio_bruto > 0:
            if es_cabeza:
                self.head_sp = max(0, self.head_sp - 1)
            else:
                self.body_sp = max(0, self.body_sp - 1)

    def curar(self, cantidad):
        self.hp = min(self.max_hp, self.hp + cantidad)

    def modificar_stat_secundario(self, atributo, cantidad_relativa):
        valor_actual = getattr(self, atributo)
        valor_maximo = getattr(self, f"max_{atributo}")
        
        nuevo_valor = max(0, min(valor_maximo, valor_actual + cantidad_relativa))
        setattr(self, atributo, nuevo_valor)

    def modificar_atributo_simple(self, atributo, cantidad_relativa):
        """
        Modifica un contador simple (balas, penalizador de muerte) sumando o restando.
        Garantiza que el resultado se mantenga entre 0 y un límite superior razonable (ej. 99).
        """
        if not hasattr(self, atributo):
             print(f"Error: El atributo '{atributo}' no existe.")
             return
        valor_actual = getattr(self, atributo)
        # Establecemos límites: mínimo 0, máximo 99
        nuevo_valor = max(0, min(99, valor_actual + cantidad_relativa))
        setattr(self, atributo, nuevo_valor)