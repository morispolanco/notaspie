import streamlit as st
import requests
import re

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

# Función para extraer y separar las notas a pie de página del texto principal
def separar_footnotes(texto):
    """
    Separa las definiciones de notas a pie de página del texto principal.
    Retorna el texto sin las definiciones de footnotes y una lista con las definiciones extraídas.
    """
    # Expresión regular para encontrar definiciones de footnotes en Markdown
    pattern = re.compile(r'(\[\^[^\]]+\]:.*(?:\n(?!\[\^[^\]]+\]:).*)*)', re.MULTILINE)
    footnotes = pattern.findall(texto)
    # Eliminar las definiciones de footnotes del texto principal
    texto_sin_footnotes = pattern.sub('', texto).strip()
    return texto_sin_footnotes, footnotes

# Función para reintegrar las definiciones de footnotes al texto
def reintegrar_footnotes(texto_principal, footnotes):
    """
    Reintegra las definiciones de footnotes al texto principal.
    """
    texto_corregido = texto_principal.strip()
    if footnotes:
        texto_corregido += "\n\n" + "\n\n".join(footnotes)
    return texto_corregido

# Función para corregir el texto utilizando la API de LanguageTool
def corregir_texto(texto, idioma):
    # Separar footnotes del texto principal
    texto_principal, footnotes = separar_footnotes(texto)
    
    url = "https://api.languagetool.org/v2/check"
    data = {
        'text': texto_principal,
        'language': idioma,
        'enabledOnly': False,
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        matches = result.get('matches', [])

        # Aplicar las correcciones en orden inverso para no afectar los índices
        corrected_text = texto_principal
        for match in sorted(matches, key=lambda x: x['offset'], reverse=True):
            if match['replacements']:
                replacement = match['replacements'][0]['value']
                start = match['offset']
                end = match['offset'] + match['length']
                corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
        
        # Reintegrar las footnotes
        texto_corregido = reintegrar_footnotes(corrected_text, footnotes)
        return texto_corregido
    except requests.exceptions.RequestException as e:
        st.error(f"Ocurrió un error al conectar con la API de LanguageTool: {e}")
        return texto

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
