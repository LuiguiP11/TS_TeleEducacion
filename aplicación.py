import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
import docx
from io import BytesIO

# --- CONFIGURACIÓN DEL SERVIDOR FLASK ---
# Usamos 'app' como nombre estándar
app = Flask(__name__)

# --- CONFIGURACIÓN SEGURA DE LA API KEY ---
# La cargamos desde una "variable de entorno" que configuraremos en el sitio de hosting.
# ¡NUNCA escribas la clave directamente en el código!
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
except Exception as e:
    # Esto nos ayudará a saber si la clave no está configurada
    print(f"Error al configurar la API de Google: {e}")
    model = None

# --- EL PROMPT (LAS INSTRUCCIONES) PARA LA IA ---
PROMPT_PEDAGOGICO = """
Actúa como un asesor pedagógico experto para la organización TulaSalud en Cobán, Alta Verapaz.
He recibido el siguiente texto extraído de un documento didáctico. Tu tarea es realizar un análisis en dos partes, usando Markdown para el formato:

**Análisis de Fortalezas:**
* Valida los puntos fuertes del documento, considerando que está dirigido a jóvenes y adultos.
* Menciona la alineación con los objetivos de salud comunitaria de TulaSalud.
* Evalúa la relevancia cultural para la región.

**Áreas de Mejora y Observaciones:**
* Proporciona un mínimo de 3 sugerencias detalladas y accionables para mejorar el material.
* Explica la observación (el porqué) y la acción concreta a realizar.
* Enfócate en aumentar la interactividad, la accesibilidad (uso de visuales, lenguaje claro) y el impacto comunitario.

El texto a analizar es el siguiente:
---
{TEXTO_DEL_DOCUMENTO}
---
"""

# --- RUTA PRINCIPAL QUE MUESTRA LA PÁGINA WEB ---
@app.route('/')
def index():
    # Sirve el archivo index.html
    return render_template('index.html')

# --- RUTA DE LA API QUE HACE EL ANÁLISIS ---
@app.route('/api/analizar', methods=['POST'])
def analizar_documento():
    if model is None:
        return jsonify({"error": "El servicio de IA no está configurado correctamente en el servidor."}), 500

    if 'documento_word' not in request.files:
        return jsonify({"error": "No se encontró ningún archivo en la solicitud."}), 400

    file = request.files['documento_word']

    if file.filename == '':
        return jsonify({"error": "No se seleccionó ningún archivo."}), 400

    try:
        # Lee el contenido del archivo en memoria
        document_stream = BytesIO(file.read())
        document = docx.Document(document_stream)
        
        # Extrae el texto de todos los párrafos
        texto_completo = "\n".join([para.text for para in document.paragraphs])

        if not texto_completo.strip():
            return jsonify({"error": "El documento parece estar vacío o no contiene texto legible."}), 400

        # Formatea el prompt con el texto extraído
        prompt_completo = PROMPT_PEDAGOGICO.format(TEXTO_DEL_DOCUMENTO=texto_completo)
        
        # --- LLAMADA REAL A LA IA ---
        response = model.generate_content(prompt_completo)
        
        # Devolvemos la respuesta de la IA al frontend
        return jsonify({"analisis": response.text})

    except Exception as e:
        # Captura cualquier otro error durante el proceso
        return jsonify({"error": f"Ocurrió un error al procesar el archivo: {str(e)}"}), 500

# Vercel redeploy trigger
# Esta parte es necesaria para que algunos servicios de hosting encuentren la app
if __name__ == '__main__':
    app.run()
