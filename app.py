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

# Configurar Gemini
genai.configure(api_key=api_key)
# Usamos Gemini 1.5 Flash con temperatura baja para respuestas más concisas y predecibles
generation_config = {
    "temperature": 0.2,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    generation_config=generation_config
)

# Funciones auxiliares
def extraer_texto_pdf(pdf_bytes):
    """Extrae el texto de un PDF usando pdfplumber."""
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
    """Envía a Gemini para comparar documentos y obtener resumen conciso."""
    prompt = f"""
    Eres un especialista en gestión documental. Compara el documento ANTIGUO con el NUEVO y genera un resumen de cambios siguiendo estas reglas:

    - Agrupa los cambios por sección o numeral. Usa un formato jerárquico con viñetas.
    - Para cada sección, escribe una viñeta principal con el identificador de la sección (ej. "4. DEFINICIONES").
    - Debajo, enumera los cambios de esa sección con subviñetas. No uses la palabra "Adición:" o "Modificación:" al inicio de cada subviñeta; integra la acción de forma natural en la frase. Ejemplo: "Se agregó la definición de ...", "Se modificó la descripción de ...", "Se eliminó el punto ...".
    - Sé conciso. Describe el cambio en una línea corta, sin detalles excesivos. Evita textos largos.
    - No repitas el mismo título varias veces. Agrupa todos los cambios de una sección bajo una sola viñeta principal.
    - No incluyas números de versión, fechas ni sugerencias.

    --- DOCUMENTO ANTIGUO ---
    {texto_antiguo}

    --- DOCUMENTO NUEVO ---
    {texto_nuevo}

    Resumen de cambios:
    """
    respuesta = model.generate_content(prompt)
    return respuesta.text

# Interfaz de usuario
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

        st.text_area("Texto listo para copiar", resumen, height=250)
        st.info("Selecciona el texto de arriba y copia con Ctrl+C (Cmd+C en Mac).")
else:
    st.info("Esperando la carga de ambos documentos para comenzar.")
