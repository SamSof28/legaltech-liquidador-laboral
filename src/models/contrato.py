from typing import List
from datetime import datetime

from src.models.pago import ConceptoNomina
from src.models.suspension import SuspensionContrato

class ContratoLaboral:
    def __init__(self, fecha_inicio: datetime, fecha_final: datetime, tipo_contrato: str, regimen_ley_50: bool) -> None:
        self.fecha_inicio: datetime = fecha_inicio
        self.fecha_final: datetime = fecha_final
        self.tipo_contrato: str = tipo_contrato
        self.regimen_ley_50: bool = regimen_ley_50
        self.pagos: List[ConceptoNomina] = []
        self.suspensiones: List[SuspensionContrato] = []

    def agregar_pago(self, pago: ConceptoNomina) -> None:
        self.pagos.append(pago)

    def agregar_suspension(self, suspension: SuspensionContrato) -> None:
        self.suspensiones.append(suspension)

    def calcular_dias_comerciales(self) -> int:
        f_in = self.fecha_inicio
        f_fin = self.fecha_final
        dias = (f_fin.year - f_in.year) * 360 + (f_fin.month - f_in.month) * 30 + (f_fin.day - f_in.day) + 1
        return max(0, dias)

    def obtener_base_salarial(self) -> float:
        return sum(pago.valor for pago in self.pagos if pago.es_salarial)

    def obtener_subsidio_transporte_aplicable(self, valor_aux_historico: float, smlmv_historico: float) -> float:
        base_salarial = self.obtener_base_salarial()
        if base_salarial <= (smlmv_historico * 2):
            return valor_aux_historico
        return 0.0

    def calcular_total_dias_suspension(self, afecta_concepto: str) -> int:
        total_dias = 0
        for susp in self.suspensiones:
            if afecta_concepto.lower() in ['cesantias', 'vacaciones'] and susp.debe_descontarse():
                total_dias += susp.dias
        return total_dias

    def __repr__(self) -> str:
        formato_fecha = "%d/%m/%Y"
        txt_regimen = "Ley 50 de 1990 (Anualizado)" if self.regimen_ley_50 else "Pre-Ley 50 (Retroactivo)"
        dias_brutos = self.calcular_dias_comerciales()
        base_sal = self.obtener_base_salarial()
        lines = [
            "╔" + "═" * 58 + "╗",
            f"║ 📄 CONTRATO LABORAL ({self.tipo_contrato.upper()})".ljust(59) + "║",
            "╠" + "═" * 58 + "╣",
            f"║ 🗓️  Periodo: {self.fecha_inicio.strftime(formato_fecha)} al {self.fecha_final.strftime(formato_fecha)}".ljust(59) + "║",
            f"║ ⏳ Tiempo Bruto: {dias_brutos} días comerciales".ljust(59) + "║",
            f"║ ⚖️  Régimen: {txt_regimen}".ljust(59) + "║",
            f"║ 💰 Salario Base Ordinario: ${base_sal:,.2f}".ljust(59) + "║",
            f"║ 📊 Novedades: {len(self.pagos)} Conceptos | {len(self.suspensiones)} Suspensiones".ljust(59) + "║",
            "╚" + "═" * 58 + "╝"
        ]
        return "\n".join(lines)