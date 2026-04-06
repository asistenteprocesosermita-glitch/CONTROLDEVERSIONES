import streamlit as st
import pdfplumber
import google.generativeai as genai
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="Control de Versiones IA",
    page_icon="📌",
    layout="centered"
)

# Título y descripción
st.title("📌 CONTROL DE VERSIONES IA")
st.markdown("Carga la versión antigua y la nueva del documento para obtener el control de versiones.")

# Obtener API Key desde secrets
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ No se encontró la API Key de Gemini. Configúrala en los secrets de Streamlit.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Funciones ---
def extraer_texto_pdf(pdf_bytes):
    texto_completo = ""
    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            for pagina in pdf.pages:
                texto_pagina = pagina.extract_text()
                if texto_pagina:
                    texto_completo += texto_pagina + "\n"
    except Exception as e:
        st.error(f"Error al leer el PDF: {e}")
        return ""
    return texto_completo.strip()

def generar_resumen_cambios(texto_antiguo, texto_nuevo):
    prompt = f"""
    Eres un especialista en gestión documental. Compara el documento ANTIGUO con el NUEVO y genera un resumen de cambios siguiendo estas reglas:

    1. Utiliza un estilo preciso y conciso, como en los siguientes ejemplos:
       - Se modifica el título: antes “X”, ahora “Y”.
       - Se reestructura el objetivo, alcance y consideraciones generales.
       - En la sección 6.1, se reestructuran las actividades: “Actividad1”, “Actividad2”.
       - Se agrega una nueva sección 7.6 con consideraciones específicas para...
       - Se actualiza el numeral 4, incluyendo nuevas causas.
       - Se elimina el numeral 6.2.
       - Se agregan dos anexos: “Anexo1” y “Anexo2”.

    2. Agrupa los cambios por sección o numeral. No repitas el mismo título en varias viñetas.
    3. Para cada sección, usa una viñeta principal (con guión) y dentro de ella describe todos los cambios de esa sección, ya sea en una lista o en texto continuo.
    4. Usa las palabras clave: “Se agrega”, “Se elimina”, “Se modifica”, “Se actualiza”, “Se reestructura”, “Se incluye”, “Se ajusta”.
    5. No uses la palabra “Adición” repetitiva; intégrala en la frase.
    6. No incluyas números de versión, fechas, ni sugerencias futuras.
    7. Sé muy preciso: menciona los numerales o títulos de sección afectados.

    --- DOCUMENTO ANTIGUO ---
    {texto_antiguo}

    --- DOCUMENTO NUEVO ---
    {texto_nuevo}

    Resumen de cambios (con el formato descrito):
    """
    respuesta = model.generate_content(prompt)
    return respuesta.text

def resumir_aun_mas(texto_resumen):
    prompt_resumir = f"""
    Tienes el siguiente resumen de cambios de un documento. Por favor, resúmelo aún más, haciéndolo más corto pero manteniendo la información esencial y el formato de viñetas (con guiones). Elimina redundancias, combina ideas similares y usa frases más directas. No pierdas datos importantes como números de sección o cambios clave.

    Resumen original:
    {texto_resumen}

    Resumen más condensado (manteniendo viñetas y precisión):
    """
    respuesta = model.generate_content(prompt_resumir)
    return respuesta.text

# --- Interfaz de usuario ---
col1, col2 = st.columns(2)

with col1:
    archivo_antiguo = st.file_uploader("📄 Documento ANTIGUO (PDF)", type=["pdf"], key="antiguo")
with col2:
    archivo_nuevo = st.file_uploader("📄 Documento NUEVO (PDF)", type=["pdf"], key="nuevo")

# Inicializar session_state para el resumen
if "resumen_actual" not in st.session_state:
    st.session_state.resumen_actual = ""
if "resumen_original" not in st.session_state:
    st.session_state.resumen_original = ""

if archivo_antiguo and archivo_nuevo:
    if st.button("🚀 Generar Control de Versiones"):
        with st.spinner("Extrayendo texto de los PDFs..."):
            texto_antiguo = extraer_texto_pdf(archivo_antiguo.read())
            texto_nuevo = extraer_texto_pdf(archivo_nuevo.read())

        if not texto_antiguo or not texto_nuevo:
            st.error("No se pudo extraer texto de uno o ambos PDFs. Asegúrate de que no estén escaneados o protegidos.")
            st.stop()

        st.success("Texto extraído correctamente. Analizando cambios con Gemini...")

        with st.spinner("Generando resumen conciso..."):
            try:
                resumen = generar_resumen_cambios(texto_antiguo, texto_nuevo)
                st.session_state.resumen_actual = resumen
                st.session_state.resumen_original = resumen  # guardamos el original por si se quiere resetear
            except Exception as e:
                st.error(f"Error al comunicarse con Gemini: {e}")
                st.stop()

        st.subheader("📝 Resumen de cambios (para el apartado Modificación)")
        st.markdown(st.session_state.resumen_actual)

        st.text_area("Texto listo para copiar", st.session_state.resumen_actual, height=250, key="area_texto")
        st.info("Selecciona el texto de arriba y copia con Ctrl+C (Cmd+C en Mac).")

# Siempre mostrar el botón de resumir si hay un resumen actual
if st.session_state.resumen_actual:
    col_boton1, col_boton2 = st.columns(2)
    with col_boton1:
        if st.button("✨ QUIERES HACERLO MÁS RESUMIDO"):
            with st.spinner("Resumiendo aún más con IA..."):
                try:
                    resumen_nuevo = resumir_aun_mas(st.session_state.resumen_actual)
                    st.session_state.resumen_actual = resumen_nuevo
                    # Actualizar la visualización
                    st.subheader("📝 Resumen de cambios (versión más resumida)")
                    st.markdown(st.session_state.resumen_actual)
                    # Actualizar el text_area usando la clave
                    st.text_area("Texto listo para copiar", st.session_state.resumen_actual, height=250, key="area_texto_actualizada")
                    st.success("¡Resumen condensado exitosamente!")
                    st.rerun()  # Forzar actualización de la interfaz
                except Exception as e:
                    st.error(f"Error al resumir: {e}")
    with col_boton2:
        if st.button("🔄 Restaurar resumen original"):
            st.session_state.resumen_actual = st.session_state.resumen_original
            st.rerun()
