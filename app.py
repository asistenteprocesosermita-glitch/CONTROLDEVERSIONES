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
# CORRECCIÓN: usar modelo válido
model = genai.GenerativeModel("gemini-1.5-flash")  # o "gemini-1.5-pro"

# --- Funciones de extracción y generación ---
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

def generar_detallado(texto_antiguo, texto_nuevo):
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

    Resumen de cambios detallado (con viñetas):
    """
    respuesta = model.generate_content(prompt)
    return respuesta.text

def generar_resumido(texto_antiguo, texto_nuevo):
    prompt = f"""
    Compara el documento ANTIGUO con el NUEVO y genera un resumen de cambios EXTREMADAMENTE CORTO.
    Obligatoriamente debe cumplir:
    - Máximo 100 palabras (ideal 85-100).
    - Un solo párrafo (sin viñetas, sin guiones, sin saltos de línea).
    - Redacción fluida, en español.
    - Solo los cambios más importantes: títulos modificados, secciones nuevas o eliminadas, cambios clave en actividades o definiciones.
    - No incluir números de versión, fechas ni sugerencias.
    - Usa frases como "Se modifica...", "Se agrega...", "Se elimina...", "Se actualiza...".

    --- DOCUMENTO ANTIGUO ---
    {texto_antiguo}

    --- DOCUMENTO NUEVO ---
    {texto_nuevo}

    Resumen ultracorto (único párrafo, máx 100 palabras):
    """
    respuesta = model.generate_content(prompt)
    return respuesta.text

# --- Interfaz de usuario ---
col1, col2 = st.columns(2)

with col1:
    archivo_antiguo = st.file_uploader("📄 Documento ANTIGUO (PDF)", type=["pdf"], key="antiguo")
with col2:
    archivo_nuevo = st.file_uploader("📄 Documento NUEVO (PDF)", type=["pdf"], key="nuevo")

if archivo_antiguo and archivo_nuevo:
    # Leer textos una sola vez y guardar en session_state para no reprocesar
    if st.button("📖 Extraer texto de los PDFs"):
        with st.spinner("Extrayendo texto..."):
            texto_antiguo = extraer_texto_pdf(archivo_antiguo.read())
            texto_nuevo = extraer_texto_pdf(archivo_nuevo.read())
            if texto_antiguo and texto_nuevo:
                st.session_state.texto_antiguo = texto_antiguo
                st.session_state.texto_nuevo = texto_nuevo
                st.success("Textos extraídos correctamente. Ahora puedes generar las versiones.")
            else:
                st.error("No se pudo extraer texto de uno o ambos PDFs.")

    # Solo mostrar botones si ya se extrajeron textos
    if "texto_antiguo" in st.session_state and "texto_nuevo" in st.session_state:
        col_det, col_res = st.columns(2)
        with col_det:
            if st.button("📝 Generar Control de Versiones DETALLADO"):
                with st.spinner("Generando resumen detallado..."):
                    try:
                        detallado = generar_detallado(st.session_state.texto_antiguo, st.session_state.texto_nuevo)
                        st.session_state.detallado = detallado
                    except Exception as e:
                        st.error(f"Error: {e}")
        with col_res:
            if st.button("⚡ Generar Control de Versiones RESUMIDO (máx 100 palabras)"):
                with st.spinner("Generando resumen ultracorto..."):
                    try:
                        resumido = generar_resumido(st.session_state.texto_antiguo, st.session_state.texto_nuevo)
                        st.session_state.resumido = resumido
                    except Exception as e:
                        st.error(f"Error: {e}")

        # Mostrar resultados si existen
        if "detallado" in st.session_state:
            st.subheader("📌 Versión Detallada (con viñetas)")
            st.markdown(st.session_state.detallado)
            st.text_area("Copiar detallado", st.session_state.detallado, height=200, key="copy_det")

        if "resumido" in st.session_state:
            st.subheader("📌 Versión Resumida (único párrafo, ≤100 palabras)")
            st.markdown(f"*{st.session_state.resumido}*")
            st.text_area("Copiar resumido", st.session_state.resumido, height=100, key="copy_res")
            # Contador de palabras opcional
            palabras = len(st.session_state.resumido.split())
            st.caption(f"Palabras: {palabras} / Máx 100")
else:
    st.info("Esperando la carga de ambos documentos para comenzar.")
