import json
import time
import requests
import hashlib
import base64
import re

def hash_id(string):
    return hashlib.md5(string.encode()).hexdigest()

def get_high_quality_link(session, master_url):
    try:
        res = session.get(master_url, timeout=5)
        if "#EXT-X-STREAM-INF" in res.text:
            lines = res.text.split('\n')
            best_url = master_url
            max_bandwidth = 0
            for i in range(len(lines)):
                if "BANDWIDTH" in lines[i]:
                    bw_match = re.search(r'BANDWIDTH=(\d+)', lines[i])
                    if bw_match and int(bw_match.group(1)) > max_bandwidth:
                        max_bandwidth = int(bw_match.group(1))
                        v_url = lines[i + 1].strip()
                        best_url = v_url if v_url.startswith("http") else master_url.rsplit('/', 1)[0] + '/' + v_url
            return best_url
    except:
        pass
    return master_url

def run_scraper():
    print("🚀 Memulai Scraper Kora (Logika VS Code: Base64 + Frame)...")
    
    now = time.time()
    today_query = time.strftime("%Y-%m-%d") # Asia/Jakarta UTC+7
    
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://vsys.kora-top.zip/',
        'Origin': 'https://vsys.kora-top.zip'
    }
    session.headers.update(headers)

    try:
        # 1. Ambil Jadwal
        res = session.get(f"https://ws.kora-api.space/api/matches/{today_query}/1").json()
        matches = res.get('matches', [])
    except Exception as e:
        print(f"❌ Error Jadwal: {e}")
        return

    channels_data = {}

    for m in matches:
        home = m.get('home_en', 'Home')
        away = m.get('away_en', 'Away')
        match_id = m.get('id')
        
        final_stream_url = ""
        print(f"🔍 Memproses: {home} vs {away}...")

        try:
            # 2. Ambil Detail Match (Logika detailRes)
            detail_res = session.get(f"https://kora-api.space/api/matche/{match_id}/ar").json()
            channels = detail_res.get('channels', [])
            
            if channels:
                ch_data = channels[0]
                ch_key = ch_data.get('ch') or ch_data.get('key')
                
                if not ch_key and ch_data.get('mobile_link'):
                    php_match = re.search(r'\/([^\/]+)\.php', ch_data['mobile_link'])
                    if php_match: ch_key = php_match.group(1)

                if ch_key:
                    # 3. Ambil Token dari frame.php
                    frame_url = f"https://vsys.kora-top.zip/frame.php?ch={ch_key}&p=12"
                    frame_res = session.get(frame_url)
                    token_match = re.search(r'token\s*:\s*"([^"]+)"', frame_res.text, re.IGNORECASE)
                    
                    if token_match:
                        # 4. Decode Base64 Token
                        decoded = base64.b64decode(token_match.group(1)).decode('utf-8')
                        if "/.m3u8" in decoded:
                            decoded = decoded.replace("/.m3u8", f"/{ch_key}.m3u8")
                        
                        # 5. Cari Kualitas Tertinggi
                        final_stream_url = get_high_quality_link(session, decoded)

        except Exception as e:
            print(f"⚠️ Gagal pada ID {match_id}: {e}")

        # ID hash sesuai logic JS kamu
        clean_id = hash_id(f"match_{match_id}_{today_query}")
        
        channels_data[clean_id] = {
            "channelName": f"{home} vs {away}",
            "contentType": "event_pertandingan",
            "streamUrl": final_stream_url,
            "status": "live" if final_stream_url else "scheduled",
            "team1Logo": f"https://img.kora-api.space/uploads/team/{m.get('home_logo')}" if m.get('home_logo') else "",
            "team2Logo": f"https://img.kora-api.space/uploads/team/{m.get('away_logo')}" if m.get('away_logo') else "",
            "referer": "https://vsys.kora-top.zip/",
            "userAgent": headers['User-Agent']
        }
        time.sleep(1)

    # Simpan Hasil
    output = {
        "category_name": "EVENT BEIN ARAB",
        "order": 2,
        "channels": channels_data
    }
    
    with open('kora_results.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)
    print(f"🔥 Selesai! File kora_results.json diperbarui.")

if __name__ == "__main__":
    run_scraper()
