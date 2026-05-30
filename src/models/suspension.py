class SuspensionContrato:
    # Tipos de novedades permitidas y si suspenden legalmente el contrato (Art. 51 CST)
    TIPOS_VALIDOS = {
        "suspension_disciplinaria": True,
        "fuerza_mayor_caso_fortuito": True, # Incendios, inundaciones
        "detencion_preventiva": True,
        "huelga_legal": True,
        "licencia_no_remunerada": True,
        "incapacidad": False,          # NO es suspensión, el contrato sigue vigente
        "calamidad_domestica": False   # NO es suspensión
    }

    def __init__(self, tipo: str, dias: int, ano: int, mes: str) -> None:
        """
        Modela las novedades temporales que afectan la ejecución del contrato.
        """
        if tipo not in self.TIPOS_VALIDOS:
            raise ValueError(f"Tipo de novedad '{tipo}' no reconocido por el sistema laboral.")
            
        self.tipo: str = tipo
        self.dias: int = dias
        self.ano: int = ano
        self.mes: str = mes

    def debe_descontarse(self) -> bool:
        """
        Aplica el Artículo 53 del CST. Determina si el evento descuenta tiempo 
        para los cálculos de Cesantías y Vacaciones.
        """
        return self.TIPOS_VALIDOS[self.tipo]

    def __repr__(self) -> str:
        estado = "📉 Descuenta (Art. 53)" if self.debe_descontarse() else "⏳ No descuenta"
        desc = self.tipo.replace("_", " ").title()
        return f"   ▪️ {desc} ({self.mes}/{self.ano})".ljust(45) + f" | {self.dias} días -> {estado}"