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

# --- Obtener API Key desde los secrets de Streamlit ---
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("❌ No se encontró la API Key de Gemini. Configúrala en los secrets de Streamlit.")
    st.stop()

# Configurar Gemini
genai.configure(api_key=api_key)
# Usamos Gemini 1.5 Flash por rapidez; para mayor precisión cambiar a "gemini-1.5-pro"
model = genai.GenerativeModel("gemini-1.5-flash")

# --- Funciones auxiliares ---
def extraer_texto_pdf(pdf_bytes):
    """
    Extrae el texto de un archivo PDF usando pdfplumber.
    Devuelve el texto completo como string.
    """
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
    """
    Envía los textos a Gemini con un prompt optimizado para agrupar cambios por sección.
    Devuelve el resumen en formato markdown con viñetas.
    """
    prompt = f"""
    Eres un especialista en gestión documental. Compara el documento ANTIGUO con el NUEVO y genera un resumen de cambios con las siguientes reglas:

    1. Agrupa los cambios por sección o numeral. No repitas el mismo título varias veces.
    2. Utiliza viñetas con guiones (-). Para cada sección, coloca una viñeta principal con el identificador de la sección (ej. "7.7. CONSIDERACIONES IMPORTANTES") y debajo, en subviñetas (con guiones o espacios), enumera los cambios específicos de esa sección.
    3. En cada cambio específico, indica si es adición, eliminación o modificación, y describe brevemente el contenido.
    4. No incluyas números de versión, fechas, ni sugerencias de acciones futuras.
    5. Si una sección tiene múltiples cambios, inclúyelos todos dentro de la misma viñeta principal.
    6. Sé preciso pero conciso. Evita redundancias.

    --- DOCUMENTO ANTIGUO ---
    {texto_antiguo}

    --- DOCUMENTO NUEVO ---
    {texto_nuevo}

    Resumen de cambios (en formato de viñetas agrupadas por sección):
    """
    respuesta = model.generate_content(prompt)
    return respuesta.text

# --- Interfaz de usuario ---
col1, col2 = st.columns(2)

with col1:
    archivo_antiguo = st.file_uploader(
        "📄 Documento ANTIGUO (PDF)",
        type=["pdf"],
        key="antiguo"
    )

with col2:
    archivo_nuevo = st.file_uploader(
        "📄 Documento NUEVO (PDF)",
        type=["pdf"],
        key="nuevo"
    )

# Botón de comparación
if archivo_antiguo and archivo_nuevo:
    if st.button("🚀 Generar Control de Versiones"):
        with st.spinner("Extrayendo texto de los PDFs..."):
            texto_antiguo = extraer_texto_pdf(archivo_antiguo.read())
            texto_nuevo = extraer_texto_pdf(archivo_nuevo.read())

        if not texto_antiguo or not texto_nuevo:
            st.error(
                "No se pudo extraer texto de uno o ambos PDFs. "
                "Asegúrate de que no estén escaneados o protegidos."
            )
            st.stop()

        st.success("Texto extraído correctamente. Analizando cambios con Gemini...")

        with st.spinner("Generando resumen agrupado..."):
            try:
                resumen = generar_resumen_cambios(texto_antiguo, texto_nuevo)
            except Exception as e:
                st.error(f"Error al comunicarse con Gemini: {e}")
                st.stop()

        st.subheader("📝 Resumen de cambios (para el apartado Modificación)")
        st.markdown(resumen)

        # Área de texto para copiar fácilmente
        st.text_area("Texto listo para copiar", resumen, height=250)
        st.info("Selecciona el texto de arriba y copia con Ctrl+C (Cmd+C en Mac).")
else:
    st.info("Esperando la carga de ambos documentos para comenzar.")
