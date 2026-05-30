import streamlit as st
from datetime import datetime
import pandas as pd

# Importaciones de nuestro backend estructurado
from src.models.contrato import ContratoLaboral
from src.models.pago import ConceptoNomina
from src.models.suspension import SuspensionContrato
from src.engine.calculador import CalculadorEngine

# Configuración de página de Streamlit
st.set_page_config(page_title="LegalTech - Liquidador Laboral", page_icon="⚖️", layout="wide")

# Inicialización de estados para simular persistencia de datos agregados
if "pagos_lista" not in st.session_state:
    st.session_state.pagos_lista = []
if "suspensiones_lista" not in st.session_state:
    st.session_state.suspensiones_lista = []

st.title("⚖️ Calculadora Avanzada de Liquidaciones Laborales")
st.markdown("---")

# ==========================================
# BARRA LATERAL: PARÁMETROS DEL CONTRATO
# ==========================================
st.sidebar.header("📋 Datos Principales del Contrato")

tipo_contrato = st.sidebar.selectbox(
    "Tipo de Contrato",
    ["Término Indefinido", "Término Fijo", "Obra o Labor"]
)

fecha_inicio = st.sidebar.date_input("Fecha de Inicio de Labores", datetime(1984, 8, 3))
fecha_final = st.sidebar.date_input("Fecha de Terminación", datetime(2023, 9, 25))

regimen = st.sidebar.radio(
    "Régimen de Cesantías (Ley 50/1990)",
    ["Anualizado (Post-Ley 50)", "Retroactivo (Tradicional / Pre-Ley 50)"],
    index=0
)
es_ley_50 = True if "Anualizado" in regimen else False

# Valores históricos de referencia para el año del cálculo (Ej: 2023)
st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Parámetros de Ley del Año de Cierre")
smlmv_input = st.sidebar.number_input("SMLMV Año de Liquidación ($)", value=1160000)
aux_trans_input = st.sidebar.number_input("Auxilio Transporte Año ($)", value=140606)

# Validación rápida de seguridad jurídica
if fecha_inicio > fecha_final:
    st.sidebar.error("❌ Error: La fecha de inicio no puede ser posterior a la fecha final.")

# ==========================================
# CUERPO PRINCIPAL: TRABAJO CON NOVEDADES
# ==========================================
tab1, tab2, tab3 = st.tabs(["💵 Gestión de Pagos (Art. 127/128)", "📉 Suspensiones (Art. 51/53)", "🧮 Motor de Liquidación"])

with tab1:
    st.subheader("Adición de Conceptos Mensuales Devengados")
    st.caption("Determina qué conceptos constituyen o no salario para la base prestacional.")
    
    col1, col2, col3 = st.columns([3, 2, 2])
    with col1:
        nombre_pago = st.text_input("Nombre del Concepto", placeholder="Ej: Salario Base, Horas Extras...")
    with col2:
        valor_pago = st.number_input("Monto Mensual ($)", min_value=0.0, value=0.0, step=50000.0)
    with col3:
        es_salarial = st.checkbox("¿Constituye Salario? (Art. 127 CST)", value=True)
        btn_pago = st.button("➕ Agregar Pago")
        
    if btn_pago and nombre_pago:
        st.session_state.pagos_lista.append({"nombre": nombre_pago, "valor": valor_pago, "es_salarial": es_salarial})
        st.success(f"Agregado: {nombre_pago}")

    # Mostrar tabla resumen de pagos actuales
    if st.session_state.pagos_lista:
        df_pagos = pd.DataFrame(st.session_state.pagos_lista)
        df_pagos["Tipo Jurídico"] = df_pagos["es_salarial"].apply(lambda x: "🟢 Salarial" if x else "🔴 No Salarial")
        st.dataframe(df_pagos[["nombre", "valor", "Tipo Jurídico"]], use_container_width=True)
        if st.button("🗑️ Limpiar Todos los Pagos"):
            st.session_state.pagos_lista = []
            st.rerun()

with tab2:
    st.subheader("Registro de Suspensiones Contractuales e Incapacidades")
    st.caption("Aplica el impacto asimétrico sobre las prestaciones sociales de acuerdo con el Art. 53 del CST.")
    
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
    with col1:
        tipo_susp = st.selectbox(
            "Causa Jurídica",
            [
                ("suspension_disciplinaria", "Suspension Disciplinaria"),
                ("fuerza_mayor_caso_fortuito", "Fuerza Mayor o Caso Fortuito (Incendio/Inundación)"),
                ("detencion_preventiva", "Detención Preventiva del Trabajador"),
                ("huelga_legal", "Huelga Legal Declarada"),
                ("licencia_no_remunerada", "Licencia No Remunerada"),
                ("incapacidad", "Incapacidad Médica (No Suspende)"),
                ("calamidad_domestica", "Calamidad Doméstica (No Suspende)")
            ],
            format_func=lambda x: x[1]
        )
    with col2:
        dias_susp = st.number_input("Días de Novedad", min_value=1, value=1)
    with col3:
        ano_susp = st.number_input("Año", min_value=1980, max_value=2026, value=datetime.now().year)
    with col4:
        mes_susp = st.text_input("Mes", value="Enero")
        btn_susp = st.button("➕ Agregar Novedad")

    if btn_susp:
        st.session_state.suspensiones_lista.append({
            "tipo_id": tipo_susp[0], "tipo_nombre": tipo_susp[1], "dias": dias_susp, "ano": ano_susp, "mes": mes_susp
        })
        st.success(f"Novedad registrada: {tipo_susp[1]}")

    # Mostrar tabla resumen de suspensiones actuales
    if st.session_state.suspensiones_lista:
        df_susp = pd.DataFrame(st.session_state.suspensiones_lista)
        # Identificar si descuenta mapeando con la lógica legal del backend
        def evalua_descuento(tid):
            return "📉 Descuenta de Cesantías/Vacaciones" if tid not in ["incapacidad", "calamidad_domestica"] else "⏳ Mantiene Derechos intactos"
        
        df_susp["Impacto de Ley"] = df_susp["tipo_id"].apply(evalua_descuento)
        st.dataframe(df_susp[["tipo_nombre", "dias", "ano", "mes", "Impacto de Ley"]], use_container_width=True)
        if st.button("🗑️ Limpiar Todas las Novedades"):
            st.session_state.suspensiones_lista = []
            st.rerun()

# ==========================================
# TAB 3: MOTOR Y CÁLCULOS TRANSPARENTES
# ==========================================
with tab3:
    st.subheader("Cálculo y Desglose Prestacional Estricto")
    
    if st.button("🧮 CORRER LIQUIDACIÓN DE LEY"):
        if fecha_inicio > fecha_final:
            st.error("No se puede calcular. Revise las fechas en la barra lateral.")
        else:
            # 1. Instanciar Entidad de Dominio (Contrato)
            contrato_usuario = ContratoLaboral(
                fecha_inicio=datetime.combine(fecha_inicio, datetime.min.time()),
                fecha_final=datetime.combine(fecha_final, datetime.min.time()),
                tipo_contrato=tipo_contrato,
                regimen_ley_50=es_ley_50
            )
            
            # Cargar los pagos mapeados desde la UI a objetos reales del backend
            for p in st.session_state.pagos_lista:
                contrato_usuario.agregar_pago(ConceptoNomina(p["nombre"], p["valor"], p["es_salarial"]))
                
            # Cargar las novedades mapeadas desde la UI a objetos reales del backend
            for s in st.session_state.suspensiones_lista:
                contrato_usuario.agregar_suspension(SuspensionContrato(s["tipo_id"], s["dias"], s["ano"], s["mes"]))
                
            # 2. Invocar Engine de Cálculos
            engine = CalculadorEngine(smlmv_ano_liquidacion=smlmv_input, aux_transporte_ano_liquidacion=aux_trans_input)
            
            # 3. Presentación de Resultados en UI
            st.success("✨ Liquidación procesada exitosamente. Desglose matemático disponible a continuación:")
            
            # Tarjeta de estado de inspección
            st.text(str(contrato_usuario))
            
            # Ejecutar operaciones
            dias_totales = contrato_usuario.calcular_dias_comerciales()
            
            # Consultas al motor para cada concepto
            res_prima = engine.liquidar_concepto_prestacional(contrato_usuario, dias_totales, "prima")
            res_cesantias = engine.liquidar_concepto_prestacional(contrato_usuario, dias_totales, "cesantias")
            res_intereses = engine.liquidar_intereses_cesantias(res_cesantias["valor_liquidado"], res_cesantias["dias_netos_calculados"])
            res_vacaciones = engine.liquidar_concepto_prestacional(contrato_usuario, dias_totales, "vacaciones")
            
            total_prestaciones = (
                res_prima["valor_liquidado"] + 
                res_cesantias["valor_liquidado"] + 
                res_intereses["valor_liquidado"] + 
                res_vacaciones["valor_liquidado"]
            )
            
            # Bloque de Métricas Generales
            c1, c2, c3 = st.columns(3)
            with c1:
                st.metric(label="Base Salarial Estricta", value=f"${contrato_usuario.obtener_base_salarial():,.2f}")
            with c2:
                st.metric(label="Días Totales Brutos", value=f"{dias_totales} días")
            with c3:
                st.metric(label="TOTAL PRESTACIONES SOCIALES", value=f"${total_prestaciones:,.2f}")
                
            st.markdown("### 📋 Desglose Técnico por Conceptos (Para el Jurado)")
            
            # Tarjetas detalladas expandibles para demostrar la transparencia matemática requerida por Orión
            for r in [res_prima, res_cesantias, res_intereses, res_vacaciones]:
                with st.expander(f"🔍 Detalles: {r['concepto']}"):
                    st.write(f"**Valor Liquidado:** ${r['valor_liquidado']:,.2f}")
                    if "base_calculo_total" in r:
                        st.write(f"* Base de Cálculo Aplicada: ${r['base_calculo_total']:,.2f} (Salarios + Auxilio de Transporte Aplicable)")
                        st.write(f"* Días Solicitados netos: {r['dias_netos_calculados']} (Días Brutos: {r['dias_solicitados']} - Suspensiones Restadas: {r['dias_descontados_suspension']})")
                    else:
                        st.write(f"* Base imponible sobre Cesantías Acumuladas: ${r['base_cesantias']:,.2f}")
                        st.write(f"* Tasa aplicada por Ley: {r['tasa_legal']} en proporción a {r['dias_netos_cesantias']} días netos.")