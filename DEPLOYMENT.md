# 🖥️ Wdrożenie: Mac mini M2 (Server) + Domena na home.pl

Twoja konfiguracja sprzętowa (**Mac mini z procesorem M2 i 24 GB RAM**, włączony 24/7) to idealny, potężny i darmowy serwer pod ten projekt. Zamiast płacić 100–300 zł miesięcznie za chmurę AWS czy dedykowany VPS, Mac mini bez trudu obsłuży scraping, indeksowanie bazy, modele AI oraz serwer FastAPI.

---

## 🏛️ Architektura rozwiązania

```
[ Klient w Internecie (Telefon / Komputer) ]
                     │
                     ▼
        [ Domena na home.pl ]
                     │
                     ▼ (Bezpieczny tunel HTTPS - Cloudflare Tunnel)
                     │
    ┌────────────────┴────────────────────────┐
    │          Mac mini M2 (24/7)             │
    │                                         │
    │  • FastAPI (port 8000)                  │
    │    - Web UI (Single Page App)           │
    │    - REST API (/api/basket, /api/search)│
    │                                         │
    │  • Scheduler (06:00 rano)               │
    │    - Pobieranie świeżych gazetek        │
    │    - Ekstrakcja i aktualizacja bazy     │
    │                                         │
    │  • Baza danych (SQLite + FTS5)          │
    └─────────────────────────────────────────┘
```

---

## 🚀 Krok 1: Uruchomienie usług na Macu mini jako procesy w tle

Przygotowany skrypt `deploy/setup_mac_mini.sh` konfiguruje natywne usługi systemowe macOS (`launchd`). Dzięki temu serwer API i poranny scheduler działają w tle i **uruchamiają się automatycznie nawet po restarcie komputera**.

```bash
# Wejdź do katalogu projektu
cd ~/Desktop/Prokjekty_github/przegladanie_gazetek

# Wygeneruj konfigurację launchd
./deploy/setup_mac_mini.sh

# Włącz usługi w systemie macOS
launchctl load ~/Library/LaunchAgents/com.gazetkoagent.api.plist
launchctl load ~/Library/LaunchAgents/com.gazetkoagent.scheduler.plist
```

Sprawdzenie w przeglądarce na Macu: wejdź na [http://localhost:8000](http://localhost:8000) – zobaczysz działającą aplikację!

---

## 🌐 Krok 2: Wystawienie Maca mini na świat i połączenie z home.pl

Najbezpieczniejszym i w 100% darmowym sposobem na połączenie Maca mini z domeną na home.pl jest **Cloudflare Tunnel (`cloudflared`)**.

### Dlaczego Cloudflare Tunnel?
- **Nie musisz mieć publicznego ani stałego IP** od operatora internetu.
- **Nie musisz otwierać portów na domowym routerze** (bezpieczeństwo Twojej sieci domowej).
- Zapewnia **automatyczny, darmowy certyfikat SSL (HTTPS)** i ochronę przed atakami DDoS.

### Instrukcja w 3 krokach:

1. **Instalacja `cloudflared` na Macu mini**:
   ```bash
   brew install cloudflared
   ```

2. **Szybki start (darmowy tunel tymczasowy lub z domeną)**:
   Możesz natychmiast odpalić publiczny adres HTTPS poleceniem:
   ```bash
   cloudflared tunnel --url http://localhost:8000
   ```
   Otrzymasz publiczny link `https://xxx.trycloudflare.com`, który działa na całym świecie (w telefonie, u znajomych).

3. **Podpięcie Twojej domeny z home.pl**:
   - W panelu Cloudflare (darmowe konto) dodajesz swoją domenę z home.pl (zmieniając DNS-y w home.pl na Cloudflare).
   - Wpisujesz jedno polecenie:
     ```bash
     cloudflared tunnel route dns moje-gazetki api.twojadomena.pl
     ```
   - Twoja domena `api.twojadomena.pl` lub `twojadomena.pl` automatycznie przekierowuje cały ruch szyfrowanym tunelem prosto do Twojego Maca mini!

---

## 📁 Krok 3: Opcja z frontendem na hostingu home.pl

Jeśli wolisz, aby sam plik HTML był hostowany na Twoim tradycyjnym serwerze FTP w home.pl:
1. Skopiuj plik [web/index.html](file:///Users/jakubmadejski/Desktop/Prokjekty_github/przegladanie_gazetek/web/index.html) do katalogu `public_html` na swoim serwerze home.pl.
2. W pliku `index.html` zmień linię:
   ```javascript
   const API_BASE = "https://twoj-tunel-mac-mini.twojadomena.pl";
   ```
3. Użytkownicy wchodzą na Twoją stronę w home.pl, a zapytania o promocje lecą do potężnego Maca mini w Twoim pokoju!
