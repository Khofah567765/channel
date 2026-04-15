import json
import time
import requests
import hashlib
import re

def hash_id(string):
    return hashlib.sha256(string.encode()).hexdigest()[:16]

def run_scraper():
    print("🛰️ Memulai Scraper Kora (Mode Stealth)...")
    
    today_str = time.strftime("%Y-%m-%d")
    KORA_URL = f"https://ws.kora-api.space/api/matches/{today_str}/1"
    
    # Gunakan Session agar terlihat seperti browser asli yang menyimpan cookie
    session = requests.Session()
    
    # Header super lengkap mirip Chrome Windows
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9,id;q=0.8',
        'Referer': 'https://vsys.kora-top.zip/',
        'Origin': 'https://vsys.kora-top.zip/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
    })

    try:
        # Pancing dulu dengan akses halaman utama (opsional tapi membantu)
        res_main = session.get(KORA_URL, timeout=15).json()
        matches = res_main.get('matches', [])
    except Exception as e:
        print(f"❌ Gagal ambil daftar pertandingan: {e}")
        return

    channels_data = {}

    for m in matches:
        match_id = m.get('id')
        print(f"🔍 Mencari link: {m.get('home_en')} vs {m.get('away_en')}")
        
        link_stream = ""
        try:
            # Fetch detail
            detail_url = f"https://ws.kora-api.space/api/match/{match_id}"
            response = session.get(detail_url, timeout=15)
            
            # CEK APAKAH TERBLOKIR
            if "access denied" in response.text.lower():
                print(f"🚫 Terdeteksi Access Denied untuk ID {match_id}")
                continue
                
            res_detail = response.json()
            
            # Ambil link m3u8
            match_obj = res_detail.get('match', {})
            if match_obj.get('stream_url'):
                link_stream = match_obj['stream_url']
            elif res_detail.get('streams'):
                for s in res_detail['streams']:
                    url = s.get('url', '')
                    if url and 'm3u8' in url:
                        link_stream = url
                        break
            if not link_stream and match_obj.get('player_code'):
                found = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', match_obj['player_code'])
                if found: link_stream = found.group(1)

        except Exception as e:
            print(f"⚠️ Error pada ID {match_id}: {e}")

        clean_id = hash_id(f"{match_id}{today_str}kora")
        channels_data[clean_id] = {
            "channelName": f"{m.get('home_en')} vs {m.get('away_en')}",
            "contentType": "event_pertandingan",
            "status": "live" if link_stream else "scheduled",
            "streamUrl": link_stream,
            "referer": "https://vsys.kora-top.zip/",
            "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        }
        # Jeda agak lama agar tidak dicurigai bot
        time.sleep(2)

    final_output = {
        "category_name": "EVENT BEIN ARAB",
        "order": 2,
        "channels": channels_data
    }

    with open('kora_results.json', 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=4)
    
    print(f"✅ Selesai! {len(channels_data)} diproses.")

if __name__ == "__main__":
    run_scraper()
