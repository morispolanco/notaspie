import streamlit as st
import language_tool_python
from typing import List

# Configuración de la página
st.set_page_config(
    page_title="Editor de Texto con Corrección Gramatical",
    layout="wide",
)

# Título de la aplicación
st.title("📝 Editor de Texto con Corrección Gramatical")  

# Descripción
st.markdown("""
Esta aplicación permite escribir texto y verificar errores gramaticales y ortográficos utilizando **LanguageTool**.
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

# Botón para verificar el texto
if st.button("Verificar Texto"):
    if user_text.strip() == "":
        st.warning("Por favor, ingresa algún texto para verificar.")
    else:
        with st.spinner("Verificando..."):
            try:
                # Inicializar el corrector con el idioma seleccionado
                tool = language_tool_python.LanguageTool(language_options[selected_language])

                # Buscar coincidencias (errores)
                matches = tool.check(user_text)

                # Mostrar resultados
                if not matches:
                    st.success("¡No se encontraron errores!")
                else:
                    st.warning(f"Se encontraron {len(matches)} error(es):")

                    for match in matches:
                        # Mostrar cada error con detalles
                        st.markdown(f"**Error:** {match.message}")
                        st.markdown(f"**Texto incorrecto:** `{match.context}`")
                        st.markdown(f"**Sugerencias:** {', '.join(match.replacements) if match.replacements else 'Ninguna'}")
                        st.markdown("---")

                tool.close()
            except Exception as e:
                st.error(f"Ocurrió un error al verificar el texto: {e}")

# Opcional: Mostrar el texto corregido
if st.checkbox("Mostrar texto corregido"):
    if user_text.strip() == "":
        st.warning("Por favor, ingresa algún texto para corregir.")
    else:
        with st.spinner("Corrigiendo texto..."):
            try:
                tool = language_tool_python.LanguageTool(language_options[selected_language])
                corrected_text = language_tool_python.utils.correct(user_text, tool.check(user_text))
                st.text_area(
                    "Texto Corregido:",
                    value=corrected_text,
                    height=300
                )
                tool.close()
            except Exception as e:
                st.error(f"Ocurrió un error al corregir el texto: {e}")
