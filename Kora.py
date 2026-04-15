import json
import time
import requests
import hashlib

def hash_id(string):
    return hashlib.sha256(string.encode()).hexdigest()[:16]

def run_scraper():
    print("🛰️ Memulai Scraper Kora (Output: Local File)...")
    
    today_str = time.strftime("%Y-%m-%d")
    KORA_URL = f"https://ws.kora-api.space/api/matches/{today_str}/1"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://vsys.kora-top.zip/'
    }

    try:
        # 1. Ambil daftar match
        res_main = requests.get(KORA_URL, headers=headers, timeout=15).json()
        matches = res_main.get('matches', [])
    except Exception as e:
        print(f"❌ Gagal ambil daftar: {e}")
        return

    channels_data = {}

    for m in matches:
        match_id = m.get('id')
        print(f"🔍 Fetching ID: {match_id}")
        
        link_stream = ""
        try:
            # 2. Ambil detail link
            res_detail = requests.get(f"https://ws.kora-api.space/api/match/{match_id}", headers=headers, timeout=15).json()
            
            if res_detail.get('match', {}).get('stream_url'):
                link_stream = res_detail['match']['stream_url']
            elif res_detail.get('streams'):
                streams = res_detail['streams']
                m3u8 = next((s['url'] for s in streams if 'm3u8' in s.get('url', '')), None)
                link_stream = m3u8 if m3u8 else (streams[0].get('url') if streams else "")
            elif res_detail.get('match', {}).get('player_code'):
                import re
                found = re.search(r'http[^"\']+\.m3u8', res_detail['match']['player_code'])
                if found: link_stream = found.group(0)
        except:
            pass

        clean_id = hash_id(f"{match_id}{today_str}kora")
        
        # Susun data sesuai struktur yang kamu inginkan
        channels_data[clean_id] = {
            "channelName": f"{m.get('home_en')} vs {m.get('away_en')}",
            "contentType": "event_pertandingan",
            "status": "live" if link_stream else "scheduled",
            "streamUrl": link_stream,
            "referer": "https://vsys.kora-top.zip/",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        time.sleep(1) # Jeda sopan

    # Gabungkan ke struktur final
    final_output = {
        "category_name": "EVENT BEIN ARAB",
        "order": 2,
        "channels": channels_data
    }

    # 3. Simpan ke file JSON
    with open('kora_results.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4)
    
    print(f"✅ Selesai! {len(channels_data)} match disimpan ke kora_results.json")

if __name__ == "__main__":
    run_scraper()
