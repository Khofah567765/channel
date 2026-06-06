import os
import json
import urllib.parse
import requests
import time
from datetime import datetime
import pytz
from playwright.sync_api import sync_playwright

# Konfigurasi
WORKER_DOMAIN = os.environ.get("WORKER_DOMAIN", "https://default-domain.workers.dev")
API_URL = "https://ws.kora-api.space/api/matches/"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"

def convert_to_wib(utc_time_str):
    """Mengonversi string waktu UTC ke format WIB yang mudah dibaca."""
    try:
        # Parse string waktu dari API
        utc_dt = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ")
        utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
        # Konversi ke WIB
        wib_tz = pytz.timezone("Asia/Jakarta")
        wib_dt = utc_dt.astimezone(wib_tz)
        return wib_dt.strftime("%d-%m-%Y %H:%M WIB")
    except:
        return utc_time_str

def get_m3u8_from_embed(embed_url):
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            found_m3u8 = {"url": None}
            def on_request(request):
                if ".m3u8" in request.url and "st=" in request.url:
                    found_m3u8["url"] = request.url

            page.on("request", on_request)
            page.goto(embed_url, timeout=30000)
            page.wait_for_timeout(5000)
            return found_m3u8["url"]
    except:
        return None
    finally:
        if browser:
            browser.close()

def run_scraper():
    print("🚀 Memulai ekstraksi & sinkronisasi data dengan WIB...")
    
    try:
        response = requests.get(API_URL).json()
        matches = response.get('data', [])
    except Exception as e:
        print(f"❌ Gagal koneksi API: {e}")
        return
    
    results = []
    for m in matches:
       # Ambil data kategori
        category_data = m.get('category', {})
        
        match_info = {
            "id": m.get('id'),
            "title": m.get('name'),
            "is_live": m.get('is_live'),
            "category": category_data.get('name'),
            "category_image": category_data.get('image'), # Tambahkan ini
            "waktu_wib": convert_to_wib(m.get('begin_at')),
            "logo_t1": m.get('logo_team1'),
            "logo_t2": m.get('logo_team2'),
            "streams": []
        }
        
        for s in m.get('streams', []):
            embed_url = s.get('url')
            m3u8_raw = get_m3u8_from_embed(embed_url)
            
            if m3u8_raw:
                parsed = urllib.parse.urlparse(m3u8_raw)
                path_with_query = f"{parsed.path}?{parsed.query}"
                m3u8_final = f"{WORKER_DOMAIN.rstrip('/')}{path_with_query}"
                
                match_info['streams'].append({"lang": s.get('lang'), "m3u8": m3u8_final})
            
            time.sleep(2)
        
        results.append(match_info)
    
    with open('full_matches_data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    print("\n🔥 Selesai! Data tersimpan dengan format waktu WIB & logo.")

if __name__ == "__main__":
    run_scraper()
