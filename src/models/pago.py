class ConceptoNomina:
    def __init__(self, nombre: str, valor: float, es_salarial: bool) -> None:
        """
        Modela cualquier pago, bonificación o recargo que recibe el trabajador.
        
        :param nombre: Identificador del concepto (ej: 'Salario Ordinario', 'Horas Extras')
        :param valor: Monto económico mensual o devengado
        :param es_salarial: True si constituye salario (Art. 127 CST), False si está desalarizado (Art. 128 CST)
        """
        self.nombre: str = nombre
        self.valor: float = valor
        self.es_salarial: bool = es_salarial

    def __repr__(self) -> str:
        tipo = "🟢 SALARIAL" if self.es_salarial else "🔴 NO SALARIAL"
        return f"   ▪️ {self.nombre.ljust(35)} | ${self.valor:,.2f} ({tipo})"