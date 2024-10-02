import streamlit as st
import requests

# Configuración de la página
st.set_page_config(
    page_title="📝 Editor de Texto con Corrección Automática",
    layout="wide",
)

# Título de la aplicación
st.title("📝 Editor de Texto con Corrección Automática")

# Descripción
st.markdown("""
Esta aplicación permite escribir texto con **notas a pie de página** y corregir errores gramaticales y ortográficos automáticamente utilizando la **API de LanguageTool**. Las notas a pie de página se preservarán en el texto corregido.
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

# Área de texto para ingresar el texto
user_text = st.text_area(
    "Ingresa tu texto aquí (puede incluir notas a pie de página):",
    height=300,
    placeholder="Escribe o pega tu texto con notas a pie de página aquí..."
)

# Función para corregir el texto utilizando la API de LanguageTool
def corregir_texto(texto, idioma):
    url = "https://api.languagetool.org/v2/check"
    data = {
        'text': texto,
        'language': idioma,
        'enabledOnly': False,
        'ignoreTypes': 'TYPO'  # Opcional: Ignora ciertos tipos de errores si lo deseas
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
                # Evitar reemplazar dentro de una nota a pie de página
                if not es_dentro_de_footnote(start, texto):
                    corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
        return corrected_text
    except requests.exceptions.RequestException as e:
        st.error(f"Ocurrió un error al conectar con la API de LanguageTool: {e}")
        return texto

def es_dentro_de_footnote(pos, texto):
    """
    Verifica si una posición dada en el texto está dentro de una nota a pie de página.
    Asume que las notas a pie de página están en formato Markdown: [^1], [^2], etc.
    """
    # Encontrar todas las posiciones de inicio y fin de las notas a pie de página
    import re
    footnote_definitions = list(re.finditer(r'\[\^[^\]]+\]', texto))
    for match in footnote_definitions:
        start, end = match.span()
        if start <= pos < end:
            return True
    return False

# Botón para corregir el texto
if st.button("Corregir Texto"):
    if user_text.strip() == "":
        st.warning("Por favor, ingresa algún texto para corregir.")
    else:
        with st.spinner("Corrigiendo..."):
            texto_corregido = corregir_texto(user_text, language_options[selected_language])
            st.success("¡Corrección completada!")
            st.markdown("### Texto Corregido:")
            st.text_area(
                "",
                value=texto_corregido,
                height=300
            )
