import ast
import math
import operator
import statistics

import numpy as np
import streamlit as st


# ============================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================

st.set_page_config(
    page_title="Calculadora Científica Avanzada",
    page_icon="🧮",
    layout="wide",
)

st.title("🧮 Calculadora Científica Avanzada")
st.caption(
    "Calculadora matemática, estadística, regresión lineal "
    "y resolución de ecuaciones en una aplicación web."
)


# ============================================================
# FUNCIONES DE CÁLCULO
# ============================================================

def evaluar_expresion(expresion: str, grados: bool, ans):
    """Evalúa expresiones matemáticas mediante una lista segura de operaciones."""
    expresion = expresion.replace("^", "**").strip()

    if not expresion:
        raise ValueError("Introduce una expresión matemática.")
    if len(expresion) > 500:
        raise ValueError("La expresión es demasiado larga.")

    def seno(x):
        return math.sin(math.radians(x) if grados else x)

    def coseno(x):
        return math.cos(math.radians(x) if grados else x)

    def tangente(x):
        return math.tan(math.radians(x) if grados else x)

    def arcoseno(x):
        resultado = math.asin(x)
        return math.degrees(resultado) if grados else resultado

    def arcocoseno(x):
        resultado = math.acos(x)
        return math.degrees(resultado) if grados else resultado

    def arcotangente(x):
        resultado = math.atan(x)
        return math.degrees(resultado) if grados else resultado

    def raiz(x):
        if x < 0:
            raise ValueError("La raíz cuadrada requiere un valor x ≥ 0.")
        return math.sqrt(x)

    funciones = {
        "sin": seno,
        "cos": coseno,
        "tan": tangente,
        "asin": arcoseno,
        "acos": arcocoseno,
        "atan": arcotangente,
        "sinh": math.sinh,
        "cosh": math.cosh,
        "tanh": math.tanh,
        "sqrt": raiz,
        "log": lambda x, base=10: math.log(x, base),
        "log10": math.log10,
        "log2": math.log2,
        "ln": math.log,
        "exp": math.exp,
        "abs": abs,
        "factorial": math.factorial,
        "comb": math.comb,
        "perm": math.perm,
        "floor": math.floor,
        "ceil": math.ceil,
        "round": round,
        "degrees": math.degrees,
        "radians": math.radians,
    }

    constantes = {
        "pi": math.pi,
        "e": math.e,
        "Ans": ans,
    }

    operaciones = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
    }
    unarias = {ast.UAdd: operator.pos, ast.USub: operator.neg}

    arbol = ast.parse(expresion, mode="eval")

    def resolver(nodo):
        if isinstance(nodo, ast.Expression):
            return resolver(nodo.body)

        if isinstance(nodo, ast.Constant):
            if isinstance(nodo.value, (int, float)) and not isinstance(nodo.value, bool):
                return nodo.value
            raise ValueError("Solo se permiten valores numéricos.")

        if isinstance(nodo, ast.Name):
            if nodo.id in constantes:
                return constantes[nodo.id]
            raise ValueError(f"Nombre desconocido: {nodo.id}")

        if isinstance(nodo, ast.BinOp):
            tipo = type(nodo.op)
            if tipo not in operaciones:
                raise ValueError("Operación no permitida.")
            izquierda = resolver(nodo.left)
            derecha = resolver(nodo.right)
            if tipo == ast.Pow and abs(derecha) > 1000:
                raise ValueError("El exponente es demasiado grande.")
            return operaciones[tipo](izquierda, derecha)

        if isinstance(nodo, ast.UnaryOp):
            tipo = type(nodo.op)
            if tipo not in unarias:
                raise ValueError("Operación no permitida.")
            return unarias[tipo](resolver(nodo.operand))

        if isinstance(nodo, ast.Call):
            if not isinstance(nodo.func, ast.Name):
                raise ValueError("Tipo de llamada no permitido.")
            nombre = nodo.func.id
            if nombre not in funciones:
                raise ValueError(f"Función desconocida: {nombre}")
            if nodo.keywords:
                raise ValueError("No se permiten argumentos con nombre.")
            return funciones[nombre](*[resolver(arg) for arg in nodo.args])

        raise ValueError("La expresión contiene elementos no permitidos.")

    resultado = resolver(arbol)

    if isinstance(resultado, complex):
        if abs(resultado.imag) < 1e-12:
            resultado = resultado.real
        else:
            raise ValueError("El resultado es complejo y esta calculadora muestra resultados reales.")

    if not isinstance(resultado, (int, float)) or not math.isfinite(float(resultado)):
        raise ValueError("El resultado no es un número real finito.")

    return resultado


def leer_datos(texto: str):
    texto = texto.replace(",", " ").replace(";", " ")
    datos = [float(elemento) for elemento in texto.split()]
    if not datos:
        raise ValueError("Introduce al menos un dato.")
    if not all(math.isfinite(x) for x in datos):
        raise ValueError("Todos los datos deben ser números finitos.")
    return datos


def formato_numero(valor):
    if isinstance(valor, (int, np.integer)):
        return str(valor)
    if isinstance(valor, (float, np.floating)):
        return f"{valor:.10g}"
    return str(valor)


# ============================================================
# ESTADO DE SESIÓN
# ============================================================

if "ans" not in st.session_state:
    st.session_state.ans = 0
if "historial" not in st.session_state:
    st.session_state.historial = []


# ============================================================
# NAVEGACIÓN WEB
# ============================================================

pestanas = st.tabs([
    "🧮 Calculadora científica",
    "📊 Estadística",
    "📈 Regresión lineal",
    "🟰 Ecuaciones",
])


# ============================================================
# PESTAÑA 1: CALCULADORA CIENTÍFICA
# ============================================================

with pestanas[0]:
    st.subheader("Operaciones científicas")

    izquierda, derecha = st.columns([2, 1])

    with izquierda:
        grados = st.radio(
            "Unidad angular para funciones trigonométricas",
            ["Grados", "Radianes"],
            horizontal=True,
            key="unidad_angular",
        )
        expresion = st.text_input(
            "Escribe la expresión",
            value="sin(30) + sqrt(16)",
            placeholder="Ej.: sin(30) + log10(100)",
            help="Usa ** para potencias o ^ como atajo. Ejemplos: 2**8, ln(e), comb(10,3).",
            key="expresion_calculadora",
        )

        c1, c2, c3, c4 = st.columns(4)
        ejemplos = {
            "π": "pi",
            "e": "e",
            "Potencia": "2**8",
            "Raíz": "sqrt(144)",
            "Seno": "sin(30)",
            "Log10": "log10(1000)",
            "Factorial": "factorial(5)",
            "Combinación": "comb(10,3)",
        }
        for col, (etiqueta, ejemplo) in zip(
            [c1, c2, c3, c4, c1, c2, c3, c4], ejemplos.items()
        ):
            with col:
                if st.button(etiqueta, key=f"ejemplo_{etiqueta}", use_container_width=True):
                    st.session_state["expresion_calculadora"] = ejemplo
                    st.rerun()

        if st.button("Calcular", type="primary", use_container_width=True):
            try:
                resultado = evaluar_expresion(
                    expresion,
                    grados=(grados == "Grados"),
                    ans=st.session_state.ans,
                )
                st.session_state.ans = resultado
                st.session_state.historial.insert(
                    0, (expresion, resultado)
                )
                st.success(f"Resultado: {formato_numero(resultado)}")
            except Exception as error:
                st.error(f"No se pudo calcular: {error}")

    with derecha:
        st.markdown("**Funciones disponibles**")
        st.code(
            "sin(x), cos(x), tan(x)\n"
            "asin(x), acos(x), atan(x)\n"
            "sinh(x), cosh(x), tanh(x)\n"
            "sqrt(x), abs(x), exp(x)\n"
            "ln(x), log(x), log10(x), log2(x)\n"
            "factorial(n), comb(n,k), perm(n,k)\n"
            "floor(x), ceil(x), round(x)\n"
            "pi, e, Ans, ^ o **",
            language="text",
        )
        st.caption("log(x) usa base 10 por defecto; log(x, base) permite otra base.")

    st.markdown("### Historial de cálculos")
    if st.session_state.historial:
        if st.button("Borrar historial"):
            st.session_state.historial = []
            st.rerun()
        st.dataframe(
            [
                {"Expresión": expresion_ant, "Resultado": formato_numero(resultado_ant)}
                for expresion_ant, resultado_ant in st.session_state.historial
            ],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Tus cálculos aparecerán aquí después de pulsar «Calcular».")


# ============================================================
# PESTAÑA 2: ESTADÍSTICA DESCRIPTIVA
# ============================================================

with pestanas[1]:
    st.subheader("Estadística descriptiva")
    st.write("Introduce los datos separados por comas, espacios o saltos de línea.")

    datos_texto = st.text_area(
        "Conjunto de datos",
        value="10, 12, 15, 18, 20, 22, 25",
        height=110,
        key="datos_estadisticos",
    )

    if st.button("Calcular estadísticas", type="primary", key="boton_estadistica"):
        try:
            datos = leer_datos(datos_texto)
            n = len(datos)
            arreglo = np.array(datos, dtype=float)
            q1, q2, q3 = np.percentile(arreglo, [25, 50, 75])

            metricas = st.columns(4)
            metricas[0].metric("Cantidad", n)
            metricas[1].metric("Media", formato_numero(statistics.mean(datos)))
            metricas[2].metric("Mediana", formato_numero(statistics.median(datos)))
            metricas[3].metric("Rango", formato_numero(max(datos) - min(datos)))

            moda = statistics.multimode(datos)
            resultados = [
                ("Suma", sum(datos)),
                ("Mínimo", min(datos)),
                ("Máximo", max(datos)),
                ("Moda(s)", ", ".join(formato_numero(x) for x in moda)),
                ("Q1 / Percentil 25", q1),
                ("Q2 / Percentil 50", q2),
                ("Q3 / Percentil 75", q3),
                ("Percentil 90", np.percentile(arreglo, 90)),
                ("Varianza poblacional", statistics.pvariance(datos)),
                ("Desviación estándar poblacional", statistics.pstdev(datos)),
            ]

            if n >= 2:
                resultados.extend([
                    ("Varianza muestral", statistics.variance(datos)),
                    ("Desviación estándar muestral", statistics.stdev(datos)),
                ])

            st.markdown("#### Resultados detallados")
            st.dataframe(
                [{"Medida": nombre, "Valor": formato_numero(valor)}
                 for nombre, valor in resultados],
                use_container_width=True,
                hide_index=True,
            )

            st.markdown("#### Visualización de los datos")
            st.bar_chart(
                [{"Índice": i + 1, "Valor": valor} for i, valor in enumerate(datos)],
                x="Índice",
                y="Valor",
            )

        except Exception as error:
            st.error(f"No se pudieron calcular las estadísticas: {error}")


# ============================================================
# PESTAÑA 3: REGRESIÓN LINEAL
# ============================================================

with pestanas[2]:
    st.subheader("Regresión lineal y correlación")
    col_x, col_y = st.columns(2)

    with col_x:
        x_texto = st.text_area(
            "Valores X",
            value="1, 2, 3, 4, 5",
            height=100,
            key="regresion_x",
        )
    with col_y:
        y_texto = st.text_area(
            "Valores Y",
            value="2, 4, 5, 4, 6",
            height=100,
            key="regresion_y",
        )

    if st.button("Calcular regresión", type="primary"):
        try:
            x = np.array(leer_datos(x_texto), dtype=float)
            y = np.array(leer_datos(y_texto), dtype=float)

            if len(x) != len(y):
                raise ValueError("X e Y deben tener la misma cantidad de datos.")
            if len(x) < 2:
                raise ValueError("Se necesitan al menos dos pares de datos.")
            if np.all(x == x[0]):
                raise ValueError("Los valores X no pueden ser todos iguales.")
            if np.all(y == y[0]):
                raise ValueError("Los valores Y no pueden ser todos iguales para calcular r y R².")

            pendiente, intercepto = np.polyfit(x, y, 1)
            predicciones = pendiente * x + intercepto
            residuos = np.sum((y - predicciones) ** 2)
            total = np.sum((y - np.mean(y)) ** 2)
            r2 = 1 - residuos / total
            correlacion = np.corrcoef(x, y)[0, 1]
        except SyntaxError:
            st.error("Revisa los datos ingresados.")
        except Exception as error:
            st.error(f"No se pudo calcular la regresión: {error}")
        else:
            st.markdown("#### Resultados")
            m1, m2, m3 = st.columns(3)
            m1.metric("Pendiente", formato_numero(pendiente))
            m2.metric("Intercepto", formato_numero(intercepto))
            m3.metric("Correlación r", formato_numero(correlacion))

            st.latex(
                rf"\hat{{y}} = {pendiente:.6g}x + ({intercepto:.6g})"
            )
            st.write(f"**Coeficiente de determinación R²:** {r2:.6g}")
            st.write(
                f"**Error cuadrático medio (ECM):** "
                f"{np.mean((y - predicciones) ** 2):.6g}"
            )

            st.markdown("#### Datos y recta estimada")
            orden = np.argsort(x)
            tabla = {
                "X": x,
                "Y observado": y,
                "Y estimado": predicciones,
            }
            st.dataframe(tabla, use_container_width=True, hide_index=True)

            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.scatter(x, y, label="Datos observados")
            ax.plot(x[orden], predicciones[orden], label="Regresión lineal")
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.grid(True, alpha=0.3)
            ax.legend()
            st.pyplot(fig)
            plt.close(fig)


# ============================================================
# PESTAÑA 4: ECUACIONES
# ============================================================

with pestanas[3]:
    st.subheader("Resolución de ecuaciones")
    st.write("Resuelve una ecuación de la forma **ax² + bx + c = 0**.")

    col_a, col_b, col_c = st.columns(3)
    with col_a:
        a = st.number_input("Coeficiente a", value=1.0, key="coef_a")
    with col_b:
        b = st.number_input("Coeficiente b", value=-5.0, key="coef_b")
    with col_c:
        c = st.number_input("Coeficiente c", value=6.0, key="coef_c")

    if st.button("Resolver ecuación", type="primary"):
        if a == 0:
            if b == 0:
                if c == 0:
                    st.success("La igualdad se cumple para todo valor de x.")
                else:
                    st.error("No existe solución.")
            else:
                st.success(f"Es una ecuación lineal. Solución: x = {-c / b:.10g}")
        else:
            discriminante = b**2 - 4*a*c
            st.write(f"**Discriminante:** {discriminante:.10g}")

            if discriminante > 0:
                x1 = (-b + math.sqrt(discriminante)) / (2*a)
                x2 = (-b - math.sqrt(discriminante)) / (2*a)
                st.success("La ecuación tiene dos soluciones reales.")
                st.write(f"**x₁ =** {x1:.10g}")
                st.write(f"**x₂ =** {x2:.10g}")
            elif discriminante == 0:
                x = -b / (2*a)
                st.success("La ecuación tiene una solución real doble.")
                st.write(f"**x =** {x:.10g}")
            else:
                parte_real = -b / (2*a)
                parte_imaginaria = math.sqrt(-discriminante) / abs(2*a)
                st.info("La ecuación tiene dos soluciones complejas.")
                st.write(f"**x₁ =** {parte_real:.6g} + {parte_imaginaria:.6g}i")
                st.write(f"**x₂ =** {parte_real:.6g} - {parte_imaginaria:.6g}i")


st.divider()
st.caption("Calculadora Científica Avanzada · Python + Streamlit")
