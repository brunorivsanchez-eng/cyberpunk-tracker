class Personaje:
    def __init__(self, nombre, hp, body_sp, head_sp, luck):
        self.nombre = nombre
        self.hp = int(hp)
        self.max_hp = int(hp)
        self.body_sp = int(body_sp)
        self.max_body_sp = int(body_sp)
        self.head_sp = int(head_sp)
        self.max_head_sp = int(head_sp)
        self.luck = int(luck)
        self.max_luck = int(luck)

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
        """
        Modifica un atributo sumando o restando el valor relativo.
        Garantiza que el resultado se mantenga entre 0 y el límite máximo del atributo.
        """
        valor_actual = getattr(self, atributo)
        valor_maximo = getattr(self, f"max_{atributo}")
        
        nuevo_valor = max(0, min(valor_maximo, valor_actual + cantidad_relativa))
        setattr(self, atributo, nuevo_valor)