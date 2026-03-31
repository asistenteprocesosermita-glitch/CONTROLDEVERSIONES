import streamlit as st
import pdfplumber
import google.generativeai as genai
from io import BytesIO

# Configuración de la página
st.set_page_config(page_title="Control de Versiones IA", layout="centered")

# Título principal
st.title("📌 CONTROL DE VERSIONES IA")
st.markdown("Carga la versión antigua y la nueva del documento para obtener el control de versiones.")

# --- Obtener API Key desde los secrets de Streamlit ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ No se encontró la API Key de Gemini. Configúrala en los secrets de Streamlit.")
    st.stop()

genai.configure(api_key=api_key)
# Usamos Gemini 1.5 Flash por ser más rápido y económico; si prefieres más calidad, cambia a "gemini-1.5-pro"
model = genai.GenerativeModel("gemini-2.5-flash")

# --- Funciones auxiliares ---
def extraer_texto_pdf(pdf_bytes):
    """Extrae el texto de un archivo PDF."""
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
    """Envía los textos a Gemini y obtiene un resumen conciso pero detallado de los cambios."""
    prompt = f"""
    Eres un especialista en gestión documental. Compara el documento ANTIGUO con el NUEVO y genera un resumen de cambios con las siguientes características:
    - Usa viñetas con guiones (-).
    - Cada viñeta debe ser breve pero precisa: indica la sección, numeral o apartado donde ocurrió el cambio.
    - Especifica si fue una adición, eliminación o modificación.
    - No incluyas números de versión, fechas, ni sugerencias de acciones futuras.
    - Prioriza cambios sustanciales; evita enumerar cambios de formato o puntuación a menos que afecten el contenido.

    --- DOCUMENTO ANTIGUO ---
    {texto_antiguo}

    --- DOCUMENTO NUEVO ---
    {texto_nuevo}

    Resumen de cambios (solo viñetas):
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
    if st.button("🚀 Generar Control de Versiones"):
        with st.spinner("Extrayendo texto de los PDFs..."):
            texto_antiguo = extraer_texto_pdf(archivo_antiguo.read())
            texto_nuevo = extraer_texto_pdf(archivo_nuevo.read())

        if not texto_antiguo or not texto_nuevo:
            st.error("No se pudo extraer texto de uno o ambos PDFs. Asegúrate de que no estén escaneados o protegidos.")
            st.stop()

        st.success("Texto extraído correctamente. Analizando cambios con Gemini...")

        with st.spinner("Generando resumen..."):
            try:
                resumen = generar_resumen_cambios(texto_antiguo, texto_nuevo)
            except Exception as e:
                st.error(f"Error al comunicarse con Gemini: {e}")
                st.stop()

        st.subheader("📝 Resumen de cambios (para el apartado Modificación)")
        st.markdown(resumen)

        # Mostrar en un área de código para copiar fácilmente
        st.text_area("Texto listo para copiar", resumen, height=200)

        # Botón para copiar (Streamlit no tiene función nativa, pero podemos sugerir)
        st.info("Selecciona el texto de arriba y copia con Ctrl+C (Cmd+C en Mac).")
else:
    st.info("Esperando la carga de ambos documentos para comenzar.")
