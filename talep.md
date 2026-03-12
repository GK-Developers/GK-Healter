***GK Healter – Pardus kullanıcıları için disk temizleme, sağlık izleme ve güvenlik denetimi yapan masaüstü uygulama (Teknofest 2026 Geliştirme Kategorisi)***

**1. Yarışma ve Kategori Bilgisi**

- Yarışma: **Pardus Hata Yakalama ve Öneri Yarışması 2026**  
- Kategori: **Geliştirme Kategorisi**  
- Proje adı: **GK Healter**  
- Takım adı: *GK-Developers*  
- GitHub depo: `https://github.com/GK-Developers/gk-healter`

Bu talep, Teknofest 2026 kapsamında Geliştirme Kategorisi için geliştirilen **GK Healter** isimli Pardus odaklı masaüstü uygulamasının proje dosyası ve çıktılarının Pardus ekibine iletilmesi amacıyla açılmıştır.

---

**2. Projenin Amacı**

GK Healter, **Pardus ve Debian tabanlı sistemlerde:**

1. Sistem hatalarını tespit etmek ve iyileştirme önerileri sunmak (bozuk paketler, başarısız servisler, journal hataları vb.),
2. **Güvenlik zafiyetlerini** ortaya çıkarmak (SUID/SGID anormalleri, world‑writable izinler, zayıf SSH ayarları, sudoers riskleri, otomatik güncelleme durumu vb.),
3. Disk alanı yönetimini kolaylaştırmak (APT önbelleği, loglar, coredump’lar, tarayıcı önbellekleri),
4. Pardus’a özgü depo/servis/paket doğrulamalarını yapmak ve **Pardus kimliğini ispatlayabilen raporlar** üretmek,
5. Tüm bunları **güvenli ve denetlenebilir** bir şekilde, polkit üzerinden yetki yükseltme ve beyaz liste tabanlı silme yaklaşımı ile gerçekleştirmek

amacıyla geliştirilmiş bir **GTK masaüstü uygulamasıdır**.

---

**3. Pardus’a Özgü Katkılar**

Projede özellikle Pardus şartnamesiyle uyumlu olacak şekilde şu modüller yer almaktadır:

- **Pardus Depo Sağlık Kontrolü**  
  - `depo.pardus.org.tr` erişilebilirlik ve gecikme ölçümü  
  - APT kaynaklarının **mevcut Pardus sürümü ile uyumlu olup olmadığının** denetimi
- **Pardus Doğrulama Modülü (`pardus_verifier.py`)**  
  - `/etc/os-release`, `lsb_release`, donanım bilgisi, kurulu `pardus-`* paketleri, masaüstü ortamı ve hostname bilgisini toplayarak **jüriye sunulabilir doğrulama raporu** üretir.
- **Pardus Servis Tanılama**  
  - `pardus-`* ve `eta-*` servislerinin durumunun kontrolü, Pardus Yazılım Merkezi servislerinin analizi.
- **Pardus Depo Bozulması Tespiti**  
  - Yanlış sürüme işaret eden veya eksik güvenlik depolarını yakalayan kontroller.

Bu sayede proje, sadece genel bir sistem temizleyici değil, **Pardus ekosistemine özel bir “sağlık ve güvenlik” paneli** işlevi görür.

---

**4. Teknik Özellikler (Geliştirme Kategorisi açısından)**

- Dil: **Python 3 + PyGObject (GTK 3)**  
- Derleme / kurulum: **Meson** ve `Makefile`  
- Paketleme: **Debian (.deb), Flatpak, Arch (PKGBUILD), RPM (.spec)**  
- Yetki yükseltme: **Polkit (pkexec)** ile 5 ayrı güvenli eylem  
- Test altyapısı:
  - 200’ün üzerinde test fonksiyonu,  
  - %75+ satır kapsamı,  
  - GitHub Actions ile çoklu Python sürümü ve AppStream/desktop dosya doğrulaması,  
  - Güvenlik tarayıcısı (`security_scanner.py`), Pardus doğrulama (`pardus_verifier.py`) ve rapor üretici (`report_exporter.py`) için ayrı testler.

Kodlar tamamen **açık kaynak** ve halka açık bir repoda yer almaktadır:

- GitHub depo: `https://github.com/GK-Developers/gk-healter`

---

**5. Güvenlik ve Hata Yakalama Özellikleri (Şartname ile ilişkili)**

Proje, şartnamede belirtilen hata türlerine şu şekilde katkı sağlar:

- **Fonksiyonel Hatalar / Öneriler:**  
  - Bozuk paket / APT cache / dpkg lock tespiti, başarısız systemd servisleri, loglardaki hata sayıları.
- **Performans Hataları / Önerileri:**  
  - Büyük dosya ve log analizi, disk doluluk oranları, sistem sağlık puanı.
- **Kullanılabilirlik Hataları / Önerileri:**  
  - Temiz, Türkçe/İngilizce arayüz; tek tıkla tarama ve rapor alma; otomatik bakım zamanlamaları.
- **Güvenlik Zafiyetleri:**  
  - World‑writable dosyalar, beklenmeyen SUID/SGID binary’ler, sudoers `NOPASSWD: ALL` satırları, zayıf `sshd_config` ayarları, `unattended-upgrades` kurulu/etkin mi, başarısız giriş denemeleri.
- **Yerelleştirme:**  
  - Tam Türkçe ve İngilizce çeviri dosyaları (`en.json` / `tr.json`), Türkçe odaklı arayüz ve dokümantasyon.

---

**6. Docker Tabanlı Pardus Test Ortamı ve Kanıtlar**

Projeyi **zaafiyet içeren Pardus senaryolarında** test etmek için, resmi `pardus/yirmibes` imajı üzerinde çalışan bir Docker test ortamı hazırlanmıştır (`tests/docker/`):

- Çeşitli senaryolar (disk şişmesi, APT bozulması, SUID backdoor simülasyonu, repo bozulması, pseudo‑malware kalıcılığı vb.) konteyner içinde otomatik olarak koşturulmuş,  
- Her senaryo için GK Healter’ın ürettiği TXT/HTML/JSON raporları ve özet `*.manifest.json` dosyaları `artifacts/` altında saklanmıştır,  
- `GKHealter_DockerSecurityEvaluation_2026-03-11.md` dosyasında bu testlerin **detaylı teknik değerlendirmesi ve puanlaması** yer almaktadır. (Bu dosyayı ekte iletiyorum.)

Bu testler, uygulamanın özellikle **güvenlik denetimi ve Pardus’a özgü hata yakalama** açısından pratikte nasıl davrandığını göstermeyi amaçlıyor.

---

**7. Değerlendirme için yeniden üretilebilir adımlar**

Şartname gereği, talebin **yeniden üretilebilir** olması için aşağıdaki adımlar ile aynı çıktılar alınabilir.

**7.1. Kaynaktan kurulum / çalıştırma**

- Kurulum/derleme yönergeleri repo içinde `README.md` ve `README.tr.md` dosyalarında mevcuttur.
- Paketleme çıktıları (Deb/Flatpak/RPM/PKGBUILD) ilgili dizinlerde bulunmaktadır.

**7.2. Offline’a yakın Docker test akışı (önerilen)**

1) İmajı bir kez oluştur:

```bash
docker build -t gk-healter-test:pardus25 -f tests/docker/Dockerfile .
```

2) Konteyneri çalıştır, senaryoları koştur ve rapor üret:

```bash
docker run --rm -it --privileged -v /dev:/dev -v "$(pwd)":/workspace gk-healter-test:pardus25

# konteyner içinde:
bash tests/docker/run_all_scenarios.sh
ls -la /workspace/artifacts
```

3) Çıktılar:
- Her senaryo için ayrı `*.txt / *.html / *.json / *.manifest.json` raporları `artifacts/` altında oluşur.

**7.3. Kanıt/ekler (talep ekinde sunulması planlananlar)**

- `GKHealter_DockerSecurityEvaluation_2026-03-11.md` (İngilizce değerlendirme)
- `GKHealter_DockerSecurityEvaluation_2026-03-11.tr.md` (Türkçe değerlendirme)
- `artifacts/` klasöründen örnek senaryo raporları (en az 2–3 adet HTML + manifest)
- Uygulama arayüz ekran görüntüleri (`screenshots/` altındaki görseller)

Not: Docker imajının `*.tar` dışa aktarılan hali (offline taşınabilir artefact) boyut olarak büyük olabildiği için repoya eklenmemiştir; ihtiyaç halinde talep ekinde ayrıca paylaşılabilir veya releases sayfasından indirilebilir https://github.com/GK-Developers/gk-healter/releases/download/v0.1.7-pre/gk-healter-test_pardus25.tar.

---

**8. Beklentimiz**

Bu talep ile:

- GK Healter projesinin **Teknofest 2026 Pardus Hata Yakalama ve Öneri Yarışması – Geliştirme Kategorisi** kapsamında değerlendirilmesini,  
- Pardus ekibinin gerekli gördüğü ek geri bildirimleri paylaşmasını,  
- Uygun görülürse projenin ilerleyen dönemde Pardus deposu / Pardus Mağaza gibi kanallar üzerinden son kullanıcılara sunulabilmesi için yönlendirme yapılmasını

talep ediyoruz.

Proje ile ilgili her türlü teknik detay, ek dokümantasyon ve ekran görüntüleri ekte ve GitHub deposunda sunulmuştur.

Saygılarımızla,  
*Egehan KAHRAMAN, Mustafa GÖKPINAR (GK-Developers)*