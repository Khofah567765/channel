import json
import time
import requests
import hashlib
import re

def hash_id(string):
    return hashlib.sha256(string.encode()).hexdigest()[:16]

def run_scraper():
    print("🛰️ Memulai Scraper Kora Agresif...")
    
    today_str = time.strftime("%Y-%m-%d")
    # Gunakan endpoint web untuk memancing data lebih segar jika ada
    KORA_URL = f"https://ws.kora-api.space/api/matches/{today_str}/1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Referer': 'https://vsys.kora-top.zip/',
        'Origin': 'https://vsys.kora-top.zip/'
    }

    try:
        res_main = requests.get(KORA_URL, headers=headers, timeout=15).json()
        matches = res_main.get('matches', [])
    except Exception as e:
        print(f"❌ Gagal ambil daftar: {e}")
        return

    channels_data = {}

    for m in matches:
        match_id = m.get('id')
        print(f"🔍 Mencari link untuk: {m.get('home_en')} vs {m.get('away_en')} (ID: {match_id})")
        
        link_stream = ""
        try:
            # Fetch detail dengan timeout lebih santai
            detail_url = f"https://ws.kora-api.space/api/match/{match_id}"
            res_detail = requests.get(detail_url, headers=headers, timeout=15).json()
            
            # --- STRATEGI 1: Cek field stream_url langsung ---
            match_obj = res_detail.get('match', {})
            if match_obj.get('stream_url'):
                link_stream = match_obj['stream_url']
            
            # --- STRATEGI 2: Cek di dalam array streams ---
            if not link_stream and res_detail.get('streams'):
                for s in res_detail['streams']:
                    url = s.get('url', '')
                    if url and ('m3u8' in url or 'http' in url):
                        link_stream = url
                        break
            
            # --- STRATEGI 3: Ekstrak dari player_code (Iframe) ---
            if not link_stream and match_obj.get('player_code'):
                p_code = match_obj['player_code']
                # Cari pola URL m3u8 atau link source di dalam string HTML
                found = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', p_code)
                if not found:
                    found = re.search(r'src=["\'](https?://[^\s\'"]+)["\']', p_code)
                
                if found:
                    link_stream = found.group(1)

        except Exception as e:
            print(f"⚠️ Detail error untuk ID {match_id}: {e}")

        clean_id = hash_id(f"{match_id}{today_str}kora")
        
        # Tentukan status berdasarkan apakah link ditemukan
        status_text = "live" if link_stream else "scheduled"

        channels_data[clean_id] = {
            "channelName": f"{m.get('home_en')} vs {m.get('away_en')}",
            "contentType": "event_pertandingan",
            "status": status_text,
            "streamUrl": link_stream,
            "referer": "https://vsys.kora-top.zip/",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        # Jeda 1.5 detik agar tidak dianggap spamming
        time.sleep(1.5)

    final_output = {
        "category_name": "EVENT BEIN ARAB",
        "order": 2,
        "channels": channels_data
    }

    with open('kora_results.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4)
    
    print(f"✅ Selesai! {len(channels_data)} pertandingan diproses.")

if __name__ == "__main__":
    run_scraper()
