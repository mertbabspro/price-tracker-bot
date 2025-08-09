import time
import json
import requests
import re
import os

def mesaj_gonder(bot_token, chat_id, mesaj):
    """Telegram'a mesaj gönder"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": mesaj}
        response = requests.post(url, data=data, timeout=10)
        return response.status_code == 200
    except:
        return False

def hepsiburada_fiyat_al(url):
    """Hepsiburada'dan fiyat al"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        html = response.text
        
        # Hepsiburada fiyat pattern'leri
        patterns = [
            r'"currentPrice":"([\d,]+\.?\d*)"',
            r'"price":"([\d,]+\.?\d*)"',
            r'data-bind="text: currentPriceBeforePoint"[^>]*>(\d+)',
            r'currentPrice[^>]*>[\s]*(\d{1,3}(?:[.,]\d{3})*)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html)
            if match:
                fiyat_str = match.group(1).replace(',', '')
                try:
                    return float(fiyat_str)
                except:
                    continue
        
        return None
    except:
        return None

def fiyat_kaydet(fiyat):
    """Fiyatı kaydet"""
    try:
        with open("onceki_fiyat.txt", "w") as f:
            f.write(str(fiyat))
    except:
        pass

def fiyat_oku():
    """Önceki fiyatı oku"""
    try:
        if os.path.exists("onceki_fiyat.txt"):
            with open("onceki_fiyat.txt", "r") as f:
                return float(f.read().strip())
        return None
    except:
        return None

def main():
    # Sabit değerler
    CHAT_ID = "6805362332"
    BOT_TOKEN = "8006318166:AAF0GcJfrTDfqAip-I3kavgv9kvtNgLOh5s"
    URL = "https://www.hepsiburada.com/madame-coco-benard-6-kisilik-12-parca-kahve-fincan-seti-beyaz-110-ml-p-HBCV000079PQO1"
    
    try:
        # Yeni fiyatı al
        yeni_fiyat = hepsiburada_fiyat_al(URL)
        
        if yeni_fiyat:
            # Önceki fiyatı oku
            onceki_fiyat = fiyat_oku()
            
            if onceki_fiyat is None:
                # İlk kayıt
                mesaj = f"🆕 Fiyat takibi başladı!\n💰 Mevcut fiyat: {yeni_fiyat:.2f} TL"
                mesaj_gonder(BOT_TOKEN, CHAT_ID, mesaj)
            else:
                # Fiyat karşılaştır
                fark = yeni_fiyat - onceki_fiyat
                
                if fark < -0.5:  # 50 kuruş düşmüş
                    yuzde = abs(fark / onceki_fiyat * 100)
                    mesaj = f"📉 FİYAT DÜŞTÜ! 🔥\n\n💰 Önceki: {onceki_fiyat:.2f} TL\n🎯 Şimdi: {yeni_fiyat:.2f} TL\n💸 İndirim: {abs(fark):.2f} TL (%{yuzde:.1f})"
                    mesaj_gonder(BOT_TOKEN, CHAT_ID, mesaj)
                elif fark > 0.5:  # 50 kuruş yükselmiş
                    yuzde = fark / onceki_fiyat * 100
                    mesaj = f"📈 Fiyat yükseldi\n\n💰 Önceki: {onceki_fiyat:.2f} TL\n📊 Şimdi: {yeni_fiyat:.2f} TL\n⬆️ Artış: {fark:.2f} TL (%{yuzde:.1f})"
                    mesaj_gonder(BOT_TOKEN, CHAT_ID, mesaj)
            
            # Yeni fiyatı kaydet
            fiyat_kaydet(yeni_fiyat)
        else:
            # Fiyat alınamadı
            mesaj = "❌ Fiyat alınamadı. Site erişilemeyebilir."
            mesaj_gonder(BOT_TOKEN, CHAT_ID, mesaj)
            
    except Exception as e:
        mesaj = f"❌ Hata: {str(e)}"
        mesaj_gonder(BOT_TOKEN, CHAT_ID, mesaj)

if __name__ == "__main__":
    # Railway'de sürekli çalış
    while True:
        main()
        time.sleep(300)  # 5 dakika bekle