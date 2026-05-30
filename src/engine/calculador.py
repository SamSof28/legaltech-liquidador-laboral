from typing import Dict, Any
from src.models.contrato import ContratoLaboral

class CalculadorEngine:
    def __init__(self, smlmv_ano_liquidacion: float, aux_transporte_ano_liquidacion: float) -> None:
        """
        Inicializa el motor con los valores legales del año en que se realiza la liquidación.
        (Ej: Para el cierre del caso o año fiscal correspondiente).
        """
        self.smlmv: float = smlmv_ano_liquidacion
        self.aux_transporte: float = aux_transporte_ano_liquidacion

    def liquidar_concepto_prestacional(self, contrato: ContratoLaboral, dias_a_liquidar: int, concepto: str) -> Dict[str, Any]:
        """
        Calcula de manera aislada un concepto legal (cesantias, intereses, prima o vacaciones)
        determinando la base exacta y aplicando las suspensiones correspondientes.
        """
        concepto_norm = concepto.lower().strip()
        base_salarial_estricta = contrato.obtener_base_salarial()
        
        # 1. Determinar Base de Cálculo según el concepto jurídico
        if concepto_norm in ["cesantias", "prima"]:
            # Cesantías y Prima INCLUYEN Auxilio de Transporte por ley si se devengan menos de 2 SMLMV
            auxilio_aplicable = contrato.obtener_subsidio_transporte_aplicable(self.aux_transporte, self.smlmv)
            base_calculo = base_salarial_estricta + auxilio_aplicable
        elif concepto_norm == "vacaciones":
            # Las vacaciones NO incluyen Auxilio de Transporte (Art. 192 CST)
            base_calculo = base_salarial_estricta
            auxilio_aplicable = 0.0
        elif concepto_norm == "intereses_cesantias":
            # Se calculan sobre el valor acumulado de las cesantías, no directamente sobre el salario
            raise ValueError("Para calcular intereses use el método especializado 'liquidar_intereses_cesantias'")
        else:
            raise ValueError(f"Concepto '{concepto}' no soportado por el motor.")

        # 2. Aplicar el Impacto de las Suspensiones (Art. 53 CST)
        # La Prima de Servicios NO se ve afectada por suspensiones contractuales según jurisprudencia de la CSJ.
        if concepto_norm == "prima":
            dias_descontables = 0
        else:
            dias_descontables = contrato.calcular_total_dias_suspension(concepto_norm)
        
        # Días prestacionales netos (evitando valores negativos)
        dias_netos = max(0, dias_a_liquidar - dias_descontables)

        # 3. Aplicar Fórmulas Matemáticas del CST
        if concepto_norm in ["cesantias", "prima"]:
            valor_final = (base_calculo * dias_netos) / 360
        elif concepto_norm == "vacaciones":
            valor_final = (base_calculo * dias_netos) / 720

        return {
            "concepto": concepto.upper(),
            "base_salarial_estricta": base_salarial_estricta,
            "auxilio_transporte_incluido": auxilio_aplicable,
            "base_calculo_total": base_calculo,
            "dias_solicitados": dias_a_liquidar,
            "dias_descontados_suspension": dias_descontables,
            "dias_netos_calculados": dias_netos,
            "valor_liquidado": round(valor_final, 2)
        }

    def liquidar_intereses_cesantias(self, valor_cesantias: float, dias_netos_cesantias: int) -> Dict[str, Any]:
        """
        Calcula los intereses sobre cesantías basados en el monto ya liquidado de las mismas.
        Fórmula: (Cesantías * Días Netos * 12%) / 360
        """
        valor_final = (valor_cesantias * dias_netos_cesantias * 0.12) / 360
        return {
            "concepto": "INTERESES A LAS CESANTÍAS",
            "base_cesantias": valor_cesantias,
            "dias_netos_cesantias": dias_netos_cesantias,
            "tasa_legal": "12% Anual",
            "valor_liquidado": round(valor_final, 2)
        }