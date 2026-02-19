# CatchBot by MyNameIsKillua
## Beta Version 2.5

Ein Discord Self-Bot für automatisches Pokemon Hunting in PokéMeow.

⚠️ **WICHTIGER HINWEIS:** Self-Bots verstoßen gegen die Discord Terms of Service und können zu einem permanenten Account-Ban führen. Nutze diesen Bot auf eigene Verantwortung!

**Multi-Account erhöht das Ban-Risiko deutlich, weil:**

**IP-Verknüpfung:** Discord verbindet alle Accounts über deine IP - wird einer erkannt, fliegen alle gleichzeitig ("Chain-Ban").

**Auffälliges Muster:** Mehrere Accounts mit identischem, automatisiertem Verhalten zur gleichen Zeit sind extrem leicht zu erkennen.

**Mehr API-Traffic:** Jeder zusätzliche Account multipliziert die Anfragen und triggert Rate-Limits/Flags schneller.

**Grobe Einschätzung:**

| Setup | Relatives Risiko
|-----|-----
| 1 Account, vorsichtig | Basis
| 2-3 Accounts, gleiche IP | ca. 2-3x höher
| 5+ Accounts, gleiche IP | deutlich höher
| Viele Accounts, ohne Proxy/Cooldown | sehr hoch

---

## 📋 Features

- ✅ Automatische Daily-Tasks (;daily, ;h, ;swap, ;q)
- ✅ Automatisches Pokemon Hunting (;p mit zufälligen Intervallen)
- ✅ Halb Automatisches Fischen (;f)
- ✅ **Auto-Catch basierend auf Rarity** 🎯
  - Erkennt Pokemon-Rarity automatisch
  - Klickt passenden Ball-Button (Pokeball, Greatball, Ultraball, Masterball)
  - **Pokemon-Name** wird erkannt und im Log angezeigt (via `Pokemon_Names.txt`)
  - **Farbige Konsolen-Ausgabe** pro Rarity + **Catch-Result** (✅/❌)
- ✅ **Multi-Account Launcher** 🚀
  - Mehrere Accounts gleichzeitig in eigenen Konsolenfenstern
  - Zentraler Launcher mit Account-Verwaltung
- ✅ **Proxy-Support** 🔒
  - HTTP/HTTPS und SOCKS5 Proxy pro Account
  - **IP-Check** `[Z]`: Echte IP vs. Proxy-IP vergleichen
- ✅ **AutoEgg System** 🥚
  - Hatch + Hold beim Start, automatisch während Hunting
- ✅ **AutoBuyer System** 🛒
  - Ball-Bestände überwachen und automatisch nachkaufen
- ✅ **Auto-Release Duplikate** ♻️
  - Doppelte Pokemon automatisch releasen (behält Legendary & Shiny)
- ✅ **Daily Catch-Limit Erkennung** ⛔
  - Bot pausiert komplett wenn Limit erreicht
- ✅ **Session-Statistiken & Tracking** 📊
  - Catch-Rate, Fangquote pro Rarity, Shiny/Legendary Counter
  - Persistent in `stats.json`, [I] Hotkey
- ✅ **Discord Webhook Benachrichtigungen** 🔔
  - Seltene Fänge ans Handy melden lassen
- ✅ **Captcha-Erkennung & Auto-Solve** 🛡️
  - 2Captcha + Anti-Captcha, **Guthaben-Abfrage** im Config-Menü
  - **Report-Feedback**: Meldet korrekte/falsche Lösungen automatisch zurück
  - Temp-Ban Erkennung
- ✅ **Hotkeys** ⌨️ — [P] Pause, [I] Stats, [Q/ESC] Stop
- ✅ Live-Logging in Dateien

---

## 🔧 Installation

### 1. Dateien herunterladen

Lade alle Dateien herunter und lege sie in einen gemeinsamen Ordner:

| Datei | Beschreibung |
|-------|-------------|
| `CatchBot.exe` | Haupt-Bot (Einzel-Account) |
| `Catchbot-Multi-Acc-launcher.exe` | Multi-Account Launcher (Hauptbot benötigt) |
| `Pokemon_Names.txt` | Pokemon-Namensdatenbank |


### 2. Antivirus-Hinweis

Manche Antivirus-Programme melden `.exe`-Dateien die mit PyInstaller erstellt wurden als verdächtig. Das ist ein **False Positive**. Falls Windows Defender oder ein anderes Programm die Datei blockiert, füge den Ordner zur Ausnahmeliste hinzu.

---

## 🚀 Nutzung

### Einzelner Account

Doppelklicke `CatchBot.exe`

### Erste Einrichtung

1. **Token erhalten:**
   - Öffne Discord im Browser (https://discord.com/app)
   - Drücke `F12` (bei Opera/GX `STRG+Shift+I`) für Developer Tools
   - Gehe zum Tab "Network"
   - Drücke `F5` zum Neuladen
   - Suche nach "api", "science" oder "ack" in den Requests
   - Finde den Header "Authorization" - das ist dein Token
   - ⚠️ **ACHTUNG:** Gib deinen Token niemals an Dritte weiter!

2. **Channel ID erhalten:**
   - Aktiviere Developer Mode in Discord (Einstellungen → Erweitert → Entwicklermodus)
   - Rechtsklick auf den Channel → "ID kopieren"

3. **Bot konfigurieren:**
   - Wähle `[3] Config` im Hauptmenü
   - Wähle `[8]` und füge deinen Token ein
   - Wähle `[9]` und füge die Channel ID ein
   - Konfiguriere Auto-Catch, Ball-Regeln etc.

4. **Bot starten:**
   - `[1] Start` — Nur Hunting (ohne Daily Tasks)
   - `[2] Start + Daily Tasks` — Führt erst ;daily, ;h, ;swap, ;q aus, dann Hunting

---

## 🚀 Multi-Account Launcher

Der Multi-Account Launcher ermöglicht es, mehrere Accounts gleichzeitig zu betreiben. Jeder Account bekommt sein eigenes Konsolenfenster und eigene Config/Stats/Logs.

### Starten

Doppelklicke `Catchbot-Multi-Acc-launcher.exe`

### Launcher-Menü

| Taste | Funktion |
|-------|----------|
| **A** | Neuen Account hinzufügen (z.B. "main", "alt1", "alt2") |
| **K** | Account konfigurieren (öffnet CatchBot Config-Menü) |
| **S** | Alle bereiten Accounts gleichzeitig starten |
| **1-9** | Einzelnen Account starten/konfigurieren |
| **P** | Laufende Prozesse anzeigen / alle beenden |
| **D** | Account deaktivieren / aktivieren |
| **R** | Account aus der Liste entfernen |
| **Q** | Beenden |

### Workflow

1. `Catchbot-Multi-Acc-launcher.exe` starten
2. `[A]` Account hinzufügen (Name eingeben, z.B. "main")
3. `[K]` Token, Channel ID und **Proxy** für den Account setzen
4. Schritte 2-3 für weitere Accounts wiederholen
5. `[S]` Alle Accounts gleichzeitig starten

### Dateien pro Account

Jeder Account bekommt eigene Dateien:
- `config_<n>.json` — Konfiguration (inkl. Proxy)
- `stats_<n>.json` — Persistente Statistiken
- `logs/<n>/` — Log-Dateien

---

## 🔒 Proxy-Support

Für Multi-Account wird dringend empfohlen, **jedem Account einen eigenen Proxy** zu geben, damit Discord nicht mehrere Accounts von der gleichen IP sieht.

### WICHTIG: Proxy richtig nutzen

> **Wenn du einen Proxy im Bot nutzt, MUSS auch dein Browser (in dem du den Discord-Account manuell nutzt) denselben Proxy verwenden!**
>
> Sonst sieht Discord, dass der Account gleichzeitig oder abwechselnd von verschiedenen Standorten (z.B. Deutschland im Browser, Tokyo im Bot) aktiv ist. Das wird als "Impossible Travel" erkannt und kann zum Ban führen.
>
> **Regeln:**
> - Jedes Gerät/Browser das denselben Account nutzt, muss denselben Proxy verwenden
> - Wenn mehrere Personen den gleichen Account botten, müssen alle denselben Proxy nutzen
> - Deutsche Residential Proxies sind weniger auffällig wenn man selbst in DE ist
> - **Ohne Proxy ist man sicherer als mit falsch konfiguriertem Proxy!**

### Proxy setzen

Config → `[Y]` → Proxy-URL eingeben

### IP-Check

Config → `[Z]` prüft ob der Proxy korrekt funktioniert:
- Zeigt deine **echte IP** (direkte Verbindung)
- Zeigt die **Proxy-IP** (Verbindung über Proxy)
- Vergleicht beide: Wenn sie unterschiedlich sind → Proxy funktioniert ✓
- Warnung wenn beide IPs identisch sind → Proxy leitet nicht korrekt weiter

### Unterstützte Formate

| Typ | Format | Beispiel |
|-----|--------|----------|
| HTTP | `http://host:port` | `http://proxy.example.com:8080` |
| HTTP mit Auth | `http://user:pass@host:port` | `http://myuser:mypass@proxy.example.com:8080` |
| SOCKS5 | `socks5://host:port` | `socks5://proxy.example.com:1080` |
| SOCKS5 mit Auth | `socks5://user:pass@host:port` | `socks5://myuser:mypass@proxy.example.com:1080` |

### Proxy-Anbieter Empfehlung
- **Residential Proxies** — Sehen aus wie echte Heim-IPs, am sichersten
- **Datacenter Proxies** — Günstiger, aber leichter erkennbar
- **Tipp:** Deutsche Residential Proxies wenn man selbst in DE ist

---

## ⚙️ Config-Übersicht

### Hauptmenü

| Option | Taste | Beschreibung |
|--------|-------|-------------|
| Start | [1] | Hunting starten (ohne Daily Tasks) |
| Start + Daily Tasks | [2] | Dailys ausführen, dann Hunting |
| Config | [3] | Konfigurationsmenü öffnen |
| Logs | [4] | Log-Dateien anzeigen |
| Update-Checker | [5] | Auf neue Version prüfen |
| Beenden | [6] | Bot beenden |

### Config-Menü

| Option | Taste | Beschreibung | Standard |
|--------|-------|-------------|----------|
| **═══ Hunting ═══** | | | |
| Auto-Catch | [1] | Automatisch fangen an/aus | ✅ An |
| Ball-Regeln | [2] | Ball pro Rarity einstellen | Standard |
| Fish | [3] | Fischen an/aus | ❌ Aus |
| **═══ Systeme ═══** | | | |
| AutoBuyer | [B] | Ball-Kauf Konfiguration | ❌ Aus |
| AutoEgg | [E] | Egg Hatch/Hold an/aus | ❌ Aus |
| Webhook | [W] | Discord Webhook einrichten | ❌ Aus |
| **═══ Captcha ═══** | | | |
| Captcha-Service | [D] | 2Captcha / Anti-Captcha / Manuell | Manuell |
| 2Captcha Key | [C] | API Key setzen | - |
| Anti-Captcha Key | [K] | API Key setzen | - |
| Guthaben | [G] | Guthaben beider Services prüfen | - |
| **═══ Auto-Release ═══** | | | |
| Auto-Release | [X] | Duplikate releasen an/aus | ❌ Aus |
| Intervall | [V] | Alle X Catches releasen | 50 |
| **═══ Einstellungen ═══** | | | |
| Token | [8] | Discord Token setzen | - |
| Channel ID | [9] | Channel ID setzen | - |
| Proxy | [Y] | Proxy URL setzen (HTTP/SOCKS5) | - |
| IP-Check | [Z] | Echte IP vs. Proxy-IP prüfen | - |

### 🎯 Auto-Catch Ball-Regeln & Farben

Jede Rarity hat ihre eigene Farbe in der Konsole + Catch-Result + Pokemon-Name:

| Rarity | Ball | Button | Konsolen-Farbe |
|--------|------|--------|----------------|
| Common | Pokeball | 1. (ganz links) | 🔵 Blau |
| Uncommon | Pokeball | 1. (ganz links) | 🔵 Blau |
| Rare | Greatball | 2. (von links) | 🟡 Orange/Gelb |
| Super Rare | Ultraball | 3. (von links) | 🟡 Hellgelb |
| Legendary | Masterball | 5. (ganz rechts) | 🟣 Lila |
| Shiny | Masterball | 5. (ganz rechts) | 🩷 Pink/Rosa |

**Beispiel-Ausgabe:**
```
[23:49:57] 🎯 UNCOMMON (Wingull) → Pokeball geklickt! (Button 0) ✅ Gefangen
[23:50:12] 🎯 RARE (Eevee) → Greatball geklickt! (Button 1) ❌ Geflohen
[23:50:45] 🎯 LEGENDARY (Mewtwo) → Masterball geklickt! (Button 4) ✅ Gefangen
```

### 📖 Pokemon-Namens-Erkennung

Die Datei `Pokemon_Names.txt` enthält alle bekannten Pokemon-Namen. Der Bot:
- Bereinigt Discord-Markdown und Emojis aus den Nachrichten
- Sucht nach Pokemon-Namen (längste zuerst: "Tapu Koko" vor "Koko", "Mewtwo" vor "Mew")
- Zeigt den erkannten Namen im Log und in der Konsole

> **Wichtig:** `Pokemon_Names.txt` muss im selben Ordner wie `CatchBot.exe` liegen. Falls die Datei fehlt, funktioniert der Bot trotzdem — die Namens-Erkennung ist dann nur eingeschränkt.

### 🛒 AutoBuyer System

**Config → [B]** öffnet das AutoBuyer-Fenster:

| Option | Taste | Beschreibung |
|--------|-------|--------------|
| An/Aus | [1] | AutoBuyer aktivieren/deaktivieren |
| Pokeball | [2] | Schwellenwert + Kaufmenge einstellen |
| Greatball | [3] | Schwellenwert + Kaufmenge einstellen |
| Ultraball | [4] | Schwellenwert + Kaufmenge einstellen |
| Masterball | [5] | Schwellenwert + Kaufmenge einstellen |
| Reset | [6] | Standard-Werte wiederherstellen |

**Standard-Werte:**

| Ball | Kaufen wenn ≤ | Kaufmenge | Command |
|------|---------------|-----------|---------|
| Pokeball | ≤ 10 | 200x | `;shop buy pb 200` |
| Greatball | ≤ 10 | 100x | `;shop buy gb 100` |
| Ultraball | ≤ 10 | 25x | `;shop buy ub 25` |
| Masterball | ≤ 1 | 1x | `;shop buy mb 1` |

### ♻️ Auto-Release Duplikate

Automatisch doppelte Pokemon releasen mit dem PokéMeow Command `;release duplicates`. Behält Legendary und Shiny automatisch.

| Option | Taste | Beschreibung |
|--------|-------|--------------|
| An/Aus | [X] | Auto-Release aktivieren/deaktivieren |
| Intervall | [V] | Alle X Catches releasen (Standard: 50) |

### 📊 Session-Statistiken & Tracking

Drücke **[I]** während der Bot läuft um die aktuelle Statistik zu sehen. Beim Beenden wird sie automatisch angezeigt.

**Session-Stats (pro Bot-Start):**
- Encounters, Gefangen, Geflohen, Catch-Rate %
- Catch-Rate pro Rarity aufgeschlüsselt
- Beste Fänge (Shiny, Legendary, Super Rare)
- Session-Dauer

**All-Time Stats (persistent in `stats.json`):**
- Gefangen/Geflohen gesamt über alle Sessions
- Shinys gefangen (mit Name + Datum)
- Legendarys gefangen (mit Name + Datum)
- Anzahl Sessions

### 🔔 Discord Webhook einrichten

Lass dir seltene Fänge auf dein Handy schicken!

**Config → [W]** öffnet das Webhook-Fenster:

1. Erstelle einen Webhook in deinem Discord-Channel:
   - Channel → Bearbeiten → Integrationen → Webhooks → Neuer Webhook
   - Webhook URL kopieren
2. Config → [W] → [2] → URL einfügen
3. Config → [W] → [1] → Webhook aktivieren
4. Optional: Einstellen welche Rarities gemeldet werden (Standard: Legendary + Shiny)

| Option | Taste | Beschreibung |
|--------|-------|--------------|
| An/Aus | [1] | Webhook aktivieren/deaktivieren |
| URL | [2] | Webhook URL setzen |
| Common | [3] | Common Fänge melden |
| Uncommon | [4] | Uncommon Fänge melden |
| Rare | [5] | Rare Fänge melden |
| Super Rare | [6] | Super Rare Fänge melden |
| Legendary | [7] | Legendary Fänge melden (Standard: ✅) |
| Shiny | [8] | Shiny Fänge melden (Standard: ✅) |
| Geflohen | [9] | Auch bei Geflohen melden |
| Catch-Limit | [L] | Catch-Limit Warnung melden |

### 🤖 Captcha Auto-Solve einrichten

Du kannst zwischen **2Captcha** und **Anti-Captcha** wählen. Die Erkennung ist **optimiert für PokéMeow**: Nur Zahlen 1-9, 3-6 Stellen.

**Option A: 2Captcha**
1. Account auf https://2captcha.com erstellen
2. Config → `[D]` → "2Captcha" wählen
3. Config → `[C]` → API Key einfügen
4. Auto-Solve wird automatisch aktiviert

**Option B: Anti-Captcha**
1. Account auf https://anti-captcha.com erstellen
2. Config → `[D]` → "Anti-Captcha" wählen
3. Config → `[K]` → API Key einfügen
4. Auto-Solve wird automatisch aktiviert

**Guthaben prüfen:** Config → `[G]` zeigt das aktuelle Guthaben beider Services an (farbig: Grün >$1, Gelb >$0.20, Rot <$0.20).

**Report-Feedback:** Nach jedem Captcha-Versuch meldet der Bot dem Service automatisch zurück ob die Lösung korrekt oder falsch war. Bei 2Captcha verbessert das die Worker-Qualität, bei Anti-Captcha kann eine falsche Lösung zu einer Rückerstattung führen.

### ⛔ Temp-Ban & Catch-Limit Erkennung

**Temp-Ban:** Bot pausiert komplett + Warnung + Alarm. Mit [P] fortsetzen.

**Daily Catch-Limit:** Bot pausiert komplett + Warnung + Alarm + Webhook-Alert. Vote oder werde Patreon Supporter um das Limit zu entfernen. Mit [P] fortsetzen.

### ⌨️ Hotkeys (während Bot läuft)

| Taste | Funktion |
|-------|----------|
| **P** | Pause / Resume / Temp-Ban / Catch-Limit aufheben |
| **I** | Session-Statistiken anzeigen |
| **Q** oder **ESC** | Zurück ins Hauptmenü |

---

## 📁 Dateien

| Datei | Beschreibung |
|-------|-------------|
| `CatchBot.exe` | Haupt-Bot (Einzel-Account) |
| `Catchbot-Multi-Acc-launcher.exe` | Multi-Account Launcher |
| `Pokemon_Names.txt` | Pokemon-Namensdatenbank (muss im selben Ordner liegen) |
| `requirements.txt` | Referenz der verwendeten Libraries |
| `config.json` | Konfiguration (wird automatisch erstellt) |
| `config_<n>.json` | Config pro Account (Multi-Acc) |
| `stats.json` | Persistente Statistiken |
| `stats_<n>.json` | Stats pro Account (Multi-Acc) |
| `launcher_config.json` | Launcher-Konfiguration (Accountliste) |
| `logs/` | Log-Dateien pro Session |

---

## ⚠️ Wichtige Hinweise

1. **Account-Sicherheit:** Nutze einen Alt-Account, nicht deinen Haupt-Account
2. **Rate-Limiting:** Der Bot nutzt zufällige Intervalle, trotzdem kann Discord Rate-Limiting anwenden
3. **Token-Sicherheit:** Gib deinen Token niemals weiter, teile `config.json` nicht mit anderen
4. **Multi-Account:** Nutze verschiedene Proxies pro Account um Ban-Gefahr zu minimieren
5. **Rechtliches:** Self-Bots verstoßen gegen Discord ToS, Nutzung auf eigene Verantwortung
6. **Antivirus:** Falls die `.exe` blockiert wird, ist das ein False Positive — zur Ausnahmeliste hinzufügen

---

## 🛠 Troubleshooting

| Problem | Lösung |
|---------|--------|
| `.exe` wird vom Antivirus blockiert | Ordner zur Ausnahmeliste hinzufügen (False Positive) |
| Windows SmartScreen blockiert Start | "Weitere Informationen" → "Trotzdem ausführen" |
| Login fehlgeschlagen | Token überprüfen oder neuen holen |
| Channel nicht gefunden | Channel ID überprüfen |
| Bot wirft falschen Ball | Ball-Regeln in Config [2] prüfen |
| Pokemon-Name nicht erkannt | `Pokemon_Names.txt` im selben Ordner wie `CatchBot.exe` ablegen |
| AutoBuyer kauft nicht | Config → [B] → aktivieren + Schwellenwerte prüfen |
| Auto-Release geht nicht | Config → [X] → aktivieren + Intervall prüfen |
| Webhook geht nicht | Config → [W] → URL prüfen, muss mit `https://discord.com/api/webhooks/` starten |
| Captcha-Guthaben leer | Config → [G] → Guthaben prüfen, ggf. aufladen |
| Stats werden nicht gespeichert | Schreibrechte im Ordner prüfen |
| Auto-Solve funktioniert nicht | API Key prüfen, Guthaben prüfen |
| Bot pausiert nach Temp-Ban | Warte bis Ban abgelaufen, dann [P] drücken |
| Bot pausiert nach Catch-Limit | Vote/Patreon oder warten, dann [P] drücken |
| Multi-Acc startet nicht | `Catchbot-Multi-Acc-launcher.exe` nutzen |
| Proxy funktioniert nicht | URL-Format prüfen: `http://host:port` oder `socks5://host:port` |
| IP-Check zeigt gleiche IPs | Proxy leitet nicht weiter, anderen Proxy/Port testen |
| Connection Error mit Proxy | Proxy erreichbar? Credentials korrekt? |

---

## 📜 Lizenz

Dieses Projekt dient nur zu Bildungszwecken. Die Nutzung erfolgt auf eigenes Risiko.

---

**Version:** Beta 2.5
**Erstellt von:** MyNameIsKillua
