**PiWebArchiver** - **Web Sayfası Yedekleme Aracı**


| Versiyon: 1.0.0 | Lisans: MIT | Python 3.10+  |  Flask |
| - | - | - |



## **Nedir?**

WebArchiver, herhangi bir web sayfasını tüm bileşenleriyle birlikte yerel diskinize yedeklemenizi sağlayan açık kaynaklı bir Python aracıdır. HTML, CSS, JavaScript, görseller, fontlar ve diğer medya dosyalarını tek bir arşive paketler.

İndirilen arşiv internet bağlantısı olmadan çevrimdışı ortamda da tam olarak çalışır; çünkü tüm harici URL'ler otomatik olarak yerel dosya yollarına dönüştürülür.


| **Temel Özellikler** HTML + tüm varlıklar (CSS, JS, görseller, fontlar, video, ses)  •  Çevrimdışı çalışan arşiv  •  ZIP ve TAR.GZ çıktısı  •  Derin tarama modu (alt sayfalar)  •  Gerçek zamanlı ilerleme takibi  •  Modern web arayüzü |
| - |



## **Kurulum**

### **Gereksinimler**

- Python 3.10 veya üzeri

- pip (Python paket yöneticisi)

- İnternet bağlantısı (yalnızca çalışma zamanında)


### **1. Projeyi İndirin**

git clone https://github.com/sizin-repo/webarchiver.git

cd webarchiver


### **2. Bağımlılıkları Kurun**

Normal kurulum:

pip install -r requirements.txt


Fedora / Arch Linux gibi sistem Python kullanan dağıtımlar için:

pip install -r requirements.txt --break-system-packages


veya sanal ortam (önerilen):

python -m venv venv

source venv/bin/activate          \# Linux / macOS

venv\\Scripts\\activate.bat        \# Windows

pip install -r requirements.txt


### **3. Başlatın**

python app.py


Tarayıcınızda şu adresi açın:

http://localhost:5000



## **Kullanım Kılavuzu**

### **Adım Adım**

1. Tarayıcıda http://localhost:5000 adresini açın.

2. "Hedef URL" alanına yedeklemek istediğiniz web sayfasının adresini girin.

3. Çıktı formatını seçin: ZIP (varsayılan) veya TAR.GZ.

4. İsteğe bağlı olarak "Derin Tarama" seçeneğini etkinleştirin.

5. "Arşivle" butonuna tıklayın ve ilerleme çubuğunu izleyin.

6. İşlem tamamlandığında "İndir" butonuna tıklayın.


### **Seçenekler**

**ZIP Formatı**

Tüm platformlarda desteklenen evrensel sıkıştırma formatı. Çift tıkla açılır. Küçük ve orta ölçekli arşivler için idealdir.


**TAR.GZ Formatı**

Linux ve macOS sistemlerde yaygın olarak kullanılan format. Sunucu yedekleme ve otomasyon senaryoları için tercih edilir. Unix izinlerini korur.


**Derin Tarama**

Etkinleştirildiğinde araç, hedef sayfadaki linkleri takip ederek aynı domain içindeki en fazla 20 alt sayfayı da arşivler. Blog, dokümantasyon sitesi veya çok sayfalı içeriklerin tamamını yedeklemek için kullanılır.



## **Proje Yapısı**

webarchiver/

├── app.py               \# Flask sunucu ve yedekleme motoru

├── requirements.txt     \# Python bağımlılıkları

├── templates/

│   └── index.html       \# Web arayüzü

└── downloads/           \# Arşivler burada oluşturulur (otomatik)



## **API Referansı**

WebArchiver bir REST API sunar. Otomasyon ve entegrasyon için kullanabilirsiniz.


| **Endpoint** | **Metod** | **Açıklama** |
| - | - | - |
| / | GET | Web arayüzünü sunar |
| /api/backup | POST | Yeni yedekleme işi başlatır. Body: \{ url, format, deep \} |
| /api/status/\<id\> | GET | İş durumunu ve ilerlemeyi sorgular |
| /api/download/\<id\> | GET | Tamamlanan arşivi indirir |


### **Örnek API Çağrısı (curl)**

curl -X POST http://localhost:5000/api/backup \\

     -H "Content-Type: application/json" \\

     -d '\{"url":"https://example.com","format":"zip","deep":false\}'



## **Kullanım Alanları**


| **Kişisel Arşivleme ve Koleksiyon** **Blog yazıları, haberler, referans sayfaları** Beğendiğiniz içerikleri, okumak istediğiniz makaleleri ya da ileride kaybolabilecek web sayfalarını kalıcı olarak yerel diskinize kaydedin. İnternet arşivine alternatif kişisel koleksiyon oluşturun. |
| - |


| **Tasarım ve Geliştirici Referansı** **UI/UX örnekleri, kod parçacıkları, teknik dokümantasyon** İlham aldığınız web tasarımlarını, renk paletlerini ve bileşen örneklerini arşivleyin. Çevrimdışı ortamda inceleyebilir, tekrar kullanabilirsiniz. |
| - |


| **Eğitim ve Araştırma** **Ders materyalleri, akademik içerik, kütüphane kaynakları** Öğrenciler ve araştırmacılar için ders notlarını, online kaynak sayfalarını veya kütüphane veri tabanlarındaki içerikleri çevrimdışı erişim için yedekleyin. |
| - |


| **Hukuki Delil ve Belgeleme** **Ekran görüntüsü yerine tam sayfa arşiv, zaman damgası** Hukuki süreçlerde ya da kurumsal belgelemelerde web sayfalarının orijinal haline ilişkin tam arşiv oluşturun. HTML kodunu, meta verileri ve zaman damgasını korur. |
| - |


| **SEO ve Rakip Analizi** **Rakip site yapısı, içerik stratejisi, backlink analizi** Rakip web sitelerinin yapısını, içeriklerini ve teknik detaylarını arşivleyerek zaman içindeki değişimleri takip edin. |
| - |


| **Felaket Kurtarma ve Site Yedekleme** **Sunucu kaybı, hosting sorunları, migration desteği** Kendi web sitenizin tam kopyasını periyodik olarak yedekleyin. Hosting kaynaklı sorunlarda, sunucu göçü senaryolarında veya site kazalarında geri dönüş noktası oluşturun. |
| - |


| **Çevrimdışı Okuma ve Erişim** **Uçak modu, sınırlı bağlantı, uzak lokasyonlar** Uzun yolculuklar, internet erişiminin kısıtlı olduğu bölgeler veya yüksek veri maliyetli ortamlar için web içeriklerini önceden indirin. |
| - |



## **Bilinen Kısıtlamalar**

- Login gerektiren veya oturum korumalı sayfalar arşivlenemez.

- JavaScript ile dinamik olarak yüklenen içerikler (Single Page Application) tam olarak yakalanamayabilir.

- Cloudflare veya benzeri WAF koruması olan siteler erişimi engelleyebilir.

- Çok büyük siteler (binlerce sayfa) için derin tarama sınırı 20 alt sayfa ile kısıtlıdır.

- Video akış platformlarındaki (YouTube, Netflix) DRM korumalı içerikler indirilemez.



## **Lisans**

| **MIT Lisansı** Copyright (c) 2025 WebArchiver Katkıda Bulunanları Bu yazılımın ve ilgili dokümantasyon dosyalarının ("Yazılım") bir kopyasını edinen herkese, Yazılımı herhangi bir kısıtlama olmaksızın kullanma, kopyalama, değiştirme, birleştirme, yayımlama, dağıtma, alt lisanslama ve/veya satma hakları da dahil olmak üzere ücretsiz olarak izin verilmektedir. Yazılımın tüm kopyalarına veya önemli bölümlerine yukarıdaki telif hakkı bildirimi ve bu izin bildirimi dahil edilmelidir. YAZILIM "OLDUĞU GİBİ" SAĞLANMAKTADIR; AÇIK VEYA ZIMNİ HERHANGİ BİR GARANTİ VERİLMEMEKTEDİR. HİÇBİR DURUMDA YAZARLAR VEYA TELİF HAKKI SAHİPLERİ HERHANGİ BİR TALEP, HASAR VEYA DİĞER YÜKÜMLÜLÜKLERDEN SORUMLU TUTULAMAZ. |
| - |


### **Üçüncü Taraf Lisansları**

| **Kütüphane** | **Lisans** | **Kullanım Amaci** |
| - | - | - |
| Flask | BSD-3-Clause | Web sunucu framework'u |
| Requests | Apache 2.0 | HTTP istek kütüphanesi |
| BeautifulSoup4 | MIT | HTML ayrıştırma motoru |
| lxml | BSD | Hızlı XML/HTML işleme |
| Flask-CORS | MIT | CORS başlık yönetimi |



## **Katkida Bulunma**

Katkılarınızı memnuniyetle karşılıyoruz. Lütfen aşağıdaki adımları izleyin:

7. Depoyu fork edin.

8. Yeni bir dal oluşturun: git checkout -b ozellik/yeni-ozellik

9. Değişikliklerinizi commitleyin: git commit -m 'feat: yeni özellik ekle'

10. Dalınızı push edin: git push origin ozellik/yeni-ozellik

11. Pull Request açın ve değişikliklerinizi açıklayın.


Hata bildirimleri için lütfen GitHub Issues sayfasını kullanın ve mümkünse yeniden üretme adımlarını ekleyin.



## **Destek ve Iletisim**

- GitHub Issues: github.com/sizin-repo/webarchiver/issues

- Dokümantasyon: github.com/sizin-repo/webarchiver/wiki


PiWebArchiver  —  Açık Kaynak  —  MIT Lisansı  —  2026
