import os
import json
import urllib.parse
import requests
import time
from datetime import datetime, timedelta
import pytz
from playwright.sync_api import sync_playwright

# --- KONFIGURASI ---
# Pastikan Anda sudah mengatur variable ini di GitHub Secrets
WORKER_DOMAIN = os.getenv("WORKER_DOMAIN")
API_URL = os.getenv("API_URL")

# URL Firebase Realtime Database Anda (ganti dengan milik Anda)
# Pastikan URL diakhiri dengan /matches.json
FIREBASE_URL = "https://webkumy-default-rtdb.asia-southeast1.firebasedatabase.app/matches.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36"

# Pengecekan keamanan
if not WORKER_DOMAIN or not API_URL:
    print("❌ Error: WORKER_DOMAIN atau API_URL belum diset di environment secret!")
    exit(1)

def convert_to_wib(utc_time_str):
    try:
        utc_dt = datetime.strptime(utc_time_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.UTC)
        wib_dt = utc_dt.astimezone(pytz.timezone("Asia/Jakarta"))
        wib_dt = wib_dt - timedelta(hours=1)
        return wib_dt.strftime("%d-%m-%Y %H:%M WIB")
    except:
        return utc_time_str

def get_tanggal(utc_time_str):
    try:
        return utc_time_str.split('T')[0]
    except:
        return None

def get_m3u8_from_browser(browser, embed_url):
    found_m3u8 = {"url": None}
    page = browser.new_context(user_agent=USER_AGENT).new_page()
    page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    def on_request(request):
        if ".m3u8" in request.url and "st=" in request.url:
            found_m3u8["url"] = request.url

    page.on("request", on_request)
    try:
        page.goto(embed_url, timeout=30000)
        page.wait_for_timeout(5000)
    except:
        pass
    finally:
        page.close()
    return found_m3u8["url"]

def upload_to_firebase(data):
    """Mengirim data JSON ke Firebase Realtime Database"""
    try:
        response = requests.put(FIREBASE_URL, json=data)
        if response.status_code == 200:
            print("✅ Data berhasil tersinkronisasi ke Firebase!")
        else:
            print(f"❌ Gagal kirim ke Firebase: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error koneksi ke Firebase: {e}")

def run_scraper():
    print("🚀 Memulai ekstraksi & sinkronisasi data...")
    
    try:
        response = requests.get(API_URL).json()
        matches = response.get('data', [])
    except Exception as e:
        print(f"❌ Gagal koneksi API: {e}")
        return

    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for m in matches:
            category_data = m.get('category', {})
            begin_at = m.get('begin_at', "")
            
            match_info = {
                "id": m.get('id'),
                "title": m.get('name'),
                "is_live": m.get('is_live'),
                "category": category_data.get('name'),
                "category_image": category_data.get('image'),
                "tanggal_pertandingan": get_tanggal(begin_at),
                "waktu_wib": convert_to_wib(begin_at),
                "logo_t1": m.get('logo_team1'),
                "logo_t2": m.get('logo_team2'),
                "streams": []
            }
            
            for s in m.get('streams', []):
                embed_url = s.get('url')
                print(f"🔍 Mencari: {m.get('name')}...")
                
                m3u8_raw = get_m3u8_from_browser(browser, embed_url)
                
                if m3u8_raw:
                    parsed = urllib.parse.urlparse(m3u8_raw)
                    path_with_query = f"{parsed.path}?{parsed.query}"
                    m3u8_final = f"{WORKER_DOMAIN.rstrip('/')}{path_with_query}"
                    
                    match_info['streams'].append({"lang": s.get('lang'), "m3u8": m3u8_final})
                
                time.sleep(2)
            
            results.append(match_info)
        
        browser.close()

    # Simpan ke file lokal (sebagai backup)
    with open('full_matches_data.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4)
    print("\n🔥 Selesai! Data tersimpan di full_matches_data.json")
    
    # Kirim ke Firebase
    upload_to_firebase(results)

if __name__ == "__main__":
    run_scraper()
