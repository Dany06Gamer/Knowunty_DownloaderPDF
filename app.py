import os
import asyncio
import requests
import io
from flask import Flask, request, render_template_string, send_file
import flet as ft
from playwright.async_api import async_playwright

app = Flask(__name__)

SESSION_DIR = "sessione_knowunity"
if not os.path.exists(SESSION_DIR):
    os.makedirs(SESSION_DIR)

# --- LOGICA DI DOWNLOAD AUTOMATICA ---
async def fetch_pdf_link(url, headless=True):
    pdf_found_url = [None]
    async with async_playwright() as p:
        # Avviamo il browser simulando un utente reale
        browser = await p.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"])
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = await context.new_page()

        # Intercettiamo i file di rete alla ricerca del PDF originale
        async def catch_pdf(response):
            if ".pdf" in response.url.lower() and "knowunity" in response.url:
                pdf_found_url[0] = response.url

        page.on("response", catch_pdf)
        
        try:
            # Sostituiamo i link della versione mobile/app con quella web standard se necessario
            if "knowunity.page.link" in url or "link.knowunity.com" in url:
                # Se i tuoi amici incollano i link presi dall'app dello smartphone, attendiamo il redirect
                await page.goto(url, wait_until="DOMContentLoaded", timeout=60000)
                url = page.url

            await page.goto(url, wait_until="networkidle", timeout=60000)
            
            # --- SIMULAZIONE CLICK AUTOMATICO ---
            # Questo blocco cerca i bottoni tipici di KnowUnity per espandere il documento a schermo intero
            # e forzare il caricamento del PDF reale in background.
            selectors = [
                "button:has-text('Espandi')", 
                "button:has-text('Schermo intero')", 
                ".fullscreen-button", 
                "div[role='button'] >> has-text('Leggi')"
            ]
            
            for selector in selectors:
                try:
                    if await page.is_visible(selector, timeout=3000):
                        await page.click(selector)
                        await asyncio.sleep(2) # Aspetta che si carichi la visualizzazione
                        break
                except:
                    continue

            # Aspettiamo qualche secondo extra per dare tempo al PDF di apparire nella rete
            for _ in range(10): 
                if pdf_found_url[0]: 
                    break
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Errore durante la navigazione: {e}")
            return None
        finally:
            await browser.close()
            
    return pdf_found_url[0]

# --- INTERFACCIA WEB SEMPLICE PER I TUOI AMICI ---
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
        <form action="/download" method="post" onsubmit="document.querySelector('button').innerText='ELABORAZIONE IN CORSO...';">
            <input type="text" name="url" placeholder="https://knowunity.it/..." required>
            <button type="submit">SCARICA PDF</button>
        </form>
    </div>
    <div class="footer">Creato con 🧠 per gli amici</div>
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
        return send_file(io.BytesIO(resp.content), mimetype='application/pdf', as_attachment=True, download_name="appunto_knowunity.pdf")
    return "<h3>Errore: Impossibile recuperare il PDF automaticamente. Assicurati che il link sia corretto o riprova tra pochi secondi.</h3><br><a href='/'>Torna indietro</a>"

# --- SEZIONE DESKTOP (FLET) ---
async def main_desktop(page: ft.Page):
    page.title = "KnowUnity Downloader"

if "PORT" in os.environ:
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
else:
    if __name__ == "__main__":
        ft.app(target=main_desktop)
