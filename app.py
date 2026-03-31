import streamlit as st
import pdfplumber
import google.generativeai as genai
import os
from io import BytesIO

# Configurar la página
st.set_page_config(page_title="Comparador de Documentos", layout="centered")
st.title("📄 Comparador de Documentos MEPRSA")
st.markdown("Carga la versión **antigua** y la **nueva** del documento para obtener un resumen de los cambios.")

# Leer API Key desde los secrets de Streamlit
api_key = st.secrets["GEMINI_API_KEY"]
if not api_key:
    st.error("No se encontró la API Key de Gemini. Configúrala en los secrets.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")  # o gemini-1.5-pro si prefieres

# Funciones
def extraer_texto_pdf(pdf_bytes):
    """Extrae el texto de un archivo PDF subido."""
    texto = ""
    with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
        for pagina in pdf.pages:
            texto_pagina = pagina.extract_text()
            if texto_pagina:
                texto += texto_pagina + "\n"
    return texto.strip()

def generar_resumen_cambios(texto_antiguo, texto_nuevo):
    """Usa Gemini para comparar los textos y generar viñetas de cambios."""
    prompt = f"""
    Eres un asistente especializado en gestión documental. Compara el siguiente documento ANTIGUO con el NUEVO.
    Genera un resumen de los cambios en formato de viñetas (cada viñeta con un guión -). 
    Debe ser resumido pero preciso. Indica qué se eliminó, qué se añadió y qué se modificó, mencionando secciones o ideas principales.
    No incluyas números de versión, fechas ni sugerencias de cambios futuros. Solo los cambios detectados.

    --- DOCUMENTO ANTIGUO ---
    {texto_antiguo}

    --- DOCUMENTO NUEVO ---
    {texto_nuevo}

    Resumen de cambios:
    """
    respuesta = model.generate_content(prompt)
    return respuesta.text

# Interfaz
col1, col2 = st.columns(2)

with col1:
    archivo_antiguo = st.file_uploader("📄 Documento ANTIGUO (PDF)", type=["pdf"], key="antiguo")
with col2:
    archivo_nuevo = st.file_uploader("📄 Documento NUEVO (PDF)", type=["pdf"], key="nuevo")

if archivo_antiguo and archivo_nuevo:
    if st.button("🚀 Comparar documentos"):
        with st.spinner("Extrayendo texto de los PDFs..."):
            texto_antiguo = extraer_texto_pdf(archivo_antiguo.read())
            texto_nuevo = extraer_texto_pdf(archivo_nuevo.read())

        if not texto_antiguo or not texto_nuevo:
            st.error("No se pudo extraer texto de uno o ambos PDFs. Verifica que no estén escaneados o protegidos.")
            st.stop()

        st.success("Texto extraído correctamente. Enviando a Gemini...")

        with st.spinner("Generando resumen de cambios..."):
            try:
                resumen = generar_resumen_cambios(texto_antiguo, texto_nuevo)
            except Exception as e:
                st.error(f"Error al comunicarse con Gemini: {e}")
                st.stop()

        st.subheader("📝 Resumen de cambios (para Control de Versiones)")
        st.markdown(resumen)

        # Botón para copiar
        st.code(resumen, language="markdown")
        st.button("📋 Copiar al portapapeles", on_click=lambda: st.write("(Selecciona el texto y copia con Ctrl+C)"))
else:
    st.info("Esperando la carga de ambos documentos para comenzar.")
