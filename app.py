from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'https://www.youtube.com/@GreyMattersYT'

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Usa la variable de entorno PORT
    app.run(host='0.0.0.0', port=port)  # Escucha en 0.0.0.0 y en el puerto especificado
