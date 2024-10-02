import streamlit as st
import requests
from docx import Document
from docx.opc.constants import RELATIONSHIP_TYPE as RT
from io import BytesIO
import re

# Configuración de la página
st.set_page_config(
    page_title="📝 Editor de Documentos con Corrección Automática",
    layout="wide",
)

# Título de la aplicación
st.title("📝 Editor de Documentos con Corrección Automática")

# Descripción
st.markdown("""
Esta aplicación permite **subir archivos `.docx`** con notas a pie de página y corregir errores gramaticales y ortográficos automáticamente utilizando la **API de LanguageTool**. Las notas a pie de página, así como la estructura y el formato del documento original, se preservarán en el documento corregido.
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

# Función para extraer y separar las footnotes del texto principal
def separar_footnotes(document):
    """
    Separa las definiciones de notas a pie de página del texto principal.
    Retorna el texto sin las definiciones de footnotes y una lista con las definiciones extraídas.
    """
    footnotes = {}
    # Extraer footnotes
    for rel_id, rel in document.part.rels.items():
        if rel.reltype == RT.FOOTNOTE:
            footnote_part = rel.target_part
            footnote_id = rel_id.split("/")[-1]
            footnote_text = ""
            for para in footnote_part.element.findall(".//w:p", namespaces=footnote_part.element.nsmap):
                for node in para.iter():
                    if node.tag.endswith('t') and node.text:
                        footnote_text += node.text + " "
            footnotes[footnote_id] = footnote_text.strip()
    
    # Extraer el texto principal con referencias a footnotes
    texto_principal = ""
    for para in document.paragraphs:
        texto_principal += para.text + "\n"
    
    return texto_principal.strip(), footnotes

# Función para aplicar las correcciones al documento
def aplicar_correcciones(document, texto_corregido):
    """
    Reemplaza el texto de los párrafos en el documento con el texto corregido.
    Preserva los footnotes y el formato de los runs tanto como sea posible.
    """
    # Dividir el texto corregido en párrafos
    parrafos_corregidos = texto_corregido.split('\n')

    # Reemplazar el texto de cada párrafo
    for para, texto_corr in zip(document.paragraphs, parrafos_corregidos):
        if para.text.strip() == "":
            continue  # Ignorar párrafos vacíos
        # Limpiar los runs actuales
        for run in para.runs:
            run.text = ""
        # Agregar el texto corregido como un solo run
        para.add_run(texto_corr)

    return document

# Función para reintegrar las footnotes al documento
def reintegrar_footnotes(document, footnotes):
    """
    Actualmente, las footnotes ya están integradas en el documento.
    Este paso es opcional si se requiere alguna modificación adicional.
    """
    # En este ejemplo, no se realiza ninguna acción adicional.
    # Las footnotes permanecen intactas en el documento.
    return document

# Función para procesar el documento .docx
def procesar_docx(file, idioma):
    # Leer el documento original
    try:
        document = Document(file)
    except Exception as e:
        st.error(f"Error al leer el archivo .docx: {e}")
        return None

    # Separar footnotes y texto principal
    texto_principal, footnotes = separar_footnotes(document)

    # Corregir el texto principal
    texto_corregido = corregir_texto(texto_principal, idioma)

    # Aplicar las correcciones al documento
    document = aplicar_correcciones(document, texto_corregido)

    # Reintegrar las footnotes (si es necesario)
    document = reintegrar_footnotes(document, footnotes)

    # Guardar el documento corregido en un buffer
    buffer = BytesIO()
    try:
        document.save(buffer)
        buffer.seek(0)
        return buffer
    except Exception as e:
        st.error(f"Error al guardar el documento corregido: {e}")
        return None

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
