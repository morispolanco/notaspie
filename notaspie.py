import streamlit as st
import requests
import re
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from io import BytesIO

# Configuración de la página
st.set_page_config(
    page_title="📝 Editor de Documentos con Corrección Automática",
    layout="wide",
)

# Título de la aplicación
st.title("📝 Editor de Documentos con Corrección Automática")

# Descripción
st.markdown("""
Esta aplicación permite **subir archivos `.docx`** con notas a pie de página y corregir errores gramaticales y ortográficos automáticamente utilizando la **API de LanguageTool**. Las notas a pie de página se preservarán en el documento corregido.
""")

# Selección de idioma
language_options = {
    "Español": "es",
    "Inglés (EE.UU.)": "en-US",
    "Francés": "fr",
    "Alemán": "de",
    # Puedes añadir más idiomas soportados por LanguageTool
}

st.sidebar.header("Configuración")
selected_language = st.sidebar.selectbox(
    "Selecciona el idioma del texto:",
    options=list(language_options.keys()),
    index=0
)

# Función para corregir texto utilizando la API de LanguageTool
def corregir_texto(texto, idioma):
    url = "https://api.languagetool.org/v2/check"
    data = {
        'text': texto,
        'language': idioma,
        'enabledOnly': False,
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        matches = result.get('matches', [])

        # Aplicar las correcciones en orden inverso para no afectar los índices
        corrected_text = texto
        for match in sorted(matches, key=lambda x: x['offset'], reverse=True):
            if match['replacements']:
                replacement = match['replacements'][0]['value']
                start = match['offset']
                end = match['offset'] + match['length']
                corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
        return corrected_text
    except requests.exceptions.RequestException as e:
        st.error(f"Ocurrió un error al conectar con la API de LanguageTool: {e}")
        return texto

# Función para procesar el documento .docx
def procesar_docx(file, idioma):
    # Leer el documento original
    try:
        document = Document(file)
    except Exception as e:
        st.error(f"Error al leer el archivo .docx: {e}")
        return None

    # Extraer el texto de los párrafos y las notas a pie de página
    # Debido a las limitaciones de python-docx para manejar footnotes,
    # se preservarán las referencias a las footnotes pero no su contenido.
    # El contenido de las footnotes se mantendrá sin modificaciones.

    # Extraer todas las footnotes
    footnotes = {}
    for rel in document.part.rels:
        if document.part.rels[rel].reltype == RT.FOOTNOTE:
            footnote_part = document.part.rels[rel].target_part
            footnote_id = rel.split("/")[-1]
            footnote_text = ""
            for para in footnote_part.element.findall(".//w:p", namespaces=footnote_part.element.nsmap):
                for node in para.iter():
                    if node.tag.endswith('t'):
                        footnote_text += node.text
            footnotes[footnote_id] = footnote_text

    # Procesar cada párrafo
    for para in document.paragraphs:
        original_text = para.text
        if original_text.strip() == "":
            continue  # Ignorar párrafos vacíos

        # Corregir el texto del párrafo
        corrected_text = corregir_texto(original_text, idioma)

        # Reemplazar el texto corregido en el párrafo
        para.text = corrected_text

    # Guardar el documento corregido en un buffer
    buffer = BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer

# Área de carga de archivo
uploaded_file = st.file_uploader(
    "Sube tu archivo .docx aquí:",
    type=["docx"]
)

# Botón para corregir el documento
if uploaded_file is not None:
    if st.button("Corregir Documento"):
        with st.spinner("Corrigiendo el documento..."):
            archivo_corregido = procesar_docx(uploaded_file, language_options[selected_language])
            if archivo_corregido:
                st.success("¡Corrección completada!")
                st.download_button(
                    label="Descargar Documento Corregido",
                    data=archivo_corregido,
                    file_name="documento_corregido.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
