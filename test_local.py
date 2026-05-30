from datetime import datetime
from src.models.contrato import ContratoLaboral
from src.models.pago import ConceptoNomina
from src.models.suspension import SuspensionContrato
from src.engine.calculador import CalculadorEngine

# 1. Configurar Contrato del examen
contrato = ContratoLaboral(
    fecha_inicio=datetime(1984, 8, 3), fecha_final=datetime(2023, 9, 25),
    tipo_contrato="Término Indefinido", regimen_ley_50=True
)

# Cargar novedades económicas reales del examen
contrato.agregar_pago(ConceptoNomina("Salario Ordinario", 1780000, es_salarial=True))
contrato.agregar_pago(ConceptoNomina("Horas Extras", 150000, es_salarial=True))
contrato.agregar_pago(ConceptoNomina("Pacto No Salarial: Cortesía", 300000, es_salarial=False))
contrato.agregar_pago(ConceptoNomina("Pacto No Salarial: Bonificación", 180000, es_salarial=False))

# Registrar las suspensiones que afectaron el último periodo (Ej: Año 2021)
contrato.agregar_suspension(SuspensionContrato("licencia_no_remunerada", 15, 2021, "Noviembre"))
contrato.agregar_suspension(SuspensionContrato("fuerza_mayor_caso_fortuito", 8, 2021, "Septiembre"))
contrato.agregar_suspension(SuspensionContrato("incapacidad", 10, 2014, "Febrero")) # No descuenta por ley

# 2. Inicializar el motor con los valores del examen
# Supongamos los valores aproximados del año de cierre del examen
engine = CalculadorEngine(smlmv_ano_liquidacion=1160000, aux_transporte_ano_liquidacion=140606)

print("=== VERIFICACIÓN DE ANÁLISIS JURÍDICO ===")
# Ejemplo: Liquidar la prima del último año (360 días del periodo pendiente)
res_prima = engine.liquidar_concepto_prestacional(contrato, dias_a_liquidar=360, concepto="prima")
res_cesantias = engine.liquidar_concepto_prestacional(contrato, dias_a_liquidar=360, concepto="cesantias")
res_intereses = engine.liquidar_intereses_cesantias(res_cesantias["valor_liquidado"], res_cesantias["dias_netos_calculados"])
res_vacaciones = engine.liquidar_concepto_prestacional(contrato, dias_a_liquidar=360, concepto="vacaciones")

# Mostrar la transparencia del desglose
for res in [res_prima, res_cesantias, res_intereses, res_vacaciones]:
    print(f"\n📌 {res['concepto']}:")
    print(f"   💸 Valor Final: ${res['valor_liquidado']:,.2f}")
    if "base_calculo_total" in res:
        print(f"   📐 Base de cálculo: ${res['base_calculo_total']:,.2f} (Salarial: ${res['base_salarial_estricta']:,.2f} + Aux: ${res['auxilio_transporte_included'] if 'auxilio_transporte_included' in res else res.get('auxilio_transporte_incluido', 0):,.2f})")
        print(f"   ⏱️  Días Netos: {res['dias_netos_calculados']} (Solicitados: {res['dias_solicitados']} - Descuentos Ley: {res['dias_descontados_suspension']})")