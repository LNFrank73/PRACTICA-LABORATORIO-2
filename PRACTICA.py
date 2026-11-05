
import streamlit as st
import pandas as pd
import os
from datetime import date
from supabase import create_client

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================

st.set_page_config(
    page_title="Sistema de Producción",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 SISTEMA DE CONTROL DE PRODUCCIÓN")
st.caption("Gestión de registros mediante Supabase")

# Credenciales de Supabase
try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except Exception:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("Configura las credenciales de Supabase.")
    st.stop()

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

TABLA = "PRACTICA"


# ==========================================
# 2. FUNCIONES
# ==========================================

def consultar_registros():
    respuesta = (
        supabase.table(TABLA)
        .select("*")
        .order("id", desc=True)
        .execute()
    )
    return respuesta.data or []


def validar_datos(datos):
    requeridos = [
        "MAQUINA", "TURNO", "PRODUCTO", "OPERADOR"
    ]

    for campo in requeridos:
        if not datos[campo].strip():
            return f"El campo {campo} es obligatorio."

    if datos["CANTIDAD_DEFECTUOSA"] > datos["CANTIDAD_PRODUCIDA"]:
        return "La cantidad defectuosa no puede superar la producida."

    return None


def preparar_datos(
    fecha, maquina, turno, producto, operador,
    programada, producida, defectuosa,
    tiempo_programado, tiempo_parada, causa
):
    return {
        "FECHA": fecha.isoformat(),
        "MAQUINA": maquina.strip(),
        "TURNO": turno.strip(),
        "PRODUCTO": producto.strip(),
        "OPERADOR": operador.strip(),
        "CANTIDAD_PROGRAMADA": int(programada),
        "CANTIDAD_PRODUCIDA": int(producida),
        "CANTIDAD_DEFECTUOSA": int(defectuosa),
        "TIEMPO_PROGRAMADO": int(tiempo_programado),
        "TIEMPO_PARADA": int(tiempo_parada),
        "CAUSA_PARADA": causa.strip() or None
    }


def formulario_registro(datos=None, clave="formulario"):
    datos = datos or {}

    def valor(campo):
        return datos.get(campo) or ""

    def numero(campo):
        try:
            return max(0, min(32767, int(datos.get(campo) or 0)))
        except (ValueError, TypeError):
            return 0

    try:
        fecha_inicial = (
            date.fromisoformat(str(datos["FECHA"])[:10])
            if datos.get("FECHA") else date.today()
        )
    except ValueError:
        fecha_inicial = date.today()

    with st.form(clave):

        st.subheader("Datos generales")

        col1, col2, col3 = st.columns(3)

        with col1:
            fecha = st.date_input("Fecha", value=fecha_inicial)
            maquina = st.text_input("Máquina", value=valor("MAQUINA"))
            turno = st.text_input("Turno", value=valor("TURNO"))

        with col2:
            producto = st.text_input("Producto", value=valor("PRODUCTO"))
            operador = st.text_input("Operador", value=valor("OPERADOR"))
            programada = st.number_input(
                "Cantidad programada",
                min_value=0, max_value=32767,
                value=numero("CANTIDAD_PROGRAMADA")
            )

        with col3:
            producida = st.number_input(
                "Cantidad producida",
                min_value=0, max_value=32767,
                value=numero("CANTIDAD_PRODUCIDA")
            )
            defectuosa = st.number_input(
                "Cantidad defectuosa",
                min_value=0, max_value=32767,
                value=numero("CANTIDAD_DEFECTUOSA")
            )
            tiempo_programado = st.number_input(
                "Tiempo programado",
                min_value=0, max_value=32767,
                value=numero("TIEMPO_PROGRAMADO")
            )

        tiempo_parada = st.number_input(
            "Tiempo de parada",
            min_value=0, max_value=32767,
            value=numero("TIEMPO_PARADA")
        )

        causa = st.text_input(
            "Causa de parada",
            value=valor("CAUSA_PARADA")
        )

        guardar = st.form_submit_button(
            "Guardar registro",
            type="primary",
            use_container_width=True
        )

    return (
        guardar, fecha, maquina, turno, producto, operador,
        programada, producida, defectuosa,
        tiempo_programado, tiempo_parada, causa
    )


# ==========================================
# 3. MENÚ CRUD
# ==========================================

tab1, tab2, tab3, tab4 = st.tabs([
    "📋 CONSULTAR",
    "➕ REGISTRAR",
    "✏️ ACTUALIZAR",
    "🗑️ ELIMINAR"
])


# ==========================================
# 4. READ - CONSULTAR
# ==========================================

with tab1:

    st.subheader("Registros de producción")

    busqueda = st.text_input(
        "Buscar por máquina, turno, producto u operador"
    )

    if st.button("Actualizar tabla"):
        st.rerun()

    try:
        registros = consultar_registros()

        if busqueda.strip():
            termino = busqueda.lower().strip()

            campos = [
                "MAQUINA", "TURNO", "PRODUCTO",
                "OPERADOR", "CAUSA_PARADA"
            ]

            registros = [
                r for r in registros
                if any(
                    termino in str(r.get(campo) or "").lower()
                    for campo in campos
                )
            ]

        st.metric("Total de registros", len(registros))

        if registros:
            df = pd.DataFrame(registros)
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.download_button(
                "Descargar registros CSV",
                data=df.to_csv(index=False).encode("utf-8-sig"),
                file_name="produccion.csv",
                mime="text/csv"
            )
        else:
            st.info("No existen registros.")

    except Exception as e:
        st.error(f"Error al consultar: {e}")


# ==========================================
# 5. CREATE - REGISTRAR
# ==========================================

with tab2:

    st.subheader("Registrar nueva producción")

    resultado = formulario_registro(clave="crear_registro")

    (
        guardar, fecha, maquina, turno, producto, operador,
        programada, producida, defectuosa,
        tiempo_programado, tiempo_parada, causa
    ) = resultado

    if guardar:

        datos = {
            "MAQUINA": maquina,
            "TURNO": turno,
            "PRODUCTO": producto,
            "OPERADOR": operador,
            "CANTIDAD_DEFECTUOSA": defectuosa,
            "CANTIDAD_PRODUCIDA": producida
        }

        error = validar_datos(datos)

        if error:
            st.warning(error)

        else:
            nuevo_registro = preparar_datos(
                fecha, maquina, turno, producto, operador,
                programada, producida, defectuosa,
                tiempo_programado, tiempo_parada, causa
            )

            try:
                respuesta = (
                    supabase.table(TABLA)
                    .insert(nuevo_registro)
                    .execute()
                )

                if respuesta.data:
                    st.success("¡Registro creado correctamente!")
                    st.rerun()
                else:
                    st.warning("No se recibió confirmación del registro.")

            except Exception as e:
                st.error(f"Error al registrar: {e}")


# ==========================================
# 6. UPDATE - ACTUALIZAR
# ==========================================

with tab3:

    st.subheader("Actualizar registro existente")

    try:
        registros = consultar_registros()

        if registros:

            opciones = {
                f"ID {r['id']} - {r.get('MAQUINA')} - {r.get('PRODUCTO')}": r
                for r in registros
            }

            seleccion = st.selectbox(
                "Seleccionar registro",
                list(opciones.keys())
            )

            registro = opciones[seleccion]

            resultado = formulario_registro(
                datos=registro,
                clave=f"editar_{registro['id']}"
            )

            (
                guardar, fecha, maquina, turno, producto, operador,
                programada, producida, defectuosa,
                tiempo_programado, tiempo_parada, causa
            ) = resultado

            if guardar:

                datos = {
                    "MAQUINA": maquina,
                    "TURNO": turno,
                    "PRODUCTO": producto,
                    "OPERADOR": operador,
                    "CANTIDAD_DEFECTUOSA": defectuosa,
                    "CANTIDAD_PRODUCIDA": producida
                }

                error = validar_datos(datos)

                if error:
                    st.warning(error)

                else:
                    actualizacion = preparar_datos(
                        fecha, maquina, turno, producto, operador,
                        programada, producida, defectuosa,
                        tiempo_programado, tiempo_parada, causa
                    )

                    respuesta = (
                        supabase.table(TABLA)
                        .update(actualizacion)
                        .eq("id", registro["id"])
                        .execute()
                    )

                    if respuesta.data:
                        st.success("Registro actualizado correctamente.")
                        st.rerun()
                    else:
                        st.warning("No se actualizó ningún registro.")

        else:
            st.info("No hay registros para actualizar.")

    except Exception as e:
        st.error(f"Error al actualizar: {e}")


# ==========================================
# 7. DELETE - ELIMINAR
# ==========================================

with tab4:

    st.subheader("Eliminar registro")

    st.warning("Esta acción es permanente.")

    try:
        registros = consultar_registros()

        if registros:

            opciones = {
                f"ID {r['id']} - {r.get('MAQUINA')} - {r.get('PRODUCTO')}": r
                for r in registros
            }

            seleccion = st.selectbox(
                "Seleccionar registro para eliminar",
                list(opciones.keys())
            )

            registro = opciones[seleccion]

            st.write("**Máquina:**", registro.get("MAQUINA"))
            st.write("**Producto:**", registro.get("PRODUCTO"))
            st.write("**Operador:**", registro.get("OPERADOR"))

            confirmar = st.checkbox(
                "Confirmo que deseo eliminar este registro."
            )

            if st.button(
                "Eliminar registro",
                type="primary",
                disabled=not confirmar
            ):

                respuesta = (
                    supabase.table(TABLA)
                    .delete()
                    .eq("id", registro["id"])
                    .execute()
                )

                if respuesta.data:
                    st.success("Registro eliminado correctamente.")
                    st.rerun()
                else:
                    st.warning("No se recibió confirmación de eliminación.")

        else:
            st.info("No hay registros para eliminar.")

    except Exception as e:
        st.error(f"Error al eliminar: {e}")


# ==========================================
# 8. PIE DE PÁGINA
# ==========================================

st.divider()
st.caption("Sistema CRUD de producción | Python + Streamlit + Supabase")
