import os
import re
import requests
import io
from flask import Flask, request, render_template_string, send_file
import flet as ft

app = Flask(__name__)

# --- LOGICA DI ESTRAZIONE DIRETTA TRAMITE API ---
def get_knowunity_pdf(url):
    try:
        # 1. Estraiamo l'UUID dell'appunto dal link inserito
        # Funziona con formati tipo: knowunity.it/knows/lettere-numeri-uuid
        match = re.search(search=r'knows/([a-f0-9\-]{36})', string=url)
        if not match:
            # Prova a cercare un ID generico se il link è diverso
            match = re.search(search=r'knows/([a-zA-Z0-9\-]+)', string=url)
            
        if death_note_id := match.group(1) if match else None:
            # 2. Interroghiamo l'API pubblica di KnowUnity per avere i dettagli dell'appunto
            api_url = f"https://api.knowunity.com/v1/knows/{death_note_id}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
            
            response = requests.get(url=api_url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                # 3. Estraiamo il link diretto al file PDF nei server Cloud di KnowUnity
                # Di solito si trova sotto 'documents' o 'fileUrl'
                pdf_url = data.get("fileUrl") or data.get("documentUrl")
                if not pdf_url and "documents" in data and len(data["documents"]) > 0:
                    pdf_url = data["documents"][0].get("fileUrl")
                
                if pdf_url:
                    return pdf_url
    except Exception as e:
        print(f"Errore API: {e}")
    return None

# --- INTERFACCIA WEB PER I TUOI AMICI ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>KnowUnity Downloader</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #121212; color: white; text-align: center; padding: 20px; margin: 0; }
        .container { max-width: 500px; margin: 80px auto auto auto; background: #1e1e1e; padding: 40px 30px; border-radius: 15px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); }
        h1 { color: #007bff; margin-bottom: 10px; font-size: 28px; }
        p { color: #aaa; font-size: 14px; margin-bottom: 30px; }
        input { width: 90%; padding: 12px; margin-bottom: 20px; border-radius: 8px; border: 1px solid #333; background: #2a2a2a; color: white; font-size: 16px; text-align: center; }
        input:focus { border-color: #007bff; outline: none; }
        button { width: 95%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.2s; }
        button:hover { background: #0056b3; }
        .footer { margin-top: 50px; color: #555; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>KnowUnity Downloader 🚀</h1>
        <p>Incolla il link dell'appunto qui sotto e scarica il PDF all'istante.</p>
        <form action="/download" method="post" onsubmit="document.querySelector('button').innerText='SCARICAMENTO IN CORSO...';">
            <input type="text" name="url" placeholder="https://knowunity.it/knows/..." required>
            <button type="submit">SCARICA PDF</button>
        </form>
    </div>
    <div class="footer">Creato per gli amici</div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download_route():
    url = request.form.get('url')
    
    # Se inseriscono un link abbreviato da mobile, ricaviamo quello reale
    if "page.link" in url or "link.knowunity" in url:
        try:
            r = requests.head(url=url, allow_redirects=True, timeout=10)
            url = r.url
        except:
            pass

    pdf_url = get_knowunity_pdf(url=url)
    
    if pdf_url:
        resp = requests.get(url=pdf_url, timeout=20)
        return send_file(
            io.BytesIO(initial_bytes=resp.content), 
            mimetype='application/pdf', 
            as_attachment=True, 
            download_name="appunto_knowunity.pdf"
        )
    
    return "<h3>Errore: Impossibile decodificare questo appunto. Assicurati che il link contenga la dicitura '/knows/' ed sia un appunto valido.</h3><br><a href='/'>Torna indietro</a>"

# --- SEZIONE DESKTOP (MANTENUTA PER COMPATIBILITÀ) ---
async def main_desktop(page: ft.Page):
    page.title = "KnowUnity Downloader"

if "PORT" in os.environ:
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
else:
    if __name__ == "__main__":
        ft.app(target=main_desktop)
