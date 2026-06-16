import os
import asyncio
import requests
import io
from flask import Flask, request, render_template_string, send_file
import flet as ft
from playwright.async_api import async_playwright

# Inizializzazione Flask
app = Flask(__name__)

# Configurazione sessione
SESSION_DIR = "sessione_knowunity"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# --- LOGICA DI DOWNLOAD (CONDIVISA) ---
async def fetch_pdf_link(url, headless=True):
    pdf_found_url = [None]
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=headless)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        page = await context.new_page()

        async def catch_pdf(response):
            if ".pdf" in response.url.lower() and "knowunity" in response.url:
                pdf_found_url[0] = response.url

        page.on("response", catch_pdf)
        
        try:
            await page.goto(url, wait_until="networkidle", timeout=60000)
            for _ in range(15): 
                if pdf_found_url[0]: break
                await asyncio.sleep(1)
        except Exception:
            return None
        finally:
            await browser.close()
    return pdf_found_url[0]

# --- SEZIONE WEB (FLASK) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="it">
<head>
    <meta charset="UTF-8">
    <title>KnowUnity Downloader</title>
    <style>
        body { font-family: sans-serif; background: #121212; color: white; text-align: center; padding: 50px; }
        .container { max-width: 500px; margin: auto; background: #1e1e1e; padding: 30px; border-radius: 15px; }
        input { width: 80%; padding: 10px; margin: 20px 0; border-radius: 5px; border: 1px solid #333; background: #2a2a2a; color: white; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <h1>KnowUnity Downloader</h1>
        <form action="/download" method="post">
            <input type="text" name="url" placeholder="Incolla link qui..." required>
            <button type="submit">SCARICA PDF</button>
        </form>
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/download', methods=['POST'])
def download_route():
    url = request.form.get('url')
    pdf_url = asyncio.run(fetch_pdf_link(url, headless=True))
    if pdf_url:
        resp = requests.get(pdf_url)
        return send_file(io.BytesIO(resp.content), mimetype='application/pdf', as_attachment=True, download_name="appunto.pdf")
    return "Errore: PDF non trovato o link non valido."

# --- SEZIONE DESKTOP (FLET) ---
async def main_desktop(page: ft.Page):
    page.title = "KnowUnity Downloader"
    # ... Qui Flet gestirà la tua interfaccia locale quando sei sul PC ...

# --- AVVIO DINAMICO (OTTIMIZZATO PER RENDER) ---
# Se "PORT" è presente nell'ambiente, eseguiamo DIRETTAMENTE Flask ignorando Flet
if "PORT" in os.environ:
    port = int(os.environ.get("PORT", 5000))
    # Questo avvia Flask forzatamente per Render
    app.run(host='0.0.0.0', port=port)
else:
    # Se sei sul tuo PC locale (senza variabile PORT), si avvia normalmente in modalità Desktop (Flet)
    if __name__ == "__main__":
        ft.app(target=main_desktop)
