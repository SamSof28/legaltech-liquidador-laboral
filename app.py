import streamlit as st
from datetime import datetime
import pandas as pd

from src.models.contrato import ContratoLaboral
from src.models.pago import ConceptoNomina
from src.models.suspension import SuspensionContrato
from src.engine.calculador import CalculadorEngine

# ─── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="LiquidaYA — Liquidador Laboral Colombia",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─── CSS personalizado ─────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Tarjetas de métricas con borde teal */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, #0D1B2A 0%, #1A2E45 100%);
    border: 1px solid #00C9A7;
    border-radius: 10px;
    padding: 16px;
    color: white;
}
div[data-testid="metric-container"] label {
    color: #00C9A7 !important;
    font-weight: 600;
}
div[data-testid="metric-container"] div[data-testid="metric-value"] {
    color: white !important;
    font-size: 1.6rem !important;
}
/* Tarjetas de guía */
.guia-card {
    background: linear-gradient(135deg, #0D1B2A, #1A2E45);
    border-left: 4px solid #00C9A7;
    border-radius: 8px;
    padding: 18px 20px;
    margin: 10px 0;
    color: white;
}
.guia-card h4 { color: #00C9A7; margin: 0 0 8px 0; font-size: 1rem; }
.guia-card p  { color: #CBD5E1; margin: 0; font-size: 0.9rem; line-height: 1.5; }

/* Alerta legal */
.alerta-legal {
    background: linear-gradient(135deg, #1a1200, #2d1f00);
    border-left: 4px solid #F59E0B;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 10px 0;
    color: #FCD34D;
    font-size: 0.88rem;
}

/* Paso numerado */
.paso {
    display: flex;
    align-items: flex-start;
    gap: 14px;
    margin: 12px 0;
    padding: 14px;
    background: #0D1B2A;
    border-radius: 8px;
    border: 1px solid #1A2E45;
}
.paso-num {
    background: #00C9A7;
    color: #0D1B2A;
    font-weight: 800;
    font-size: 1rem;
    border-radius: 50%;
    width: 32px;
    height: 32px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
}
.paso-texto h5 { color: white; margin: 0 0 4px 0; font-size: 0.95rem; }
.paso-texto p  { color: #94A3B8; margin: 0; font-size: 0.85rem; }

/* Badge de resultado */
.resultado-total {
    background: linear-gradient(135deg, #004d3d, #006b55);
    border: 2px solid #00C9A7;
    border-radius: 12px;
    padding: 24px;
    text-align: center;
    margin: 16px 0;
}
.resultado-total .label { color: #00C9A7; font-size: 0.85rem; font-weight: 700; letter-spacing: 2px; }
.resultado-total .valor { color: white; font-size: 2.5rem; font-weight: 800; margin: 8px 0; }
.resultado-total .sub   { color: #94A3B8; font-size: 0.8rem; }
</style>
""", unsafe_allow_html=True)

# ─── Estado de sesión ──────────────────────────────────────────────────────────
if "pagos_lista" not in st.session_state:
    st.session_state.pagos_lista = []
if "suspensiones_lista" not in st.session_state:
    st.session_state.suspensiones_lista = []

# ─── Header principal ──────────────────────────────────────────────────────────
col_logo, col_titulo = st.columns([1, 11])
with col_logo:
    st.markdown("## ⚖️")
with col_titulo:
    st.markdown("# LiquidaYA")
    st.caption("Calculadora oficial de prestaciones sociales — Código Sustantivo del Trabajo Colombia")

st.markdown("---")

# ══════════════════════════════════════════════════════════════════
# BARRA LATERAL
# ══════════════════════════════════════════════════════════════════
st.sidebar.markdown("## 📋 Datos del Contrato")
st.sidebar.markdown("*Ingresa la información básica del trabajador*")

tipo_contrato = st.sidebar.selectbox(
    "Tipo de Contrato",
    ["Término Indefinido", "Término Fijo", "Obra o Labor"],
    help="Selecciona el tipo de vinculación laboral pactado"
)

fecha_inicio = st.sidebar.date_input(
    "📅 Fecha de Inicio de Labores",
    datetime(2024, 1, 1),
    min_value=datetime(1950, 1, 1),
    max_value=datetime(2026, 12, 31),
    help="Primer día de trabajo efectivo"
)
fecha_final = st.sidebar.date_input(
    "📅 Fecha de Terminación",
    datetime(2024, 12, 30),
    min_value=datetime(1950, 1, 1),
    max_value=datetime(2026, 12, 31),
    help="Último día de trabajo (inclusive)"
)

regimen = st.sidebar.radio(
    "Régimen de Cesantías",
    ["Anualizado (Post-Ley 50/1990)", "Retroactivo (Pre-Ley 50)"],
    index=0,
    help="La mayoría de contratos modernos son Post-Ley 50. Si el contrato empezó antes de 1991, consulta con un abogado."
)
es_ley_50 = "Anualizado" in regimen

st.sidebar.markdown("---")
st.sidebar.markdown("### ⚙️ Valores Legales del Año")
st.sidebar.caption("Estos valores cambian cada año. Usa los del año en que termina el contrato.")

SMLMV_POR_ANIO = {
    2026: 1_750_905, 2025: 1_423_500, 2024: 1_300_000,
    2023: 1_160_000, 2022: 1_000_000, 2021: 908_526,
    2020: 877_803,   2019: 828_116,   2018: 781_242,
}
AUX_TRANS_POR_ANIO = {
    2026: 249_095,  2025: 200_000,  2024: 162_000,
    2023: 140_606,  2022: 117_172,  2021: 106_454,
    2020: 102_854,  2019: 97_032,   2018: 88_211,
}

anio_liquidacion = fecha_final.year if fecha_final.year in SMLMV_POR_ANIO else 2023
smlmv_sugerido   = SMLMV_POR_ANIO.get(anio_liquidacion, 1_160_000)
aux_sugerido     = AUX_TRANS_POR_ANIO.get(anio_liquidacion, 140_606)

smlmv_input     = st.sidebar.number_input("SMLMV ($)", value=smlmv_sugerido,
                                           help="Salario Mínimo Legal Mensual Vigente del año del contrato")
aux_trans_input = st.sidebar.number_input("Auxilio de Transporte ($)", value=aux_sugerido,
                                           help="Valor oficial del auxilio de transporte del año del contrato")

if anio_liquidacion in SMLMV_POR_ANIO:
    st.sidebar.success(f"✅ Valores {anio_liquidacion} cargados automáticamente")

if fecha_inicio > fecha_final:
    st.sidebar.error("❌ La fecha de inicio no puede ser posterior a la fecha final.")

# ══════════════════════════════════════════════════════════════════
# TABS PRINCIPALES
# ══════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs([
    "💵 Pagos Recibidos",
    "📉 Suspensiones",
    "🧮 Calcular Liquidación",
    "📘 Guía de Usuario"
])

# ─── Diccionario de conceptos ─────────────────────────────────────

CONCEPTOS_PREDEFINIDOS = {

    # ══════════════════════════════════════════════════════
    # ✅ SALARIALES — Art. 127 CST
    # Cuentan para liquidar prestaciones sociales
    # ══════════════════════════════════════════════════════

    "Salario Ordinario Fijo": {
        "es_salarial": True,
        "descripcion": "Remuneración ordinaria fija pactada en el contrato (ej: $2.000.000 al mes).",
        "icono": "💼",
        "referencia": "Art. 127 CST — Numeral 1"
    },
    "Salario Variable (por día o destajo)": {
        "es_salarial": True,
        "descripcion": "Remuneración variable por día laborado o producción (ej: $80.000 por día).",
        "icono": "📅",
        "referencia": "Art. 127 CST — Numeral 1"
    },
    "Trabajo Suplementario / Horas Extras": {
        "es_salarial": True,
        "descripcion": "Valor pagado por trabajo adicional a la jornada ordinaria de 8 horas, diurno o nocturno.",
        "icono": "⏱️",
        "referencia": "Art. 127 CST — Trabajo suplementario"
    },
    "Trabajo en Días de Descanso Obligatorio": {
        "es_salarial": True,
        "descripcion": "Pago por trabajar en domingos, festivos o días de descanso remunerado.",
        "icono": "📆",
        "referencia": "Art. 127 CST — Días de descanso obligatorio"
    },
    "Porcentajes sobre Ventas / Comisiones": {
        "es_salarial": True,
        "descripcion": "Comisiones habituales por ventas, metas o porcentaje sobre negociaciones.",
        "icono": "📈",
        "referencia": "Art. 127 CST — Porcentajes sobre ventas y comisiones"
    },
    "Bonificaciones Habituales": {
        "es_salarial": True,
        "descripcion": "Bonificaciones que se pagan de forma regular y periódica, no ocasional. Su habitualidad las convierte en salario aunque no se llamen así.",
        "icono": "🔄",
        "referencia": "Art. 127 CST — Bonificaciones habituales"
    },
    "Sobresueldos": {
        "es_salarial": True,
        "descripcion": "Pagos adicionales al salario base, reconocidos de forma regular por el empleador.",
        "icono": "➕",
        "referencia": "Art. 127 CST — Sobresueldos"
    },
    "Viáticos Habituales — Manutención y Alojamiento": {
        "es_salarial": True,
        "descripcion": "Parte de los viáticos habituales destinada a alimentación, alojamiento, lavandería y elementos de aseo. Solo esta porción es salario.",
        "icono": "🏨",
        "referencia": "Art. 127 CST — Viáticos habituales (manutención y alojamiento)"
    },
    "Salario en Especie (sin pacto de exclusión)": {
        "es_salarial": True,
        "descripcion": "Beneficios no monetarios como vivienda, vehículo o alimentación que forman parte del salario cuando no existe pacto expreso de exclusión salarial.",
        "icono": "🏠",
        "referencia": "Art. 127 CST — Salario en especie"
    },
    "Propina Pagada por el Empleador": {
        "es_salarial": True,
        "descripcion": "Propina que reconoce y paga directamente el empleador al trabajador (distinta a la propina voluntaria del cliente).",
        "icono": "💵",
        "referencia": "Art. 127 CST — Propina del empleador"
    },

    # ══════════════════════════════════════════════════════
    # 🔵 NO SALARIALES — Art. 128 CST
    # NO cuentan para liquidar prestaciones sociales
    # ══════════════════════════════════════════════════════

    "Primas Ocasionales (Mera Liberalidad)": {
        "es_salarial": False,
        "descripcion": "Primas que el empleador paga esporádicamente por decisión propia, sin obligación contractual ni periodicidad fija.",
        "icono": "🎁",
        "referencia": "Art. 128 CST — Numeral 1"
    },
    "Bonificaciones Ocasionales (Mera Liberalidad)": {
        "es_salarial": False,
        "descripcion": "Bonos que se entregan de vez en cuando sin periodicidad ni obligación. Aunque sean habituales en la práctica, si hay pacto expreso de no salarialidad no constituyen salario.",
        "icono": "🎀",
        "referencia": "Art. 128 CST — Numeral 1"
    },
    "Participación de Utilidades": {
        "es_salarial": False,
        "descripcion": "Distribución de utilidades de la empresa al trabajador. Puede ser habitual y aun así no constituir salario — es un acto de liberalidad del empleador.",
        "icono": "📊",
        "referencia": "Art. 128 CST — Numeral 2"
    },
    "Gastos de Representación": {
        "es_salarial": False,
        "descripcion": "Dinero entregado para cubrir gastos de imagen o representación de la empresa ante clientes (restaurantes, floristerías, hoteles, clubes).",
        "icono": "🍽️",
        "referencia": "Art. 128 CST — Numeral 4"
    },
    "Viáticos de Transporte (Habituales)": {
        "es_salarial": False,
        "descripcion": "Parte de los viáticos habituales destinada exclusivamente al transporte. Solo la porción de transporte no es salario; la de manutención sí lo es.",
        "icono": "🚌",
        "referencia": "Art. 128 CST — Numeral 9"
    },
    "Viáticos Ocasionales (Accidentales)": {
        "es_salarial": False,
        "descripcion": "Viáticos pagados por desplazamientos esporádicos y no habituales. Al ser ocasionales, no constituyen salario en ninguna de sus partes.",
        "icono": "🗺️",
        "referencia": "Art. 128 CST — Numeral 8"
    },
    "Auxilio de Transporte (Legal)": {
        "es_salarial": False,
        "descripcion": "Subsidio legal de transporte establecido por el Gobierno ($250.000 en 2026). No es salario, pero por ley se incluye en la base de liquidación de cesantías y prima si el salario es ≤ 2 SMLMV.",
        "icono": "🚇",
        "referencia": "Art. 128 CST + Ley 15/1959 — Nota: se suma a base prestacional si salario ≤ 2 SMLMV"
    },
    "Medios de Transporte (Vehículo, Gasolina, Parqueadero)": {
        "es_salarial": False,
        "descripcion": "Vehículos, aceite, gasolina, parqueaderos, pasajes aéreos, taxis o cuotas de vehículo por leasing entregados para el desempeño de funciones.",
        "icono": "🚗",
        "referencia": "Art. 128 CST — Numeral 4"
    },
    "Auxilio de Alimentación (Pactado como No Salarial)": {
        "es_salarial": False,
        "descripcion": "Subsidio de alimentación pactado expresamente como no constitutivo de salario (ej: Sodexo, Bigpass, casino empresarial).",
        "icono": "🥗",
        "referencia": "Art. 128 CST — Numeral 6"
    },
    "Habitación o Vivienda (Pactada como No Salarial)": {
        "es_salarial": False,
        "descripcion": "Vivienda o subsidio de arrendamiento reconocido con pacto expreso de no salarialidad.",
        "icono": "🏘️",
        "referencia": "Art. 128 CST — Numeral 6"
    },
    "Prima Técnica (Antigüedad, Escolaridad, Desplazamiento)": {
        "es_salarial": False,
        "descripcion": "Primas extrasalariales pactadas: por años de servicio, nivel educativo o desplazamiento, cuando existe acuerdo expreso de no salarialidad.",
        "icono": "🎓",
        "referencia": "Art. 128 CST — Numeral 6"
    },
    "Prima Extralegal (Navidad, Vacaciones, etc.)": {
        "es_salarial": False,
        "descripcion": "Primas adicionales a las legales (prima semestral) pactadas como no salariales en el contrato o convención colectiva.",
        "icono": "🎄",
        "referencia": "Art. 128 CST — Numeral 6"
    },
    "Dotación (Calzado y Vestido de Labor)": {
        "es_salarial": False,
        "descripcion": "Calzado y ropa de trabajo entregados por ley tres veces al año. Nunca constituyen salario.",
        "icono": "👔",
        "referencia": "Art. 128 CST — Numeral 5 (prestación social)"
    },
    "Bonos (Alimentación, Navidad, etc.)": {
        "es_salarial": False,
        "descripcion": "Bonos en especie o electrónicos entregados al trabajador. No constituyen salario cuando están pactados como no salariales.",
        "icono": "🎟️",
        "referencia": "Art. 128 CST — Numeral 10"
    },
    "Propina del Cliente": {
        "es_salarial": False,
        "descripcion": "Propina voluntaria que el cliente deja directamente al trabajador. No la paga el empleador, por tanto no constituye salario.",
        "icono": "🪙",
        "referencia": "Art. 128 CST — Numeral 11"
    },
    "Excedentes de Economía Solidaria": {
        "es_salarial": False,
        "descripcion": "Excedentes distribuidos en cooperativas y empresas de economía solidaria a sus asociados trabajadores.",
        "icono": "🤝",
        "referencia": "Art. 128 CST — Numeral 3"
    },
}
# ══════════════════════════════════════════════════════════════════
# TAB 1: PAGOS
# ══════════════════════════════════════════════════════════════════
with tab1:
    st.subheader("¿Qué pagos recibía mensualmente?")
    st.caption("Selecciona cada tipo de pago. El sistema clasifica automáticamente qué cuenta o no para sus prestaciones, según los Art. 127 y 128 del CST.")

    concepto_sel = st.selectbox(
        "Tipo de pago recibido",
        list(CONCEPTOS_PREDEFINIDOS.keys()),
        format_func=lambda x: f"{CONCEPTOS_PREDEFINIDOS[x]['icono']}  {x}",
        help="Elige la opción que mejor describe el pago que recibías"
    )

    info = CONCEPTOS_PREDEFINIDOS[concepto_sel]

    if info["es_salarial"]:
        st.success(f"🟢 **Cuenta para sus prestaciones** — {info['descripcion']}")
    else:
        st.info(f"🔵 **No afecta sus prestaciones** — {info['descripcion']}")

    col_val, col_btn = st.columns([3, 1])
    with col_val:
        valor_pago = st.number_input(
            "¿Cuánto recibía mensualmente por este concepto? ($)",
            min_value=0.0, value=0.0, step=50_000.0,
            format="%0.0f",
            help="Ingresa el promedio mensual recibido durante el contrato"
        )
    with col_btn:
        st.write("")
        st.write("")
        if st.button("➕ Agregar pago", use_container_width=True):
            if valor_pago > 0:
                st.session_state.pagos_lista.append({
                    "nombre": concepto_sel,
                    "valor": valor_pago,
                    "es_salarial": info["es_salarial"]
                })
                st.success(f"✅ {concepto_sel} agregado correctamente")
                st.rerun()
            else:
                st.warning("⚠️ El valor debe ser mayor a $0")

    if st.session_state.pagos_lista:
        st.markdown("#### 📋 Conceptos registrados")
        df_pagos = pd.DataFrame(st.session_state.pagos_lista)
        df_pagos["Clasificación Legal"] = df_pagos["es_salarial"].apply(
            lambda x: "🟢 Salarial (Art. 127)" if x else "🔵 No Salarial (Art. 128)"
        )
        df_pagos["Valor"] = df_pagos["valor"].apply(lambda x: f"${x:,.0f}")

        total_salarial = sum(p["valor"] for p in st.session_state.pagos_lista if p["es_salarial"])
        total_no_salarial = sum(p["valor"] for p in st.session_state.pagos_lista if not p["es_salarial"])

        st.dataframe(
            df_pagos[["nombre", "Valor", "Clasificación Legal"]].rename(columns={
                "nombre": "Concepto", "Valor": "Monto Mensual"
            }),
            use_container_width=True, hide_index=True
        )

        col_a, col_b = st.columns(2)
        with col_a:
            st.metric("Base Prestacional (Salarial)", f"${total_salarial:,.0f}",
                      help="Esta suma es la que se usa para calcular sus prestaciones")
        with col_b:
            st.metric("Conceptos No Salariales", f"${total_no_salarial:,.0f}",
                      help="Estos pagos NO entran al cálculo de prestaciones")

        if st.button("🗑️ Limpiar todos los pagos"):
            st.session_state.pagos_lista = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 2: SUSPENSIONES
# ══════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("¿Hubo algún período sin trabajar?")
    st.caption("Registra aquí incapacidades, suspensiones o licencias. El sistema aplica automáticamente el Art. 51 y 53 del CST para determinar si afectan sus prestaciones.")

    st.markdown("""
    <div class="alerta-legal">
    ⚠️ <strong>Importante:</strong> No todas las ausencias son iguales ante la ley.
    Las <strong>incapacidades médicas</strong> y <strong>calamidades domésticas</strong> no suspenden el contrato
    y sus prestaciones se calculan normalmente. Las <strong>suspensiones disciplinarias</strong> y
    <strong>licencias no remuneradas</strong> sí descuentan días de cesantías y vacaciones.
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns([4, 1, 1, 1])
    with col1:
        tipo_susp = st.selectbox(
            "Tipo de novedad",
            [
                ("incapacidad",                 "🏥 Incapacidad Médica — NO descuenta prestaciones"),
                ("calamidad_domestica",          "🏠 Calamidad Doméstica — NO descuenta prestaciones"),
                ("suspension_disciplinaria",     "⚠️ Suspensión Disciplinaria — SÍ descuenta"),
                ("licencia_no_remunerada",       "📋 Licencia No Remunerada — SÍ descuenta"),
                ("fuerza_mayor_caso_fortuito",   "🌊 Fuerza Mayor / Caso Fortuito — SÍ descuenta"),
                ("detencion_preventiva",         "🔒 Detención Preventiva — SÍ descuenta"),
                ("huelga_legal",                 "✊ Huelga Legal — SÍ descuenta"),
            ],
            format_func=lambda x: x[1]
        )
    with col2:
        dias_susp = st.number_input("Días", min_value=1, value=5)
    with col3:
        ano_susp = st.number_input("Año", min_value=1950, max_value=2026,
                                   value=fecha_final.year if hasattr(fecha_final, 'year') else 2023)
    with col4:
        mes_susp = st.selectbox("Mes", ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                                         "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"])

    if st.button("➕ Registrar novedad", use_container_width=False):
        st.session_state.suspensiones_lista.append({
            "tipo_id": tipo_susp[0], "tipo_nombre": tipo_susp[1],
            "dias": dias_susp, "ano": ano_susp, "mes": mes_susp
        })
        st.rerun()

    if st.session_state.suspensiones_lista:
        st.markdown("#### 📋 Novedades registradas")
        df_susp = pd.DataFrame(st.session_state.suspensiones_lista)
        df_susp["Impacto Legal"] = df_susp["tipo_id"].apply(
            lambda t: "📉 Descuenta de Cesantías y Vacaciones"
            if t not in ["incapacidad", "calamidad_domestica"]
            else "✅ Mantiene prestaciones intactas"
        )
        st.dataframe(
            df_susp[["tipo_nombre", "dias", "mes", "ano", "Impacto Legal"]].rename(columns={
                "tipo_nombre": "Tipo de Novedad", "dias": "Días",
                "mes": "Mes", "ano": "Año"
            }),
            use_container_width=True, hide_index=True
        )
        if st.button("🗑️ Limpiar todas las novedades"):
            st.session_state.suspensiones_lista = []
            st.rerun()

# ══════════════════════════════════════════════════════════════════
# TAB 3: MOTOR DE LIQUIDACIÓN
# ══════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Calcular Liquidación Completa")
    st.caption("El motor aplica exactamente las fórmulas del Código Sustantivo del Trabajo. Cada cálculo es verificable artículo por artículo.")

    if not st.session_state.pagos_lista:
        st.warning("⚠️ Primero debes agregar los pagos recibidos en la pestaña **💵 Pagos Recibidos**")
    elif fecha_inicio > fecha_final:
        st.error("❌ Las fechas del contrato tienen un error. Revisa la barra lateral.")
    else:
        if st.button("🧮 CALCULAR LIQUIDACIÓN", type="primary", use_container_width=True):
            with st.spinner("Aplicando fórmulas del CST..."):
                # Construir entidades del dominio
                contrato = ContratoLaboral(
                    fecha_inicio=datetime.combine(fecha_inicio, datetime.min.time()),
                    fecha_final=datetime.combine(fecha_final, datetime.min.time()),
                    tipo_contrato=tipo_contrato,
                    regimen_ley_50=es_ley_50
                )
                for p in st.session_state.pagos_lista:
                    contrato.agregar_pago(ConceptoNomina(p["nombre"], p["valor"], p["es_salarial"]))
                for s in st.session_state.suspensiones_lista:
                    contrato.agregar_suspension(SuspensionContrato(s["tipo_id"], s["dias"], s["ano"], s["mes"]))

                engine = CalculadorEngine(
                    smlmv_ano_liquidacion=smlmv_input,
                    aux_transporte_ano_liquidacion=aux_trans_input
                )

                dias_totales  = contrato.calcular_dias_comerciales()
                res_prima     = engine.liquidar_concepto_prestacional(contrato, dias_totales, "prima")
                res_cesantias = engine.liquidar_concepto_prestacional(contrato, dias_totales, "cesantias")
                res_intereses = engine.liquidar_intereses_cesantias(
                    res_cesantias["valor_liquidado"], res_cesantias["dias_netos_calculados"]
                )
                res_vacaciones = engine.liquidar_concepto_prestacional(contrato, dias_totales, "vacaciones")

                total = (res_prima["valor_liquidado"] + res_cesantias["valor_liquidado"] +
                         res_intereses["valor_liquidado"] + res_vacaciones["valor_liquidado"])

            # ── Resumen del contrato ───────────────────────────────
            st.markdown("#### 📄 Resumen del Contrato")
            st.code(str(contrato), language=None)

            # ── Métricas rápidas ───────────────────────────────────
            st.markdown("#### 📊 Métricas del Cálculo")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("Base Salarial", f"${contrato.obtener_base_salarial():,.0f}")
            with c2:
                st.metric("Días Brutos", f"{dias_totales} días")
            with c3:
                susp_total = sum(s["dias"] for s in st.session_state.suspensiones_lista
                                 if s["tipo_id"] not in ["incapacidad", "calamidad_domestica"])
                st.metric("Días Suspensión", f"{susp_total} días")
            with c4:
                aux_aplicado = contrato.obtener_subsidio_transporte_aplicable(aux_trans_input, smlmv_input)
                st.metric("Aux. Transporte", f"${aux_aplicado:,.0f}",
                          help="$0 si el salario supera 2 SMLMV")

            # ── Total destacado ────────────────────────────────────
            st.markdown(f"""
            <div class="resultado-total">
                <div class="label">TOTAL PRESTACIONES SOCIALES A PAGAR</div>
                <div class="valor">${total:,.2f}</div>
                <div class="sub">Prima + Cesantías + Intereses + Vacaciones · Calculado según CST Colombia</div>
            </div>
            """, unsafe_allow_html=True)

            # ── Desglose por concepto ──────────────────────────────
            st.markdown("#### 📋 Desglose por Concepto")

            conceptos_info = [
                ("🏦 Prima de Servicios", res_prima,     "Art. 306 CST — Se paga en junio y diciembre. La suspensión NO la afecta."),
                ("💼 Cesantías",          res_cesantias, "Art. 249 CST — Auxilio para cuando el trabajador quede sin empleo."),
                ("📈 Intereses Cesantías",res_intereses, "Art. 99 Ley 50/1990 — El 12% anual sobre las cesantías acumuladas."),
                ("🌴 Vacaciones",         res_vacaciones,"Art. 186 CST — 15 días hábiles de descanso por año trabajado."),
            ]

            for titulo, res, explicacion in conceptos_info:
                with st.expander(f"{titulo}  →  **${res['valor_liquidado']:,.2f}**"):
                    st.caption(explicacion)
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.write(f"**Base de cálculo:**")
                        if "base_calculo_total" in res:
                            st.write(f"- Salario base: `${res['base_salarial_estricta']:,.2f}`")
                            st.write(f"- Auxilio transporte incluido: `${res['auxilio_transporte_incluido']:,.2f}`")
                            st.write(f"- **Total base:** `${res['base_calculo_total']:,.2f}`")
                        else:
                            st.write(f"- Cesantías acumuladas: `${res['base_cesantias']:,.2f}`")
                            st.write(f"- Tasa legal aplicada: `{res['tasa_legal']}`")
                    with col_b:
                        st.write(f"**Días liquidados:**")
                        if "dias_solicitados" in res:
                            st.write(f"- Días brutos del contrato: `{res['dias_solicitados']}`")
                            st.write(f"- Días descontados por suspensión: `{res['dias_descontados_suspension']}`")
                            st.write(f"- **Días netos:** `{res['dias_netos_calculados']}`")
                        else:
                            st.write(f"- Días netos de cesantías: `{res['dias_netos_cesantias']}`")

            # ── Tabla exportable ───────────────────────────────────
            st.markdown("#### 📥 Tabla Resumen (exportable)")
            df_resultado = pd.DataFrame([
                {"Concepto": "Prima de Servicios",    "Valor": res_prima["valor_liquidado"]},
                {"Concepto": "Cesantías",             "Valor": res_cesantias["valor_liquidado"]},
                {"Concepto": "Intereses Cesantías",   "Valor": res_intereses["valor_liquidado"]},
                {"Concepto": "Vacaciones",            "Valor": res_vacaciones["valor_liquidado"]},
                {"Concepto": "TOTAL",                 "Valor": total},
            ])
            df_resultado["Valor Formateado"] = df_resultado["Valor"].apply(lambda x: f"${x:,.2f}")
            st.dataframe(df_resultado[["Concepto", "Valor Formateado"]], use_container_width=True, hide_index=True)

            st.markdown("""
            <div class="alerta-legal">
            ⚠️ <strong>Aviso legal:</strong> Esta herramienta es una calculadora de orientación basada en el CST.
            Los resultados no constituyen asesoría jurídica formal. Para casos con conflictos, demandas o dudas
            sobre la liquidación, consulte a un abogado laboralista o al Ministerio de Trabajo de Colombia.
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════
# TAB 4: GUÍA DE USUARIO
# ══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("## 📘 Guía de Usuario — Paso a Paso")
    st.markdown("*¿Es la primera vez que usas esta herramienta? Esta guía está escrita para ti, sin tecnicismos.*")

    # ── ¿Qué son las prestaciones? ────────────────────────────────
    st.markdown("---")
    st.markdown("### ¿Qué son las prestaciones sociales?")
    st.markdown("""
    Las **prestaciones sociales** son pagos adicionales al salario que la ley colombiana le garantiza
    a todo trabajador al terminar su contrato. Son un derecho, no un favor del empleador.

    Si trabajaste en Colombia bajo contrato laboral, tienes derecho a recibir:
    """)

    col1, col2, col3, col4 = st.columns(4)
    prestaciones_info = [
        ("🏦", "Prima de Servicios", "Un mes de salario al año, pagado en dos cuotas (junio y diciembre).", "Art. 306 CST"),
        ("💼", "Cesantías", "Un ahorro obligatorio de un mes de salario por año, para cuando te quedes sin empleo.", "Art. 249 CST"),
        ("📈", "Intereses s/ Cesantías", "El 12% anual sobre las cesantías acumuladas. El empleador paga esto directamente.", "Art. 99 Ley 50"),
        ("🌴", "Vacaciones", "15 días hábiles de descanso remunerado por cada año trabajado.", "Art. 186 CST"),
    ]
    for col, (icono, nombre, desc, articulo) in zip([col1,col2,col3,col4], prestaciones_info):
        with col:
            st.markdown(f"""
            <div class="guia-card">
                <h4>{icono} {nombre}</h4>
                <p>{desc}</p>
                <p><small style="color:#00C9A7">{articulo}</small></p>
            </div>
            """, unsafe_allow_html=True)

    # ── Cómo usar la app ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 🚀 Cómo usar esta calculadora en 4 pasos")

    pasos = [
        ("1", "Ingresa los datos del contrato en el menú lateral izquierdo",
         "Necesitas: tipo de contrato (indefinido, fijo o por obra), la fecha en que empezaste a trabajar y la fecha en que terminaste o vas a terminar."),
        ("2", "Agrega los pagos que recibías en la pestaña 💵 Pagos Recibidos",
         "Selecciona cada tipo de pago de la lista desplegable e ingresa el valor mensual. No te preocupes por clasificarlos: el sistema determina automáticamente cuáles cuentan para tus prestaciones según la ley."),
        ("3", "Registra incapacidades o suspensiones en la pestaña 📉 Suspensiones (si aplica)",
         "Si no tuviste ninguna ausencia, omite este paso. Si tuviste incapacidades médicas o calamidades, regístralas — estas NO te afectan las prestaciones. Las suspensiones disciplinarias y licencias no remuneradas sí pueden afectarlas."),
        ("4", "Haz clic en 'Calcular Liquidación' en la pestaña 🧮",
         "El sistema calcula automáticamente prima, cesantías, intereses y vacaciones. Verás el desglose matemático completo, artículo por artículo del CST."),
    ]

    for num, titulo, desc in pasos:
        st.markdown(f"""
        <div class="paso">
            <div class="paso-num">{num}</div>
            <div class="paso-texto">
                <h5>{titulo}</h5>
                <p>{desc}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Preguntas frecuentes ──────────────────────────────────────
    st.markdown("---")
    st.markdown("### ❓ Preguntas Frecuentes")

    faqs = [
        ("¿Qué es el SMLMV?",
         "El Salario Mínimo Legal Mensual Vigente. En 2023 fue $1.160.000. Este valor es importante porque si tu salario es menor o igual a 2 SMLMV, el empleador debe incluir el auxilio de transporte en el cálculo de tus cesantías y prima. La aplicación lo detecta automáticamente."),

        ("¿Por qué algunos pagos 'no cuentan' para las prestaciones?",
         "La ley colombiana permite que ciertos beneficios (como auxilios de alimentación, rodamiento o bonos ocasionales) sean pactados como 'no salariales' mediante acuerdo escrito. Esto significa que no se incluyen en la base de cálculo de tus prestaciones. Si tienes dudas sobre si un pago tuyo es o no salarial, revisa tu contrato o consúltalo con un abogado."),

        ("¿Una incapacidad me quita días de mis prestaciones?",
         "No. Las incapacidades médicas y calamidades domésticas NO suspenden el contrato laboral. Tu tiempo de servicio cuenta normalmente y tus prestaciones no se ven afectadas. Solo las suspensiones disciplinarias, licencias no remuneradas y ciertos eventos de fuerza mayor pueden descontar días."),

        ("¿Esta herramienta reemplaza a un abogado?",
         "No. LiquidaYA es una calculadora de orientación basada en las fórmulas exactas del CST. Es útil para que conozcas aproximadamente cuánto deberías recibir y puedas verificar si tu liquidación es correcta. Pero si hay un conflicto con tu empleador o dudas específicas sobre tu caso, siempre consulta a un abogado laboralista o al Ministerio de Trabajo (línea gratuita 01 8000 112018)."),

        ("¿Qué pasa si trabajé menos de un año?",
         "No hay problema. La calculadora maneja contratos de cualquier duración. Si trabajaste 3 meses, recibirás una parte proporcional de cada prestación. Por ejemplo, si trabajaste 180 días (6 meses), recibirás la mitad de lo que corresponde a un año completo."),

        ("¿Cómo sé qué valores de SMLMV y Auxilio de Transporte usar?",
         "Usa los valores del año en que termina tu contrato. La aplicación los carga automáticamente según la fecha final que ingreses. Si tu contrato termina en 2023, usará los valores de 2023 ($1.160.000 SMLMV y $140.606 de auxilio de transporte)."),
    ]

    for pregunta, respuesta in faqs:
        with st.expander(f"❓ {pregunta}"):
            st.write(respuesta)

    # ── Ejemplo práctico ──────────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📝 Ejemplo Práctico Resuelto")
    st.markdown("*Para que entiendas cómo funciona, aquí un caso real:*")

    with st.expander("📋 Ver ejemplo: María trabajó 1 año con salario mínimo", expanded=True):
        col_ej1, col_ej2 = st.columns(2)
        with col_ej1:
            st.markdown("""
            **Datos del contrato de María:**
            - Tipo: Término indefinido
            - Salario: $1.160.000 (salario mínimo 2023)
            - Período: 01/enero/2023 al 31/diciembre/2023
            - Sin suspensiones ni incapacidades
            """)
        with col_ej2:
            st.markdown("""
            **Lo que el sistema calcula:**
            - Base prestacional: 1.160.000 + 140.606 aux. transporte = **1.300.606**
            - Días trabajados: **360 días comerciales**
            - Prima: 1.300.606 × 360 / 360 = **1.300.606**
            - Cesantías: 1.300.606 × 360 / 360 = **1.300.606**
            - Intereses: 1.300.606 × 360 × 12% / 360 = **156.073**
            - Vacaciones: 1.160.000 × 360 / 720 = **580.000**
            - **TOTAL: $3.337.285**
            """)

    # ── Recursos y contacto ───────────────────────────────────────
    st.markdown("---")
    st.markdown("### 📞 ¿Necesitas más ayuda?")

    col_r1, col_r2, col_r3 = st.columns(3)
    recursos = [
        ("🏛️", "Ministerio de Trabajo", "Línea gratuita: **01 8000 112518**\nAsesoría laboral oficial y gratuita para trabajadores colombianos."),
        ("⚖️", "Inspección de Trabajo", "Puedes presentar quejas ante la Inspección de Trabajo de tu municipio si consideras que tu liquidación fue incorrecta."),
        ("📱", "Código Sustantivo del Trabajo", "Consulta el CST completo en:\nwww.suin-juriscol.gov.co/viewDocument.asp?ruta=Codigo/30019323\nEs público y gratuito."),
    ]
    for col, (icono, titulo, desc) in zip([col_r1, col_r2, col_r3], recursos):
        with col:
            st.markdown(f"""
            <div class="guia-card">
                <h4>{icono} {titulo}</h4>
                <p>{desc}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")
    st.markdown("""
    <div class="alerta-legal">
    ⚠️ <strong>Aviso legal:</strong> LiquidaYA es una herramienta educativa y de orientación.
    Los resultados son aproximados y no constituyen asesoría jurídica. Los cálculos se basan en
    las fórmulas del CST vigente para contratos privados en Colombia. No aplica para servidores
    públicos, trabajadores domésticos con régimen especial ni contratos de aprendizaje SENA.
    Ante cualquier duda, consulte a un abogado laboralista certificado.
    </div>
    """, unsafe_allow_html=True)