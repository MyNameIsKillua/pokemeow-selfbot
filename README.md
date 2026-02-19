<div align="center">

<pre>
 ██████╗ █████╗ ████████╗ ██████╗██╗  ██╗
██╔════╝██╔══██╗╚══██╔══╝██╔════╝██║  ██║
██║     ███████║   ██║   ██║     ███████║
██║     ██╔══██║   ██║   ██║     ██╔══██║
╚██████╗██║  ██║   ██║   ╚██████╗██║  ██║
 ╚═════╝╚═╝  ╚═╝   ╚═╝    ╚═════╝╚═╝  ╚═╝
          ██████╗  ██████╗ ████████╗
          ██╔══██╗██╔═══██╗╚══██╔══╝
          ██████╔╝██║   ██║   ██║
          ██╔══██╗██║   ██║   ██║
          ██████╔╝╚██████╔╝   ██║
          ╚═════╝  ╚═════╝    ╚═╝    by MyNameIsKillua
</pre>

### Automate your PokeMeow grind.

[![Version](https://img.shields.io/badge/version-2.5_beta-blue?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white)]()
[![Discord](https://img.shields.io/badge/Discord_Server-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/y42nVCGZqF)
[![License](https://img.shields.io/badge/license-Educational-green?style=for-the-badge)]()

**Auto-catch Pokemon with customizable settings, multi-account support, captcha solving, and more.**

[Features](#-features) &bull; [Installation](#-installation) &bull; [Usage](#-usage) &bull; [Multi-Account](#-multi-account-launcher) &bull; [Config](#%EF%B8%8F-config-overview) &bull; [Troubleshooting](#-troubleshooting)

---

</div>

> [!CAUTION]
> **Self-Bots violate the Discord Terms of Service** and may result in a **permanent account ban**. Use at your own risk. Always use an alt account.
>
> **Multi-Account significantly increases the ban risk because:**
>
> | Factor | Why it matters |
> |:-------|:---------------|
> | **IP Linking** | Discord connects all accounts via your IP -- if one is detected, all get banned simultaneously ("Chain-Ban"). |
> | **Suspicious Patterns** | Multiple accounts with identical, automated behavior at the same time are extremely easy to detect. |
> | **More API Traffic** | Each additional account multiplies the requests and triggers rate limits/flags faster. |
>
> | Setup | Relative Risk |
> |:------|:--------------|
> | 1 Account, careful | Baseline |
> | 2-3 Accounts, same IP | ~2-3x higher |
> | 5+ Accounts, same IP | Significantly higher |
> | Many Accounts, no Proxy/Cooldown | Very high |

<br>

## ⚡ Features

<table>
<tr>
<td width="50%">

**Catching & Hunting**
- Auto-catch based on rarity detection
- Smart ball selection (Pokeball to Masterball)
- Pokemon name recognition via `Pokemon_Names.txt`
- Semi-automatic fishing (`;f`)
- Auto daily tasks (`;daily`, `;h`, `;swap`, `;q`)
- Colored console output per rarity

</td>
<td width="50%">

**Automation Systems**
- AutoEgg &mdash; hatch + hold on startup & during hunting
- AutoBuyer &mdash; monitor & restock ball inventory
- Auto-Release &mdash; release duplicates (keeps Legendary & Shiny)
- Daily catch limit detection & pause
- Discord webhook notifications for rare catches

</td>
</tr>
<tr>
<td width="50%">

**Multi-Account & Security**
- Run multiple accounts in separate console windows
- Central launcher with account management
- HTTP/HTTPS & SOCKS5 proxy support per account
- Built-in IP check (real IP vs proxy IP)

</td>
<td width="50%">

**Captcha & Monitoring**
- 2Captcha + Anti-Captcha auto-solve
- Balance check in config menu
- Report feedback (correct/incorrect solutions)
- Temp-ban detection & recovery
- Session stats, all-time tracking, live logging

</td>
</tr>
</table>

<br>

## 📥 Installation

### 1. Download Files

| File | Description |
|:-----|:------------|
| `CatchBot.exe` | Main bot (single account) |
| `Catchbot-Multi-Acc-launcher.exe` | Multi-Account Launcher (required Main Bot) |
| `Pokemon_Names.txt` | Pokemon name database |

Download all files and place them in a **shared folder**.

### 2. Antivirus Notice

> [!NOTE]
> Some antivirus programs flag `.exe` files created with PyInstaller as suspicious. This is a **False Positive**.
> If Windows Defender or another program blocks the file, add the folder to the exception list.

<br>

## 🚀 Usage

### Quick Start (Single Account)

1. Double-click `CatchBot.exe`
2. Select `[3] Config` to set up your token and channel
3. Select `[1] Start` or `[2] Start + Daily Tasks`

<details>
<summary><b>How to get your Discord Token</b></summary>

<br>

1. Open Discord in your browser &mdash; https://discord.com/app
2. Press `F12` (on Opera/GX: `CTRL+Shift+I`) for Developer Tools
3. Go to the **Network** tab
4. Press `F5` to reload
5. Search for `api`, `science` or `ack` in the requests
6. Find the **Authorization** header &mdash; that is your token

> [!WARNING]
> **Never share your token with anyone!**

</details>

<details>
<summary><b>How to get your Channel ID</b></summary>

<br>

1. Enable Developer Mode in Discord &mdash; Settings > Advanced > Developer Mode
2. Right-click on the channel > **Copy ID**

</details>

<details>
<summary><b>First-Time Configuration</b></summary>

<br>

1. Select `[3] Config` in the main menu
2. Select `[8]` and paste your token
3. Select `[9]` and paste the channel ID
4. Configure auto-catch, ball rules, etc.

</details>

### Main Menu

| Key | Function |
|:---:|:---------|
| `1` | Start hunting (without daily tasks) |
| `2` | Start + Daily Tasks (`;daily`, `;h`, `;swap`, `;q` first) |
| `3` | Open configuration menu |
| `4` | View log files |
| `5` | Check for updates |
| `6` | Exit |

### Hotkeys (while running)

| Key | Function |
|:---:|:---------|
| `P` | Pause / Resume / Lift Temp-Ban / Catch Limit |
| `I` | Show session statistics |
| `Q` / `ESC` | Return to main menu |

<br>

## 👥 Multi-Account Launcher

Run multiple accounts simultaneously, each in its own console window with separate config, stats, and logs.

### Launcher Controls

| Key | Function |
|:---:|:---------|
| `A` | Add new account (e.g. "main", "alt1", "alt2") |
| `K` | Configure account (opens CatchBot config) |
| `S` | Start all ready accounts |
| `1-9` | Start/configure individual account |
| `P` | Show running processes / terminate all |
| `D` | Disable / enable account |
| `R` | Remove account from list |
| `Q` | Exit launcher |

### Workflow

```
1. Start  Catchbot-Multi-Acc-launcher.exe
2. [A]    Add account (enter a name, e.g. "main")
3. [K]    Set token, channel ID, and proxy
4.        Repeat 2-3 for additional accounts
5. [S]    Start all accounts
```

Each account gets its own files:
```
config_<name>.json    # Configuration (incl. proxy)
stats_<name>.json     # Persistent statistics
logs/<name>/          # Log files
```

<br>

## 🌐 Proxy Support

> [!IMPORTANT]
> For multi-account usage, it is **strongly recommended** to assign each account its own proxy so Discord does not see multiple accounts from the same IP.

<details>
<summary><b>Why proxies matter</b></summary>

<br>

If you use a proxy in the bot, your browser (where you manually use the Discord account) **must also use the same proxy**. Otherwise, Discord sees the account active from different locations simultaneously (e.g. Germany in browser, Tokyo in bot) &mdash; this is detected as "Impossible Travel" and can lead to a ban.

**Rules:**
- Every device/browser using the same account must use the same proxy
- If multiple people are botting the same account, they must all use the same proxy
- Residential proxies from your own country are less suspicious
- **No proxy is safer than a misconfigured proxy!**

</details>

### Supported Formats

```
http://host:port                    # HTTP
http://user:pass@host:port          # HTTP with Auth
socks5://host:port                  # SOCKS5
socks5://user:pass@host:port        # SOCKS5 with Auth
```

- Set proxy: Config > `[Y]`
- IP Check:  Config > `[Z]` &mdash; compares your real IP vs proxy IP

> **Tip:** Use **residential proxies** from your own country for the safest option.

### Multi-Account Risk Assessment

| Setup | Risk Level |
|:------|:-----------|
| 1 Account, careful | Baseline |
| 2-3 Accounts, same IP | ~2-3x higher |
| 5+ Accounts, same IP | Significantly higher |
| Many Accounts, no Proxy | Very high |

<br>

## ⚙️ Config Overview

<details>
<summary><b>Full Config Menu Reference</b></summary>

<br>

| Option | Key | Description | Default |
|:-------|:---:|:------------|:--------|
| | | **=== Hunting ===** | |
| Auto-Catch | `1` | Toggle automatic catching | On |
| Ball Rules | `2` | Set ball per rarity | Default |
| Fish | `3` | Toggle fishing | Off |
| | | **=== Systems ===** | |
| AutoBuyer | `B` | Ball purchase config | Off |
| AutoEgg | `E` | Toggle egg hatch/hold | Off |
| Webhook | `W` | Discord webhook setup | Off |
| | | **=== Captcha ===** | |
| Captcha Service | `D` | 2Captcha / Anti-Captcha / Manual | Manual |
| 2Captcha Key | `C` | Set API key | - |
| Anti-Captcha Key | `K` | Set API key | - |
| Balance | `G` | Check balance of both services | - |
| | | **=== Auto-Release ===** | |
| Auto-Release | `X` | Toggle duplicate release | Off |
| Interval | `V` | Release every X catches | 50 |
| | | **=== Settings ===** | |
| Token | `8` | Set Discord token | - |
| Channel ID | `9` | Set channel ID | - |
| Proxy | `Y` | Set proxy URL | - |
| IP Check | `Z` | Check real vs proxy IP | - |

</details>

### Ball Rules & Rarity Colors

| Rarity | Ball | Button | Console Color |
|:-------|:-----|:-------|:--------------|
| Common | Pokeball | 1st (far left) | Blue |
| Uncommon | Pokeball | 1st (far left) | Blue |
| Rare | Greatball | 2nd | Orange/Yellow |
| Super Rare | Ultraball | 3rd | Light Yellow |
| Legendary | Masterball | 5th (far right) | Purple |
| Shiny | Masterball | 5th (far right) | Pink |

**Example output:**
```
[23:49:57] UNCOMMON  (Wingull)  > Pokeball clicked! (Button 0)  Caught
[23:50:12] RARE      (Eevee)    > Greatball clicked! (Button 1)  Fled
[23:50:45] LEGENDARY (Mewtwo)   > Masterball clicked! (Button 4) Caught
```

<details>
<summary><b>AutoBuyer Configuration</b></summary>

<br>

Open with Config > `[B]`

| Key | Function |
|:---:|:---------|
| `1` | Enable/disable AutoBuyer |
| `2` | Pokeball threshold + amount |
| `3` | Greatball threshold + amount |
| `4` | Ultraball threshold + amount |
| `5` | Masterball threshold + amount |
| `6` | Reset to defaults |

**Defaults:**

| Ball | Buy when &le; | Amount | Command |
|:-----|:-------------|:-------|:--------|
| Pokeball | 10 | 200x | `;shop buy pb 200` |
| Greatball | 10 | 100x | `;shop buy gb 100` |
| Ultraball | 10 | 25x | `;shop buy ub 25` |
| Masterball | 1 | 1x | `;shop buy mb 1` |

</details>

<details>
<summary><b>Webhook Configuration</b></summary>

<br>

Get rare catches sent straight to your phone!

**Setup:**
1. Create a webhook &mdash; Channel > Edit > Integrations > Webhooks > New Webhook
2. Config > `[W]` > `[2]` > Paste webhook URL
3. Config > `[W]` > `[1]` > Enable

| Key | Reports |
|:---:|:--------|
| `1` | Enable/disable webhook |
| `2` | Set webhook URL |
| `3` | Common catches |
| `4` | Uncommon catches |
| `5` | Rare catches |
| `6` | Super Rare catches |
| `7` | Legendary catches (default: on) |
| `8` | Shiny catches (default: on) |
| `9` | Also report when fled |
| `L` | Catch limit warning |

</details>

<details>
<summary><b>Captcha Auto-Solve Setup</b></summary>

<br>

Detection is optimized for PokeMeow: numbers only 1-9, 3-6 digits.

**Option A: 2Captcha**
1. Create an account at https://2captcha.com
2. Config > `[D]` > Select "2Captcha"
3. Config > `[C]` > Paste API key

**Option B: Anti-Captcha**
1. Create an account at https://anti-captcha.com
2. Config > `[D]` > Select "Anti-Captcha"
3. Config > `[K]` > Paste API key

Check balance: Config > `[G]` &mdash; color-coded: Green >&dollar;1, Yellow >&dollar;0.20, Red <&dollar;0.20

After each captcha attempt, the bot automatically reports whether the solution was correct or incorrect. With 2Captcha this improves worker quality; with Anti-Captcha an incorrect solution can lead to a refund.

</details>

<details>
<summary><b>Session Statistics & Tracking</b></summary>

<br>

Press `[I]` while the bot is running to view current stats. On exit, they are displayed automatically.

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

</details>

<br>

## 📁 File Structure

```
CatchBot/
├── CatchBot.exe                     # Main bot
├── Catchbot-Multi-Acc-launcher.exe  # Multi-Account Launcher
├── Pokemon_Names.txt                # Pokemon name database
├── config.json                      # Configuration (auto-created)
├── config_<name>.json               # Per-account config (multi-acc)
├── stats.json                       # Persistent statistics
├── stats_<name>.json                # Per-account stats (multi-acc)
├── launcher_config.json             # Launcher account list
└── logs/                            # Log files per session
    └── <name>/
```

<br>

## 🔧 Troubleshooting

<details>
<summary><b>Click to expand full troubleshooting table</b></summary>

<br>

| Problem | Solution |
|:--------|:---------|
| `.exe` blocked by antivirus | Add folder to exception list (False Positive) |
| Windows SmartScreen blocks launch | "More info" > "Run anyway" |
| Login failed | Check token or get a new one |
| Channel not found | Check channel ID |
| Bot throws wrong ball | Check ball rules in Config `[2]` |
| Pokemon name not recognized | Place `Pokemon_Names.txt` in the same folder as `CatchBot.exe` |
| AutoBuyer not buying | Config > `[B]` > Enable + check thresholds |
| Auto-Release not working | Config > `[X]` > Enable + check interval |
| Webhook not working | Check URL starts with `https://discord.com/api/webhooks/` |
| Captcha balance empty | Config > `[G]` > Top up if needed |
| Stats not saving | Check write permissions in the folder |
| Auto-Solve not working | Check API key and balance |
| Bot pauses after temp-ban | Wait until ban expires, then press `[P]` |
| Bot pauses after catch limit | Vote/Patreon or wait, then press `[P]` |
| Multi-Acc not starting | Use `Catchbot-Multi-Acc-launcher.exe` |
| Proxy not working | Check format: `http://host:port` or `socks5://host:port` |
| IP Check shows same IPs | Proxy is not forwarding, try a different proxy/port |
| Connection error with proxy | Is the proxy reachable? Are credentials correct? |

</details>

<br>

## ⚠️ Important Notes

- **Account Safety** &mdash; Use an alt account, not your main
- **Token Safety** &mdash; Never share your token or `config.json`
- **Multi-Account** &mdash; Use different proxies per account to minimize ban risk
- **Rate Limiting** &mdash; The bot uses random intervals, but Discord may still rate limit
- **Antivirus** &mdash; `.exe` flagged as virus is a False Positive, add to exception list

<br>

---

<div align="center">

**Beta 2.5** &mdash; Created by **MyNameIsKillua**

[![Discord](https://img.shields.io/badge/Join_the_Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white)](https://discord.gg/y42nVCGZqF)

</div>
