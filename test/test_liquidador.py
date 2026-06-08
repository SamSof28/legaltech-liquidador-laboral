"""
Suite de Pruebas Automatizadas — LiquidaYA
Cobertura: Motor de cálculo CST, modelos de dominio y reglas jurídicas.
Ejecutar con: pytest test/ -v
"""
import pytest
from datetime import datetime
from src.models.contrato import ContratoLaboral
from src.models.pago import ConceptoNomina
from src.models.suspension import SuspensionContrato
from src.engine.calculador import CalculadorEngine

# ─── Fixtures reutilizables ────────────────────────────────────────────────────

SMLMV_2023 = 1_160_000
AUX_TRANS_2023 = 140_606

@pytest.fixture
def contrato_un_anio():
    """Contrato exacto de 1 año (360 días comerciales) con salario mínimo."""
    c = ContratoLaboral(
        fecha_inicio=datetime(2023, 1, 1),
        fecha_final=datetime(2023, 12, 30),   # 360 días exactos en calendario comercial
        tipo_contrato="Término Indefinido",
        regimen_ley_50=True
    )
    c.agregar_pago(ConceptoNomina("Salario Base", SMLMV_2023, True))
    return c

@pytest.fixture
def contrato_alto_salario():
    """Contrato con salario > 2 SMLMV (no aplica auxilio transporte)."""
    c = ContratoLaboral(
        fecha_inicio=datetime(2023, 1, 1),
        fecha_final=datetime(2023, 12, 30),
        tipo_contrato="Término Fijo",
        regimen_ley_50=True
    )
    c.agregar_pago(ConceptoNomina("Salario Base", 4_000_000, True))
    return c

@pytest.fixture
def engine():
    return CalculadorEngine(
        smlmv_ano_liquidacion=SMLMV_2023,
        aux_transporte_ano_liquidacion=AUX_TRANS_2023
    )

# ─── Tests: Días Comerciales ───────────────────────────────────────────────────

class TestDiasComerciales:
    def test_un_anio_exacto_360_dias(self, contrato_un_anio):
        """El año comercial colombiano debe ser de 360 días."""
        assert contrato_un_anio.calcular_dias_comerciales() == 360

    def test_un_mes_exacto_30_dias(self):
        """Un mes comercial debe ser de 30 días."""
        c = ContratoLaboral(datetime(2023, 1, 1), datetime(2023, 1, 30),
                            "Término Fijo", True)
        assert c.calcular_dias_comerciales() == 30

    def test_fechas_iguales_un_dia(self):
        """El primer día de trabajo cuenta como 1 día."""
        c = ContratoLaboral(datetime(2023, 6, 15), datetime(2023, 6, 15),
                            "Obra o Labor", True)
        assert c.calcular_dias_comerciales() == 1

    def test_no_retorna_dias_negativos(self):
        """Fechas invertidas no deben retornar días negativos."""
        c = ContratoLaboral(datetime(2023, 12, 1), datetime(2023, 1, 1),
                            "Término Indefinido", True)
        assert c.calcular_dias_comerciales() == 0

# ─── Tests: Base Salarial (Art. 127/128 CST) ──────────────────────────────────

class TestBaseSalarial:
    def test_solo_conceptos_salariales_suman(self):
        """Los conceptos no salariales NO deben incluirse en la base prestacional."""
        c = ContratoLaboral(datetime(2023,1,1), datetime(2023,12,30), "TI", True)
        c.agregar_pago(ConceptoNomina("Salario", 2_000_000, True))
        c.agregar_pago(ConceptoNomina("Bono Alimentacion", 300_000, False))  # No salarial
        c.agregar_pago(ConceptoNomina("Rodamiento", 150_000, False))          # No salarial
        assert c.obtener_base_salarial() == 2_000_000

    def test_multiples_conceptos_salariales(self):
        """Horas extras y comisiones salariales deben sumarse a la base."""
        c = ContratoLaboral(datetime(2023,1,1), datetime(2023,12,30), "TI", True)
        c.agregar_pago(ConceptoNomina("Salario Base", 2_000_000, True))
        c.agregar_pago(ConceptoNomina("Horas Extra", 400_000, True))
        c.agregar_pago(ConceptoNomina("Comision Ventas", 600_000, True))
        assert c.obtener_base_salarial() == 3_000_000

    def test_base_salarial_cero_sin_pagos(self):
        """Sin pagos registrados la base debe ser cero."""
        c = ContratoLaboral(datetime(2023,1,1), datetime(2023,12,30), "TI", True)
        assert c.obtener_base_salarial() == 0.0

# ─── Tests: Auxilio de Transporte ─────────────────────────────────────────────

class TestAuxilioTransporte:
    def test_aplica_si_salario_menor_2_smlmv(self, contrato_un_anio):
        """Trabajador con salario mínimo SÍ tiene derecho al auxilio de transporte."""
        aux = contrato_un_anio.obtener_subsidio_transporte_aplicable(AUX_TRANS_2023, SMLMV_2023)
        assert aux == AUX_TRANS_2023

    def test_no_aplica_si_salario_mayor_2_smlmv(self, contrato_alto_salario):
        """Trabajador con salario > 2 SMLMV NO tiene derecho al auxilio de transporte."""
        aux = contrato_alto_salario.obtener_subsidio_transporte_aplicable(AUX_TRANS_2023, SMLMV_2023)
        assert aux == 0.0

    def test_aplica_exactamente_en_el_limite_2_smlmv(self):
        """En el límite exacto de 2 SMLMV, sí aplica el auxilio."""
        c = ContratoLaboral(datetime(2023,1,1), datetime(2023,12,30), "TI", True)
        c.agregar_pago(ConceptoNomina("Salario", SMLMV_2023 * 2, True))  # Exactamente 2 SMLMV
        aux = c.obtener_subsidio_transporte_aplicable(AUX_TRANS_2023, SMLMV_2023)
        assert aux == AUX_TRANS_2023

# ─── Tests: Suspensiones (Art. 51/53 CST) ─────────────────────────────────────

class TestSuspensiones:
    def test_suspension_disciplinaria_descuenta(self):
        """Una suspensión disciplinaria debe descontar de cesantías y vacaciones."""
        s = SuspensionContrato("suspension_disciplinaria", 10, 2023, "Marzo")
        assert s.debe_descontarse() is True

    def test_incapacidad_no_descuenta(self):
        """Una incapacidad médica NO es suspensión y NO descuenta prestaciones."""
        s = SuspensionContrato("incapacidad", 15, 2023, "Abril")
        assert s.debe_descontarse() is False

    def test_calamidad_no_descuenta(self):
        """Una calamidad doméstica NO descuenta de las prestaciones."""
        s = SuspensionContrato("calamidad_domestica", 3, 2023, "Mayo")
        assert s.debe_descontarse() is False

    def test_tipo_invalido_lanza_excepcion(self):
        """Un tipo de novedad no reconocido debe lanzar ValueError."""
        with pytest.raises(ValueError):
            SuspensionContrato("vacaciones_ilegales", 5, 2023, "Junio")

    def test_suspension_descuenta_de_cesantias_no_de_prima(self, contrato_un_anio, engine):
        """La prima NO se ve afectada por suspensiones (jurisprudencia CSJ)."""
        contrato_un_anio.agregar_suspension(
            SuspensionContrato("suspension_disciplinaria", 30, 2023, "Febrero")
        )
        dias = contrato_un_anio.calcular_dias_comerciales()
        prima = engine.liquidar_concepto_prestacional(contrato_un_anio, dias, "prima")
        cesantias = engine.liquidar_concepto_prestacional(contrato_un_anio, dias, "cesantias")

        # Prima no descuenta, cesantías sí
        assert prima["dias_descontados_suspension"] == 0
        assert cesantias["dias_descontados_suspension"] == 30
        assert prima["valor_liquidado"] > cesantias["valor_liquidado"]

# ─── Tests: Motor de Liquidación ──────────────────────────────────────────────

class TestCalculadorEngine:
    def test_prima_formula_correcta(self, contrato_un_anio, engine):
        """Prima = (Salario + AuxTransporte) * Días / 360"""
        dias = contrato_un_anio.calcular_dias_comerciales()  # 360
        resultado = engine.liquidar_concepto_prestacional(contrato_un_anio, dias, "prima")
        esperado = round((SMLMV_2023 + AUX_TRANS_2023) * 360 / 360, 2)
        assert resultado["valor_liquidado"] == esperado

    def test_cesantias_formula_correcta(self, contrato_un_anio, engine):
        """Cesantías = (Salario + AuxTransporte) * Días / 360"""
        dias = contrato_un_anio.calcular_dias_comerciales()
        resultado = engine.liquidar_concepto_prestacional(contrato_un_anio, dias, "cesantias")
        esperado = round((SMLMV_2023 + AUX_TRANS_2023) * 360 / 360, 2)
        assert resultado["valor_liquidado"] == esperado

    def test_vacaciones_formula_correcta(self, contrato_un_anio, engine):
        """Vacaciones = Salario * Días / 720 (NO incluye auxilio transporte)."""
        dias = contrato_un_anio.calcular_dias_comerciales()
        resultado = engine.liquidar_concepto_prestacional(contrato_un_anio, dias, "vacaciones")
        esperado = round(SMLMV_2023 * 360 / 720, 2)
        assert resultado["valor_liquidado"] == esperado

    def test_vacaciones_no_incluye_auxilio_transporte(self, contrato_un_anio, engine):
        """Las vacaciones NUNCA incluyen el auxilio de transporte (Art. 192 CST)."""
        dias = contrato_un_anio.calcular_dias_comerciales()
        resultado = engine.liquidar_concepto_prestacional(contrato_un_anio, dias, "vacaciones")
        assert resultado["auxilio_transporte_incluido"] == 0.0

    def test_intereses_cesantias_12_porciento(self, engine):
        """Intereses = Cesantías * Días * 12% / 360"""
        resultado = engine.liquidar_intereses_cesantias(1_160_000, 360)
        esperado = round((1_160_000 * 360 * 0.12) / 360, 2)
        assert resultado["valor_liquidado"] == esperado

    def test_alto_salario_sin_auxilio_transporte(self, contrato_alto_salario, engine):
        """Con salario > 2 SMLMV, la base de cesantías NO incluye auxilio transporte."""
        dias = contrato_alto_salario.calcular_dias_comerciales()
        resultado = engine.liquidar_concepto_prestacional(contrato_alto_salario, dias, "cesantias")
        assert resultado["auxilio_transporte_incluido"] == 0.0
        assert resultado["base_calculo_total"] == 4_000_000

    def test_concepto_invalido_lanza_excepcion(self, contrato_un_anio, engine):
        """Un concepto no reconocido debe lanzar ValueError."""
        with pytest.raises(ValueError):
            engine.liquidar_concepto_prestacional(contrato_un_anio, 360, "indemnizacion_falsa")

# ─── Test de Integración: Caso Real Completo ──────────────────────────────────

class TestIntegracionCasoCompleto:
    def test_liquidacion_completa_coherente(self):
        """
        Caso de examen: Contrato 2 años, salario 2.5M, bono no salarial,
        30 días suspensión disciplinaria. Verifica coherencia entre conceptos.
        """
        contrato = ContratoLaboral(
            fecha_inicio=datetime(2021, 1, 1),
            fecha_final=datetime(2022, 12, 30),
            tipo_contrato="Término Indefinido",
            regimen_ley_50=True
        )
        contrato.agregar_pago(ConceptoNomina("Salario Base", 2_500_000, True))
        contrato.agregar_pago(ConceptoNomina("Bono Bienestar", 300_000, False))
        contrato.agregar_suspension(SuspensionContrato("suspension_disciplinaria", 30, 2022, "Marzo"))

        engine = CalculadorEngine(smlmv_ano_liquidacion=SMLMV_2023, aux_transporte_ano_liquidacion=AUX_TRANS_2023)
        dias = contrato.calcular_dias_comerciales()

        prima = engine.liquidar_concepto_prestacional(contrato, dias, "prima")
        cesantias = engine.liquidar_concepto_prestacional(contrato, dias, "cesantias")
        intereses = engine.liquidar_intereses_cesantias(cesantias["valor_liquidado"], cesantias["dias_netos_calculados"])
        vacaciones = engine.liquidar_concepto_prestacional(contrato, dias, "vacaciones")

        # Regla: salario 2.5M > 2 SMLMV (2.32M) → NO aplica auxilio transporte
        assert prima["auxilio_transporte_incluido"] == 0.0

        # Regla: Prima no descuenta por suspensión
        assert prima["dias_descontados_suspension"] == 0

        # Regla: Cesantías y vacaciones SÍ descuentan 30 días
        assert cesantias["dias_descontados_suspension"] == 30
        assert vacaciones["dias_descontados_suspension"] == 30

        # Regla: Todos los valores deben ser positivos
        total = (prima["valor_liquidado"] + cesantias["valor_liquidado"] +
                 intereses["valor_liquidado"] + vacaciones["valor_liquidado"])
        assert total > 0

        # Regla: Base no incluye el bono no salarial
        assert prima["base_salarial_estricta"] == 2_500_000