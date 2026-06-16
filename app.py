import os
import re
import requests
import io
from flask import Flask, request, render_template_string, send_file
import flet as ft

app = Flask(__name__)

# --- LOGICA DI ESTRAZIONE POTENZIATA ---
def get_knowunity_pdf(url):
    try:
        # Puliamo il link da eventuali spazi bianchi
        url = url.strip()
        
        # 1. Se è un link abbreviato, proviamo a espanderlo subito con un finto browser mobile
        if "page.link" in url or "link.knowunity" in url or "knowunity.com/v2/landing" in url:
            headers = {"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"}
            r = requests.get(url=url, headers=headers, allow_redirects=True, timeout=10)
            url = r.url

        # 2. Cerchiamo l'ID dell'appunto (stringa alfanumerica di 36 caratteri con i trattini)
        # Questo trucco trova l'ID ovunque sia posizionato nel link!
        match = re.search(search=r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', string=url, flags=re.IGNORECASE)
        
        # Se non trova l'UUID standard, prova a prendere l'ultima parte del link dopo l'ultimo slash
        if not match:
            # Es: se il link è knowunity.it/knows/qualcosa, prende 'qualcosa'
            if "knows/" in url:
                part = url.split("knows/")[-1]
                death_note_id = part.split("?")[0] # Rimuove eventuali parametri extra
            else:
                death_note_id = url.split("/")[-1].split("?")[0]
        else:
            death_note_id = match.group(1)
            
        if death_note_id:
            # 3. Chiamata all'API globale di KnowUnity
            api_url = f"https://api.knowunity.com/v1/knows/{death_note_id}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json"
            }
            
            response = requests.get(url=api_url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                # Estraiamo il percorso del PDF
                pdf_url = data.get("fileUrl") or data.get("documentUrl")
                if not pdf_url and "documents" in data and len(data["documents"]) > 0:
                    pdf_url = data["documents"][0].get("fileUrl")
                
                if pdf_url:
                    return pdf_url
    except Exception as e:
        print(f"Errore API: {e}")
    return None

# --- INTERFACCIA WEB ---
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
        <p>Incolla qualsiasi link di KnowUnity (PC o Smartphone) per scaricare il PDF.</p>
        <form action="/download" method="post" onsubmit="document.querySelector('button').innerText='SCARICAMENTO IN CORSO...';">
            <input type="text" name="url" placeholder="Incolla il link qui..." required>
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
    pdf_url = get_knowunity_pdf(url=url)
    
    if pdf_url:
        resp = requests.get(url=pdf_url, timeout=20)
        return send_file(
            io.BytesIO(initial_bytes=resp.content), 
            mimetype='application/pdf', 
            as_attachment=True, 
            download_name="appunto_knowunity.pdf"
        )
    
    return "<h3>Errore: Impossibile trovare il documento. Verifica che il link porti a un appunto visibile e riprova.</h3><br><a href='/'>Torna indietro</a>"

# --- SEZIONE DESKTOP ---
async def main_desktop(page: ft.Page):
    page.title = "KnowUnity Downloader"

if "PORT" in os.environ:
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
else:
    if __name__ == "__main__":
        ft.app(target=main_desktop)
