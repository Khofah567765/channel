import os
import json
import urllib.parse
import requests
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

# Memuat konfigurasi
load_dotenv()
WORKER_DOMAIN = os.getenv("WORKER_DOMAIN")
API_URL = "https://ws.kora-api.space/api/matches/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"

def get_m3u8_from_embed(embed_url):
    """Mengekstraksi link m3u8 menggunakan Playwright dengan teknik anti-bot."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT)
        page = context.new_page()

        # Teknik penyamaran browser agar tidak mudah terdeteksi bot
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        found_m3u8 = {"url": None}
        def on_request(request):
            # Mencari request m3u8 yang valid dan memiliki token
            if ".m3u8" in request.url and "st=" in request.url:
                found_m3u8["url"] = request.url

        page.on("request", on_request)
        
        try:
            page.goto(embed_url, timeout=30000)
            page.wait_for_timeout(10000)
        except Exception as e:
            print(f"    ⚠️ Gagal akses: {e}")
        
        browser.close()
        return found_m3u8["url"]

def run_scraper():
    print("🚀 Memulai ekstraksi & sinkronisasi semua data...")
    
    try:
        response = requests.get(API_URL).json()
        matches = response.get('data', [])
    except Exception as e:
        print(f"❌ Gagal koneksi API: {e}")
        return
    
    results = []
    for m in matches:
        # HAPUS ATAU KOMENTARI BARIS DI BAWAH INI:
        # if not m.get('is_live'):
        #     continue

        match_info = {
            "id": m.get('id'),
            "title": m.get('name'),
            "is_live": m.get('is_live'),
            "category": m.get('category', {}).get('name'), # Menambahkan kategori agar lebih jelas
            "begin_at": m.get('begin_at'),                # Menambahkan waktu mulai
            "streams": []
        }
        
        for s in m.get('streams', []):
            embed_url = s.get('url')
            print(f"🔍 Mencari stream: {m.get('name')}...")
            
            m3u8_raw = get_m3u8_from_embed(embed_url)
            
            if m3u8_raw:
                # Logika pembentukan Full URL
                parsed = urllib.parse.urlparse(m3u8_raw)
                path_with_query = f"{parsed.path}?{parsed.query}"
                m3u8_final = f"{WORKER_DOMAIN.rstrip('/')}{path_with_query}"
                
                match_info['streams'].append({
                    "lang": s.get('lang'),
                    "m3u8": m3u8_final
                })
        
        # Simpan semua data tanpa memfilter streams yang kosong
        results.append(match_info)
    
    # Simpan hasil akhir
    with open('full_matches_data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    print("\n🔥 Selesai! Semua data (Live & VOD) telah tersimpan.")
            
if __name__ == "__main__":
    run_scraper()
