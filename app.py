import os
from flask import Flask, request, render_template
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Azure Blob Storage setup
AZURE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME")
blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_CONTAINER_NAME)

# MySQL config
MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST"),
    "port": int(os.getenv("MYSQL_PORT", 3306)),
    "user": os.getenv("MYSQL_USER"),
    "password": os.getenv("MYSQL_PASSWORD"),
    "database": os.getenv("MYSQL_DB")
}

def save_file_metadata(filename, url):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id INT AUTO_INCREMENT PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            url VARCHAR(500) NOT NULL
        );
    """)
    cur.execute("INSERT INTO images (filename, url) VALUES (%s, %s)", (filename, url))
    conn.commit()
    cur.close()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"
        file = request.files["file"]
        if file.filename == "":
            return "No selected file"
        filename = secure_filename(file.filename)
        blob_client = container_client.get_blob_client(filename)
        blob_client.upload_blob(file, overwrite=True)
        file_url = blob_client.url
        save_file_metadata(filename, file_url)
        return f"File uploaded! URL: <a href='{file_url}'>{file_url}</a>"
    return render_template("upload.html")

if __name__ == "__main__":
    app.run(debug=True)
