import streamlit as st
from docx2python import docx2python
import re
import requests
import json
import os

# Función para convertir números a superíndice Unicode
def to_superscript(number):
    superscript_map = {
        '0': '⁰',
        '1': '¹',
        '2': '²',
        '3': '³',
        '4': '⁴',
        '5': '⁵',
        '6': '⁶',
        '7': '⁷',
        '8': '⁸',
        '9': '⁹'
    }
    return ''.join(superscript_map.get(digit, digit) for digit in str(number))

# Configuración de la página
st.set_page_config(
    page_title="Convertidor de DOCX a HTML con Notas a Pie de Página",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Título de la aplicación
st.title("Convertidor de DOCX a HTML con Notas a Pie de Página")

# Instrucciones
st.markdown("""
Esta aplicación permite subir un archivo `.docx` con notas a pie de página y lo convierte en HTML.
Las referencias a las notas se mostrarán en superíndice y las notas se listarán al final del documento.
Además, se realiza una solicitud a la API de Together.
""")

# Subir archivo DOCX
uploaded_file = st.file_uploader("Sube tu archivo DOCX", type=["docx"])

if uploaded_file is not None:
    with st.spinner("Procesando el archivo..."):
        # Guardar el archivo temporalmente
        temp_dir = "temp_files"
        os.makedirs(temp_dir, exist_ok=True)
        temp_path = os.path.join(temp_dir, "temp.docx")
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        # Procesar el DOCX
        try:
            result = docx2python(temp_path)
        except Exception as e:
            st.error(f"Error al procesar el archivo DOCX: {e}")
            st.stop()
        
        # Extraer el texto principal
        main_text = ""
        if result.body:
            for section in result.body:
                for paragraph in section:
                    para_text = ""
                    for element in paragraph:
                        if isinstance(element, str):
                            para_text += element
                        elif isinstance(element, list):
                            # Manejar elementos anidados si es necesario
                            para_text += ''.join(element)
                    main_text += para_text + "\n"
        
        # Extraer las notas a pie de página
        footnotes_text = []
        if result.footnotes:
            # footnotes es una lista de listas
            for section in result.footnotes:
                for footnote in section:
                    footnote_content = ""
                    for paragraph in footnote:
                        for element in paragraph:
                            if isinstance(element, str):
                                footnote_content += element
                            elif isinstance(element, list):
                                footnote_content += ''.join(element)
                    footnotes_text.append(footnote_content.strip())
        
        # Reemplazar las referencias de las notas en el texto principal
        # Asumiendo que las referencias están en el formato [^1], [^2], etc.
        # Puedes ajustar la expresión regular según el formato real
        footnote_pattern = re.compile(r'\[\^(\d+)\]')
        
        def replace_footnote(match):
            number = match.group(1)
            # Usar etiquetas <sup> para superíndice en HTML
            return f'<sup>[{number}]</sup>'
        
        processed_text_html = footnote_pattern.sub(replace_footnote, main_text)
        
        # Para el texto que se enviará a la API (texto plano), usar superíndice Unicode
        def replace_footnote_unicode(match):
            number = match.group(1)
            superscript = to_superscript(number)
            return f'[{superscript}]'
        
        processed_text_plain = footnote_pattern.sub(replace_footnote_unicode, main_text)
        
        # Crear el HTML
        html_content = "<html><body>\n"
        
        # Convertir saltos de línea a párrafos HTML
        paragraphs = processed_text_html.split('\n')
        for para in paragraphs:
            para = para.strip()
            if para != "":
                html_content += f"<p>{para}</p>\n"
        
        # Añadir las notas al pie
        if footnotes_text:
            html_content += "<hr>\n<h2>Notas a Pie de Página</h2>\n<ol>\n"
            for note in footnotes_text:
                html_content += f"<li>{note}</li>\n"
            html_content += "</ol>\n"
        
        html_content += "</body></html>"
        
        # Limpiar archivos temporales
        try:
            os.remove(temp_path)
            os.rmdir(temp_dir)
        except Exception:
            pass  # Ignorar si no se puede eliminar

    st.success("Archivo procesado exitosamente!")
    
    # Mostrar el HTML generado
    st.subheader("Vista Previa del HTML")
    st.components.v1.html(html_content, height=600, scrolling=True)
    
    # Botón para enviar a la API de Together
    if st.button("Enviar a la API de Together"):
        with st.spinner("Enviando a la API de Together..."):
            # Obtener la clave API de los secretos
            try:
                api_key = st.secrets["Together"]["API_KEY"]
            except KeyError:
                st.error("La clave API de Together no está configurada en los secretos.")
                st.stop()
            
            # Configurar la solicitud
            url = "https://api.together.xyz/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # Preparar el payload
            payload = {
                "model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
                "messages": [
                    {"role": "system", "content": "Eres un asistente que procesa documentos."},
                    {"role": "user", "content": "Convierte el siguiente HTML a texto plano."},
                    {"role": "user", "content": html_content}
                ],
                "max_tokens": 2512,
                "temperature": 0.7,
                "top_p": 0.7,
                "top_k": 50,
                "repetition_penalty": 1,
                "stop": ["<|eot_id|>"],
                "stream": False  # Cambiar a True si se desea streaming
            }
            
            try:
                response = requests.post(url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                data = response.json()
                
                # Procesar la respuesta (esto depende de la estructura de la respuesta de la API)
                # Asumiendo que la respuesta contiene un campo 'choices' con 'message'
                if "choices" in data and len(data["choices"]) > 0:
                    generated_text = data["choices"][0]["message"]["content"]
                    st.subheader("Respuesta de la API de Together")
                    st.text_area("Texto Generado", generated_text, height=300)
                else:
                    st.error("Respuesta inesperada de la API.")
            except requests.exceptions.HTTPError as errh:
                st.error(f"Error HTTP: {errh}")
            except requests.exceptions.ConnectionError as errc:
                st.error(f"Error de conexión: {errc}")
            except requests.exceptions.Timeout as errt:
                st.error(f"Tiempo de espera agotado: {errt}")
            except requests.exceptions.RequestException as err:
                st.error(f"Error: {err}")
