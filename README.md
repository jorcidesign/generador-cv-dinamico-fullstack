# Generador de CV Dinámico Fullstack

Un script en Python para generar un Curriculum Vitae dinámico y personalizado en formato PDF. 
Este proyecto utiliza `reportlab` para la generación del PDF, `Pillow` para procesar imágenes y `questionary` para la interfaz interactiva en la terminal.

## Requisitos

- Python 3.x
- pip

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/jorcidesign/generador-cv-dinamico-fullstack.git
   cd generador-cv-dinamico-fullstack
   ```

2. Crea y activa un entorno virtual (opcional pero recomendado):
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Linux/Mac
   # .venv\Scripts\activate  # En Windows
   ```

3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```

## Uso

1. Coloca tus datos en la carpeta `inputs/` (como tu foto de perfil y archivo de datos `cv_data.json` si es requerido).
2. Ejecuta el script principal:
   ```bash
   python generate_cv.py
   ```
3. El PDF generado se guardará en la carpeta `output/`.

## Privacidad

Por motivos de privacidad, las carpetas `inputs/` y `output/` están ignoradas en git. Los datos personales y CVs generados se mantienen únicamente en tu entorno local.
