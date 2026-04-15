import requests

def test():
    match_id = "29623" # ID dari log kamu tadi
    url = f"https://ws.kora-api.space/api/match/{match_id}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://vsys.kora-top.zip/'
    }
    
    response = requests.get(url, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text[:500]}") # Liat 500 karakter pertama

if __name__ == "__main__":
    test()
  
