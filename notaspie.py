import streamlit as st
import requests
import json

# Configuración de la página
st.set_page_config(
    page_title="📝 Editor de Texto con Corrección Gramatical",
    layout="wide",
)

# Título de la aplicación
st.title("📝 Editor de Texto con Corrección Gramatical")

# Descripción
st.markdown("""
Esta aplicación permite escribir texto y verificar errores gramaticales y ortográficos utilizando la **API de LanguageTool**.
""")

# Selección de idioma
language_options = {
    "Español": "es",
    "Inglés": "en-US",
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
    "Ingresa tu texto aquí:",
    height=300,
    placeholder="Escribe o pega tu texto aquí..."
)

# Función para verificar el texto utilizando la API de LanguageTool
def verificar_texto(texto, idioma):
    url = "https://api.languagetool.org/v2/check"
    data = {
        'text': texto,
        'language': idioma,
        'enabledOnly': False
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Ocurrió un error al conectar con la API de LanguageTool: {e}")
        return None

# Función para corregir el texto utilizando la API de LanguageTool
def corregir_texto(texto, idioma):
    url = "https://api.languagetool.org/v2/check"
    data = {
        'text': texto,
        'language': idioma,
        'enabledOnly': False
    }
    try:
        response = requests.post(url, data=data)
        response.raise_for_status()
        result = response.json()
        corrections = result.get('matches', [])
        # Aplicar las correcciones en orden inverso para no afectar los índices
        corrected_text = texto
        for match in sorted(corrections, key=lambda x: x['offset'], reverse=True):
            if match['replacements']:
                replacement = match['replacements'][0]['value']
                start = match['offset']
                end = match['offset'] + match['length']
                corrected_text = corrected_text[:start] + replacement + corrected_text[end:]
        return corrected_text
    except requests.exceptions.RequestException as e:
        st.error(f"Ocurrió un error al conectar con la API de LanguageTool: {e}")
        return texto

# Botón para verificar el texto
if st.button("Verificar Texto"):
    if user_text.strip() == "":
        st.warning("Por favor, ingresa algún texto para verificar.")
    else:
        with st.spinner("Verificando..."):
            resultado = verificar_texto(user_text, language_options[selected_language])
            if resultado:
                matches = resultado.get('matches', [])
                if not matches:
                    st.success("¡No se encontraron errores!")
                else:
                    st.warning(f"Se encontraron {len(matches)} error(es):")
                    for match in matches:
                        error_message = match.get('message', 'Error desconocido.')
                        error_context = match.get('context', {}).get('text', '')
                        error_offset = match.get('context', {}).get('offset', 0)
                        error_length = match.get('context', {}).get('length', 0)
                        incorrect_text = match.get('context', {}).get('text', '')[error_offset:error_offset+error_length]
                        replacements = [r['value'] for r in match.get('replacements', [])]
                        st.markdown(f"**Error:** {error_message}")
                        st.markdown(f"**Texto incorrecto:** `{incorrect_text}`")
                        st.markdown(f"**Sugerencias:** {', '.join(replacements) if replacements else 'Ninguna'}")
                        st.markdown("---")

# Opcional: Mostrar el texto corregido
if st.checkbox("Mostrar texto corregido"):
    if user_text.strip() == "":
        st.warning("Por favor, ingresa algún texto para corregir.")
    else:
        with st.spinner("Corrigiendo texto..."):
            texto_corregido = corregir_texto(user_text, language_options[selected_language])
            st.text_area(
                "Texto Corregido:",
                value=texto_corregido,
                height=300
            )
