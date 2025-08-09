from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
import requests
import logging
import re
import os

# Log ayarları - sadece hatalar için
logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def konfigurasyonu_yukle():
    """JSON dosyasından konfigürasyonu yükle"""
    try:
        with open("url.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config["chtid"], config["bt"], config["url"]
    except FileNotFoundError:
        logger.error("url.json dosyası bulunamadı!")
        return None, None, None
    except KeyError as e:
        logger.error(f"JSON dosyasında eksik anahtar: {e}")
        return None, None, None
    except json.JSONDecodeError:
        logger.error("JSON dosyası bozuk!")
        return None, None, None

def mesaj_gonder(bot_token, chat_id, mesaj):
    """Telegram'a mesaj gönder"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": mesaj}
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        return False

def fiyat_temizle(fiyat_text):
    """Fiyat metnini sayıya çevir"""
    if not fiyat_text:
        return None
    
    # Sadece sayıları ve virgülü al
    temiz_fiyat = re.sub(r'[^\d,.]', '', fiyat_text)
    temiz_fiyat = temiz_fiyat.replace(',', '.')
    
    try:
        return float(temiz_fiyat)
    except ValueError:
        return None

def onceki_fiyati_kaydet(fiyat):
    """Fiyatı dosyaya kaydet"""
    try:
        with open("onceki_fiyat.json", "w", encoding="utf-8") as f:
            json.dump({"fiyat": fiyat, "tarih": time.time()}, f)
    except Exception as e:
        pass

def onceki_fiyati_oku():
    """Önceki fiyatı dosyadan oku"""
    try:
        if os.path.exists("onceki_fiyat.json"):
            with open("onceki_fiyat.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("fiyat")
        return None
    except Exception as e:
        return None

def fiyat_karsilastir(yeni_fiyat, onceki_fiyat):
    """Fiyatları karşılaştır ve durum mesajı oluştur"""
    if onceki_fiyat is None:
        return "🆕 İlk fiyat kaydı", "bilgi"
    
    fark = yeni_fiyat - onceki_fiyat
    yuzde_fark = (fark / onceki_fiyat) * 100
    
    if fark < -0.01:  # Fiyat düştü
        return f"📉 FİYAT DÜŞTÜ!\n💰 Önceki: {onceki_fiyat:.2f} TL\n🔥 Şimdi: {yeni_fiyat:.2f} TL\n💸 İndirim: {abs(fark):.2f} TL (%{abs(yuzde_fark):.1f})", "dusus"
    elif fark > 0.01:  # Fiyat yükseldi
        return f"📈 Fiyat yükseldi\n💰 Önceki: {onceki_fiyat:.2f} TL\n📊 Şimdi: {yeni_fiyat:.2f} TL\n⬆️ Artış: {fark:.2f} TL (%{yuzde_fark:.1f})", "yukseli"
    else:  # Fiyat aynı
        return f"💰 Fiyat değişmedi: {yeni_fiyat:.2f} TL", "ayni"
    """Telegram'a mesaj gönder"""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {"chat_id": chat_id, "text": mesaj}
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            return True
        else:
            return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Mesaj gönderme hatası: {e}")
        return False

def tarayici_baslat():
    """Chrome tarayıcısını başlat"""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # Arka planda çalıştır
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    
    try:
        driver = webdriver.Chrome(options=options)
        return driver
    except Exception as e:
        logger.error(f"Tarayıcı başlatılamadı: {e}")
        return None

def fiyat_al(driver, url, fiyat_class_name="bWwoI8vknB6COlRVbpRj"):
    """Belirtilen URL'den fiyatı al"""
    try:
        driver.get(url)
        
        # Sayfanın yüklenmesini bekle
        wait = WebDriverWait(driver, 20)
        
        # Fiyat elementinin yüklenmesini bekle
        fiyat_element = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, fiyat_class_name))
        )
        
        fiyat = fiyat_element.text.strip()
        return fiyat
        
    except:
        return None

def main():
    """Ana fonksiyon"""
    # Konfigürasyonu yükle
    chat_id, bot_token, site_url = konfigurasyonu_yukle()
    
    if not all([chat_id, bot_token, site_url]):
        return
    
    # Tarayıcıyı başlat
    driver = tarayici_baslat()
    if not driver:
        return
    
    try:
        # Fiyatı al
        fiyat = fiyat_al(driver, site_url)
        
        if fiyat:
            # Fiyatı sayıya çevir
            yeni_fiyat_sayi = fiyat_temizle(fiyat)
            
            if yeni_fiyat_sayi:
                # Önceki fiyatı oku
                onceki_fiyat = onceki_fiyati_oku()
                
                # Fiyatları karşılaştır
                durum_mesaji, durum_tipi = fiyat_karsilastir(yeni_fiyat_sayi, onceki_fiyat)
                
                # Mesaj gönder
                mesaj_gonder(bot_token, chat_id, durum_mesaji)
                
                # Yeni fiyatı kaydet
                onceki_fiyati_kaydet(yeni_fiyat_sayi)
            else:
                hata_mesaji = "❌ Fiyat formatı anlaşılamadı."
                mesaj_gonder(bot_token, chat_id, hata_mesaji)
        else:
            hata_mesaji = "❌ Fiyat alınamadı. Site yapısı değişmiş olabilir."
            mesaj_gonder(bot_token, chat_id, hata_mesaji)
            
    except Exception as e:
        hata_mesaji = f"❌ Program hatası: {str(e)}"
        mesaj_gonder(bot_token, chat_id, hata_mesaji)
        
    finally:
        # Tarayıcıyı kapat
        driver.quit()

if __name__ == "__main__":
    # Railway için sürekli çalışım
    if os.getenv('RAILWAY_ENVIRONMENT'):
        while True:
            main()
            time.sleep(300)  # 5 dakika bekle
    else:
        # Local için tek seferlik
        main()