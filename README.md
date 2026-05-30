# LegalTech: Automating Labor Liquidations (CST Colombia)

Este proyecto es una plataforma web reactiva e interactiva desarrollada en **Python** con **Streamlit** que automatiza la liquidación avanzada de prestaciones sociales en el ordenamiento jurídico laboral colombiano, dando cumplimiento estricto a las disposiciones del **Código Sustantivo del Trabajo (CST)**.

El sistema fue diseñado bajo principios rigurosos de **Ingeniería de Software**, utilizando **Programación Orientada a Objetos (POO)** y asegurando un desacoplamiento completo entre la interfaz gráfica y las reglas del dominio legal (Backend).

## 🚀 Características y Cobertura Legal

- **Filtro de la Base Salarial (Art. 127 y 128 CST):** Discriminación automatizada de los ingresos del trabajador para aislar conceptos constitutivos de salario (salario fijo, horas extras) de aquellos excluidos por acuerdos de desalarización o naturaleza indemnizatoria.
- **Análisis Asimétrico de Novedades (Art. 51 y 53 CST):** Motor inteligente que calcula las suspensiones del contrato restando los días correspondientes para los rubros de Cesantías y Vacaciones, manteniendo intactos los derechos de Prima de Servicios conforme a la jurisprudencia de la Corte Suprema de Justicia.
- **Algoritmo de Tiempo Comercial:** Cálculo automático de términos basado en el año comercial de 360 días colombianos (meses fijos de 30 días).
- **Cálculo de Variables Auxiliares:** Evaluación en tiempo real para determinar la inclusión o exclusión legal del Auxilio de Transporte en la base prestacional (Tope de 2 SMLMV).

## 🛠️ Arquitectura del Sistema

El software sigue una arquitectura desacoplada y limpia para evitar el código espagueti y blindar la precisión matemática contra fallos en la interfaz:

```text
legaltech-liquidador/
│
├── app.py                 # Capa de Presentación (Interfaz Streamlit UI)
├── requirements.txt       # Gestión de dependencias del entorno
├── README.md              # Documentación técnica y jurídica del sistema
│
├── src/                   # Código Fuente del Backend (Capa del Dominio)
│   ├── models/            # Entidades y Modelos de Datos (POO)
│   │   ├── contrato.py    # Clase ContratoLaboral (Gestor del Ciclo de Vida del Empleado)
│   │   ├── suspension.py  # Clase SuspensionContrato (Control de Ley del Art. 53)
│   │   └── pago.py        # Clase ConceptoNomina (Estructura de Ingresos)
│   │
│   └── engine/            # Capa de Servicios / Motor Algorítmico
│       └── calculador.py  # CalculadorEngine (Fórmulas matemáticas puras del CST)

```

## 💻 Requisitos e Instalación

Para desplegar y ejecutar el entorno localmente, clone el repositorio e instale las dependencias aisladas:

1. **Clonar el proyecto:**
```bash
git clone [https://github.com/tu-usuario/legaltech-liquidador-laboral.git](https://github.com/tu-usuario/legaltech-liquidador-laboral.git)
cd legaltech-liquidador-laboral

```


2. **Crear y activar el entorno virtual:**
```bash
# En Linux / MacOS
python -m venv venv
source venv/bin/activate

# En Windows
python -m venv venv
.\venv\Scripts\activate

```


3. **Instalar dependencias:**
```bash
pip install -r requirements.txt

```


4. **Ejecutar la aplicación web:**
```bash
streamlit run app.py

```



## 🧪 Estrategia de Calidad y Pruebas (QA)

El motor lógico se encuentra protegido bajo **Programación Defensiva**. Para validar que las matemáticas del sistema no se rompan ante cambios visuales y que respondan adecuadamente a casos de examen complejos (como contratos extensos y múltiples suspensiones cruzadas), se implementan pruebas automatizadas utilizando `pytest`.

Para correr la suite de pruebas locales ejecute:

```bash
pip install pytest
pytest

```

---
