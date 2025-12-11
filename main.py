import os
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Hola desde Flask en Railway!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # 8000 local, en Railway SOBREESCRIBE PORT
    app.run(host="0.0.0.0", port=port)