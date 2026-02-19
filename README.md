# CatchBot by MyNameIsKillua

Automate your PokeMeow grind: auto-catch Pokemon with a wide range of customizable settings and fine-tuned controls.

Youtube Video - incoming

Discord Server - https://discord.gg/y42nVCGZqF



## Beta Version 2.5

A Discord Self-Bot for automatic Pokemon hunting in PokeMeow.

**IMPORTANT NOTE:** Self-Bots violate the Discord Terms of Service and may result in a permanent account ban. Use this bot at your own risk!

**Multi-Account significantly increases the ban risk because:**

**IP Linking:** Discord connects all accounts via your IP - if one is detected, all get banned simultaneously ("Chain-Ban").

**Suspicious Pattern:** Multiple accounts with identical, automated behavior at the same time are extremely easy to detect.

**More API Traffic:** Each additional account multiplies the requests and triggers rate limits/flags faster.

**Rough Estimate:**

| Setup | Relative Risk
|-----|-----
| 1 Account, careful | Baseline
| 2-3 Accounts, same IP | approx. 2-3x higher
| 5+ Accounts, same IP | significantly higher
| Many Accounts, no Proxy/Cooldown | very high

---

## Features

- Auto Daily Tasks (;daily, ;h, ;swap, ;q)
- Automatic Pokemon Hunting (;p with random intervals)
- Semi-Automatic Fishing (;f)
- **Auto-Catch based on Rarity**
  - Automatically detects Pokemon rarity
  - Clicks the matching ball button (Pokeball, Greatball, Ultraball, Masterball)
  - **Pokemon Name** is recognized and displayed in the log (via `Pokemon_Names.txt`)
  - **Colored console output** per rarity + **Catch Result** (caught/fled)
- **Multi-Account Launcher**
  - Multiple accounts simultaneously in their own console windows
  - Central launcher with account management
- **Proxy Support**
  - HTTP/HTTPS and SOCKS5 proxy per account
  - **IP Check** `[Z]`: Compare real IP vs. proxy IP
- **AutoEgg System**
  - Hatch + Hold on startup, automatic during hunting
- **AutoBuyer System**
  - Monitor ball inventory and automatically restock
- **Auto-Release Duplicates**
  - Automatically release duplicate Pokemon (keeps Legendary & Shiny)
- **Daily Catch Limit Detection**
  - Bot pauses completely when limit is reached
- **Session Statistics & Tracking**
  - Catch rate, catch rate per rarity, Shiny/Legendary counter
  - Persistent in `stats.json`, [I] hotkey
- **Discord Webhook Notifications**
  - Get notified about rare catches on your phone
- **Captcha Detection & Auto-Solve**
  - 2Captcha + Anti-Captcha, **Balance Check** in config menu
  - **Report Feedback**: Automatically reports correct/incorrect solutions back
  - Temp-Ban detection
- **Hotkeys** — [P] Pause, [I] Stats, [Q/ESC] Stop
- Live logging to files

---

## Installation

### 1. Download Files

Download all files and place them in a shared folder:

| File | Description |
|-------|-------------|
| `CatchBot.exe` | Main bot (single account) |
| `Catchbot-Multi-Acc-launcher.exe` | Multi-Account Launcher (requires main bot) |
| `Pokemon_Names.txt` | Pokemon name database |


### 2. Antivirus Notice

Some antivirus programs flag `.exe` files created with PyInstaller as suspicious. This is a **False Positive**. If Windows Defender or another program blocks the file, add the folder to the exception list.

---

## Usage

### Single Account

Double-click `CatchBot.exe`

### First-Time Setup

1. **Get your Token:**
   - Open Discord in your browser (https://discord.com/app)
   - Press `F12` (on Opera/GX use `CTRL+Shift+I`) for Developer Tools
   - Go to the "Network" tab
   - Press `F5` to reload
   - Search for "api", "science" or "ack" in the requests
   - Find the "Authorization" header - that is your token
   - **WARNING:** Never share your token with anyone!

2. **Get your Channel ID:**
   - Enable Developer Mode in Discord (Settings > Advanced > Developer Mode)
   - Right-click on the channel > "Copy ID"

3. **Configure the bot:**
   - Select `[3] Config` in the main menu
   - Select `[8]` and paste your token
   - Select `[9]` and paste the channel ID
   - Configure Auto-Catch, ball rules, etc.

4. **Start the bot:**
   - `[1] Start` — Hunting only (without daily tasks)
   - `[2] Start + Daily Tasks` — Runs ;daily, ;h, ;swap, ;q first, then hunting

---

## Multi-Account Launcher

The Multi-Account Launcher allows you to run multiple accounts simultaneously. Each account gets its own console window and separate config/stats/logs.

### Starting

Double-click `Catchbot-Multi-Acc-launcher.exe`

### Launcher Menu

| Key | Function |
|-------|----------|
| **A** | Add new account (e.g. "main", "alt1", "alt2") |
| **K** | Configure account (opens CatchBot config menu) |
| **S** | Start all ready accounts simultaneously |
| **1-9** | Start/configure individual account |
| **P** | Show running processes / terminate all |
| **D** | Disable / enable account |
| **R** | Remove account from list |
| **Q** | Exit |

### Workflow

1. Start `Catchbot-Multi-Acc-launcher.exe`
2. `[A]` Add account (enter name, e.g. "main")
3. `[K]` Set token, channel ID and **proxy** for the account
4. Repeat steps 2-3 for additional accounts
5. `[S]` Start all accounts simultaneously

### Files per Account

Each account gets its own files:
- `config_<n>.json` — Configuration (incl. proxy)
- `stats_<n>.json` — Persistent statistics
- `logs/<n>/` — Log files

---

## Proxy Support

For multi-account usage, it is strongly recommended to **assign each account its own proxy** so Discord does not see multiple accounts from the same IP.

### IMPORTANT: Using Proxies Correctly

> **If you use a proxy in the bot, your browser (where you manually use the Discord account) MUST also use the same proxy!**
>
> Otherwise, Discord sees the account active from different locations simultaneously or alternately (e.g. Germany in the browser, Tokyo in the bot). This is detected as "Impossible Travel" and can lead to a ban.
>
> **Rules:**
> - Every device/browser using the same account must use the same proxy
> - If multiple people are botting the same account, they must all use the same proxy
> - Residential proxies from your own country are less suspicious
> - **No proxy is safer than a misconfigured proxy!**

### Setting a Proxy

Config > `[Y]` > Enter proxy URL

### IP Check

Config > `[Z]` checks whether the proxy is working correctly:
- Shows your **real IP** (direct connection)
- Shows the **proxy IP** (connection via proxy)
- Compares both: If they are different > Proxy is working
- Warning if both IPs are identical > Proxy is not forwarding correctly

### Supported Formats

| Type | Format | Example |
|-----|--------|----------|
| HTTP | `http://host:port` | `http://proxy.example.com:8080` |
| HTTP with Auth | `http://user:pass@host:port` | `http://myuser:mypass@proxy.example.com:8080` |
| SOCKS5 | `socks5://host:port` | `socks5://proxy.example.com:1080` |
| SOCKS5 with Auth | `socks5://user:pass@host:port` | `socks5://myuser:mypass@proxy.example.com:1080` |

### Proxy Provider Recommendation
- **Residential Proxies** — Look like real home IPs, safest option
- **Datacenter Proxies** — Cheaper, but easier to detect
- **Tip:** Use residential proxies from your own country

---

## Config Overview

### Main Menu

| Option | Key | Description |
|--------|-------|-------------|
| Start | [1] | Start hunting (without daily tasks) |
| Start + Daily Tasks | [2] | Run dailies, then hunting |
| Config | [3] | Open configuration menu |
| Logs | [4] | View log files |
| Update Checker | [5] | Check for new version |
| Exit | [6] | Exit bot |

### Config Menu

| Option | Key | Description | Default |
|--------|-------|-------------|----------|
| **=== Hunting ===** | | | |
| Auto-Catch | [1] | Toggle automatic catching on/off | On |
| Ball Rules | [2] | Set ball per rarity | Default |
| Fish | [3] | Toggle fishing on/off | Off |
| **=== Systems ===** | | | |
| AutoBuyer | [B] | Ball purchase configuration | Off |
| AutoEgg | [E] | Toggle egg hatch/hold on/off | Off |
| Webhook | [W] | Set up Discord webhook | Off |
| **=== Captcha ===** | | | |
| Captcha Service | [D] | 2Captcha / Anti-Captcha / Manual | Manual |
| 2Captcha Key | [C] | Set API key | - |
| Anti-Captcha Key | [K] | Set API key | - |
| Balance | [G] | Check balance of both services | - |
| **=== Auto-Release ===** | | | |
| Auto-Release | [X] | Toggle duplicate release on/off | Off |
| Interval | [V] | Release every X catches | 50 |
| **=== Settings ===** | | | |
| Token | [8] | Set Discord token | - |
| Channel ID | [9] | Set channel ID | - |
| Proxy | [Y] | Set proxy URL (HTTP/SOCKS5) | - |
| IP Check | [Z] | Check real IP vs. proxy IP | - |

### Auto-Catch Ball Rules & Colors

Each rarity has its own color in the console + catch result + Pokemon name:

| Rarity | Ball | Button | Console Color |
|--------|------|--------|----------------|
| Common | Pokeball | 1st (far left) | Blue |
| Uncommon | Pokeball | 1st (far left) | Blue |
| Rare | Greatball | 2nd (from left) | Orange/Yellow |
| Super Rare | Ultraball | 3rd (from left) | Light Yellow |
| Legendary | Masterball | 5th (far right) | Purple |
| Shiny | Masterball | 5th (far right) | Pink |

**Example Output:**
```
[23:49:57] UNCOMMON (Wingull) > Pokeball clicked! (Button 0) Caught
[23:50:12] RARE (Eevee) > Greatball clicked! (Button 1) Fled
[23:50:45] LEGENDARY (Mewtwo) > Masterball clicked! (Button 4) Caught
```

### Pokemon Name Recognition

The file `Pokemon_Names.txt` contains all known Pokemon names. The bot:
- Cleans Discord markdown and emojis from messages
- Searches for Pokemon names (longest first: "Tapu Koko" before "Koko", "Mewtwo" before "Mew")
- Displays the recognized name in the log and console

> **Important:** `Pokemon_Names.txt` must be in the same folder as `CatchBot.exe`. If the file is missing, the bot still works — name recognition will just be limited.

### AutoBuyer System

**Config > [B]** opens the AutoBuyer window:

| Option | Key | Description |
|--------|-------|--------------|
| On/Off | [1] | Enable/disable AutoBuyer |
| Pokeball | [2] | Set threshold + purchase amount |
| Greatball | [3] | Set threshold + purchase amount |
| Ultraball | [4] | Set threshold + purchase amount |
| Masterball | [5] | Set threshold + purchase amount |
| Reset | [6] | Restore default values |

**Default Values:**

| Ball | Buy when <= | Purchase Amount | Command |
|------|---------------|-----------|---------|
| Pokeball | <= 10 | 200x | `;shop buy pb 200` |
| Greatball | <= 10 | 100x | `;shop buy gb 100` |
| Ultraball | <= 10 | 25x | `;shop buy ub 25` |
| Masterball | <= 1 | 1x | `;shop buy mb 1` |

### Auto-Release Duplicates

Automatically release duplicate Pokemon using the PokeMeow command `;release duplicates`. Keeps Legendary and Shiny automatically.

| Option | Key | Description |
|--------|-------|--------------|
| On/Off | [X] | Enable/disable Auto-Release |
| Interval | [V] | Release every X catches (default: 50) |

### Session Statistics & Tracking

Press **[I]** while the bot is running to view current statistics. On exit, they are displayed automatically.

**Session Stats (per bot start):**
- Encounters, Caught, Fled, Catch Rate %
- Catch rate broken down by rarity
- Best catches (Shiny, Legendary, Super Rare)
- Session duration

**All-Time Stats (persistent in `stats.json`):**
- Total caught/fled across all sessions
- Shinies caught (with name + date)
- Legendaries caught (with name + date)
- Number of sessions

### Set Up Discord Webhook

Get rare catches sent to your phone!

**Config > [W]** opens the webhook window:

1. Create a webhook in your Discord channel:
   - Channel > Edit > Integrations > Webhooks > New Webhook
   - Copy the webhook URL
2. Config > [W] > [2] > Paste URL
3. Config > [W] > [1] > Enable webhook
4. Optional: Configure which rarities are reported (default: Legendary + Shiny)

| Option | Key | Description |
|--------|-------|--------------|
| On/Off | [1] | Enable/disable webhook |
| URL | [2] | Set webhook URL |
| Common | [3] | Report Common catches |
| Uncommon | [4] | Report Uncommon catches |
| Rare | [5] | Report Rare catches |
| Super Rare | [6] | Report Super Rare catches |
| Legendary | [7] | Report Legendary catches (default: on) |
| Shiny | [8] | Report Shiny catches (default: on) |
| Fled | [9] | Also report when fled |
| Catch Limit | [L] | Report catch limit warning |

### Captcha Auto-Solve Setup

You can choose between **2Captcha** and **Anti-Captcha**. Detection is **optimized for PokeMeow**: Numbers only 1-9, 3-6 digits.

**Option A: 2Captcha**
1. Create an account at https://2captcha.com
2. Config > `[D]` > Select "2Captcha"
3. Config > `[C]` > Paste API key
4. Auto-Solve is activated automatically

**Option B: Anti-Captcha**
1. Create an account at https://anti-captcha.com
2. Config > `[D]` > Select "Anti-Captcha"
3. Config > `[K]` > Paste API key
4. Auto-Solve is activated automatically

**Check Balance:** Config > `[G]` shows the current balance of both services (color-coded: Green >$1, Yellow >$0.20, Red <$0.20).

**Report Feedback:** After each captcha attempt, the bot automatically reports back to the service whether the solution was correct or incorrect. With 2Captcha, this improves worker quality; with Anti-Captcha, an incorrect solution can lead to a refund.

### Temp-Ban & Catch Limit Detection

**Temp-Ban:** Bot pauses completely + warning + alarm. Continue with [P].

**Daily Catch Limit:** Bot pauses completely + warning + alarm + webhook alert. Vote or become a Patreon Supporter to remove the limit. Continue with [P].

### Hotkeys (while bot is running)

| Key | Function |
|-------|----------|
| **P** | Pause / Resume / Lift Temp-Ban / Catch Limit |
| **I** | Show session statistics |
| **Q** or **ESC** | Return to main menu |

---

## Files

| File | Description |
|-------|-------------|
| `CatchBot.exe` | Main bot (single account) |
| `Catchbot-Multi-Acc-launcher.exe` | Multi-Account Launcher |
| `Pokemon_Names.txt` | Pokemon name database (must be in the same folder) |
| `requirements.txt` | Reference of used libraries |
| `config.json` | Configuration (created automatically) |
| `config_<n>.json` | Config per account (multi-acc) |
| `stats.json` | Persistent statistics |
| `stats_<n>.json` | Stats per account (multi-acc) |
| `launcher_config.json` | Launcher configuration (account list) |
| `logs/` | Log files per session |

---

## Important Notes

1. **Account Safety:** Use an alt account, not your main account
2. **Rate Limiting:** The bot uses random intervals, but Discord may still apply rate limiting
3. **Token Safety:** Never share your token, do not share `config.json` with others
4. **Multi-Account:** Use different proxies per account to minimize ban risk
5. **Legal:** Self-Bots violate Discord ToS, use at your own risk
6. **Antivirus:** If the `.exe` is blocked, it is a False Positive — add to exception list

---

## Troubleshooting

| Problem | Solution |
|---------|--------|
| `.exe` blocked by antivirus | Add folder to exception list (False Positive) |
| Windows SmartScreen blocks launch | "More info" > "Run anyway" |
| Login failed | Check token or get a new one |
| Channel not found | Check channel ID |
| Bot throws wrong ball | Check ball rules in Config [2] |
| Pokemon name not recognized | Place `Pokemon_Names.txt` in the same folder as `CatchBot.exe` |
| AutoBuyer not buying | Config > [B] > Enable + check thresholds |
| Auto-Release not working | Config > [X] > Enable + check interval |
| Webhook not working | Config > [W] > Check URL, must start with `https://discord.com/api/webhooks/` |
| Captcha balance empty | Config > [G] > Check balance, top up if needed |
| Stats not saving | Check write permissions in the folder |
| Auto-Solve not working | Check API key, check balance |
| Bot pauses after temp-ban | Wait until ban expires, then press [P] |
| Bot pauses after catch limit | Vote/Patreon or wait, then press [P] |
| Multi-Acc not starting | Use `Catchbot-Multi-Acc-launcher.exe` |
| Proxy not working | Check URL format: `http://host:port` or `socks5://host:port` |
| IP Check shows same IPs | Proxy is not forwarding, try a different proxy/port |
| Connection error with proxy | Is the proxy reachable? Are credentials correct? |

---

## License

This project is for educational purposes only. Use at your own risk.

---

**Version:** Beta 2.5
**Created by:** MyNameIsKillua
