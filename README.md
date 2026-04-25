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
          ╚═════╝  ╚═════╝    ╚═╝
</pre>

### Automate your PokeMeow grind.

[![Version](https://img.shields.io/badge/version-6.2-blue?style=for-the-badge)]()
[![Python](https://img.shields.io/badge/python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white)]()
[![Source](https://img.shields.io/badge/source-Public-success?style=for-the-badge&logo=github&logoColor=white)]()
[![YouTube (outdated)](https://img.shields.io/badge/YouTube-outdated-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/Xq1AWC1P8i0)
[![License](https://img.shields.io/badge/license-Educational-green?style=for-the-badge)]()

**Auto-catch Pokemon with customizable settings, multi-account support, captcha solving, and more.**

[Notice](#-important-notice) &bull; [Installation](#-installation) &bull; [Usage](#-usage) &bull; [Multi-Account](#-multi-account-launcher) &bull; [Config](#%EF%B8%8F-config-overview) &bull; [Troubleshooting](#-troubleshooting)

---

</div>

## 📣 Important Notice

> [!WARNING]
> **CatchBot appears to be detected by PokeMeow now.**
>
> That is the reason I am releasing the full **source code publicly**. Unfortunately I do not know exactly what part of the bot makes it detectable, and I do not have the time to investigate &mdash; I have multiple new projects on my plate.
>
> If you want to **contribute, fork, improve, or donate** to keep the project alive, reach out to me directly on Discord: **`MyNameIsKillua`**.
>
> The public Discord server has been closed. DMs on Discord are the only contact channel.

> [!IMPORTANT]
> **The GitHub repository only contains the source code &mdash; the CatchBot AI captcha model is NOT in the repo.**
>
> The model (`catchbot_model_onnx_encrypted/`) is too large for GitHub and is shipped separately on the **[Releases page](https://github.com/MyNameIsKillua/pokemeow-selfbot/releases)**. You have two ways to get a working setup:
>
> | Option | What to do |
> |:-------|:-----------|
> | **A — Recommended (easiest)** | Go to **Releases** and download the full release ZIP (e.g. `CatchBot-v6.2-Full.zip`). It already contains the source **and** the AI model. Extract and you're done. |
> | **B — Clone / Download ZIP from the repo** | You only get the source. Go to **Releases**, download the standalone AI model archive (e.g. `CatchBot-Captcha-AI.zip`), extract it, and **drag the `catchbot_model_onnx_encrypted/` folder into your `CatchBot-v6.2-Modular/` folder** so it sits next to `CatchBot.py`. |
>
> If you don't want to use the local AI solver at all, you can skip the model entirely and use **2Captcha**, **Anti-Captcha**, or **Manual mode** instead (see [Captcha setup](#-captcha-auto-solve-setup)).

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
- Event Pokemon detection (red embed) &mdash; auto Premierball / Masterball
- Pokemon name recognition via `data/Pokemon_Names.txt`
- Special form detection (Iron-Leaves, Arceus-Fairy, etc.) directly from message text
- Full auto fishing (`;f`) &mdash; configurable interval (2-10x `;p`)
- Smart fishing ball pick &mdash; reads PokeMeow's `*_unlocked` emoji recommendation and throws the exact ball it suggests (Dive/Beast mapped to Masterball)
- Auto daily tasks (`;daily`, `;h`, `;swap`, `;q`)
- Colored console output per rarity

</td>
<td width="50%">

**Automation Systems**
- Spawn Command Selection &mdash; use `;p`, `;find`, or both randomly with configurable percentage
- Custom Messages &mdash; append custom text to spawn commands with independent command choice
- Custom Messages for `;fish` &mdash; separate custom messages specifically for fishing command with independent chance
- Remote Control System &mdash; Discord command system with 16 commands (`!stop`, `!start`, `!daily`, `!stats`, `!ss`, etc.)
- Activity Messages &mdash; randomly send casual messages after catches for natural appearance
- Rate Limit Protection &mdash; auto-detect command spam and pause to avoid bans
- AutoEgg &mdash; hatch + hold on startup & during hunting, egg stats tracking
- AutoBuyer &mdash; monitor & restock ball inventory
- AutoQuestRenewer &mdash; auto-renew unwanted quests using scrolls
- AutoQuestClaim &mdash; every 2h+ sends `;q` to pull a new quest and auto-rerolls it using Renewer logic
- Auto-Release &mdash; release duplicates (keeps Legendary & Shiny)
- Startup Commands &mdash; smart inventory check, open lootboxes (`;lb all`) and use razz berries (`;grazz all`) only when available
- Daily catch limit detection & pause
- Discord webhook notifications with Shiny/Legendary color highlights

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
- CatchBot AI Solver (~98% accuracy, free, local) &mdash; **bundled**
- 2Captcha + Anti-Captcha auto-solve
- Manual captcha mode with alarm + Windows toast
- Balance check in config menu
- Report feedback (correct/incorrect solutions)
- Temp-ban detection & recovery
- Configurable alarm volume (soft tones, no more ear-destroying beeps)
- Session stats, all-time tracking (incl. egg hatch + fish stats), live logging

</td>
</tr>
</table>

<br>

## 📥 Installation

This is a **Python source release** &mdash; you run it directly from `.py` files. There is no `.exe` anymore.

### 1. Requirements

- **Windows 10 / 11** (64-bit) &mdash; the bot uses Windows-only APIs (`winsound`, `msvcrt`, Windows toast)
- **Python 3.10 or newer** &mdash; download from <https://www.python.org/downloads/>
  - During install, **tick "Add Python to PATH"**
- **Discord account** with a valid token
- **PokeMeow channel** &mdash; the channel ID where the bot operates

### 2. Get the Code & the AI Model

> [!IMPORTANT]
> The GitHub repo only contains the **source code**. The **CatchBot AI model** lives on the **[Releases](https://github.com/MyNameIsKillua/pokemeow-selfbot/releases)** page because it is too large for GitHub.

Pick **one** of the two paths below:

**Path A &mdash; Easiest: download the full release** *(recommended for most people)*

1. Open the **[Releases page](https://github.com/MyNameIsKillua/pokemeow-selfbot/releases)**
2. Download the latest **Full** release ZIP (e.g. `CatchBot-v6.2-Full.zip`) &mdash; it already contains the source code **and** the AI model.
3. Extract it anywhere and open a terminal inside the `CatchBot-v6.2-Modular/` folder.
4. Skip to step 3 (Install Python Dependencies).

**Path B &mdash; Clone the repo + add the AI model manually** *(for developers / contributors)*

1. Clone or download the source from GitHub:
   ```
   git clone https://github.com/MyNameIsKillua/pokemeow-selfbot.git
   cd pokemeow-selfbot/CatchBot-v6.2-Modular
   ```
   (Or use the green **Code > Download ZIP** button and extract it.)
2. Open the **[Releases page](https://github.com/MyNameIsKillua/pokemeow-selfbot/releases)** and download the standalone AI archive (e.g. `CatchBot-Captcha-AI.zip`).
3. Extract that archive. It will produce a folder named `catchbot_model_onnx_encrypted/`.
4. **Drag that folder into your `CatchBot-v6.2-Modular/` folder** so it sits right next to `CatchBot.py`. Final layout should look like:
   ```
   CatchBot-v6.2-Modular/
     CatchBot.py
     launcher.py
     catchbot_model_onnx_encrypted/   ← the folder you just dragged in
     core/  config/  ...
   ```

> [!NOTE]
> If you don't plan to use the local AI captcha solver, you can skip the model folder entirely and use **2Captcha**, **Anti-Captcha**, or **Manual mode** instead (see [Captcha Auto-Solve Setup](#-config-overview)).

### 3. Install Python Dependencies

Open a terminal (PowerShell / CMD) in the `CatchBot-v6.2-Modular/` folder and run:

```powershell
# Install everything
python -m pip install -U discord.py-self colorama requests aiohttp onnxruntime numpy Pillow cryptography aiohttp_socks mss Pillow

# Required
python -m pip install -U discord.py-self colorama requests aiohttp

# Required for CatchBot AI (local captcha solver)
python -m pip install -U onnxruntime numpy Pillow cryptography

# Optional — SOCKS5 proxy support
python -m pip install -U aiohttp_socks

# Optional — required only if you plan to use the Remote Control !ss screenshot command
python -m pip install -U mss Pillow
```

<details>
<summary><b>Full dependency reference</b></summary>

<br>

| Package | Required? | Used for |
|:--------|:---------:|:---------|
| `discord.py-self` | ✅ | Self-bot connection to Discord |
| `colorama` | ✅ | Colored console output |
| `requests` | ✅ | Update check, captcha service HTTP calls, IP check |
| `aiohttp` | ✅ | Async HTTP requests used by Discord image/proxy/captcha handling |
| `onnxruntime` | AI captcha | Runs the CatchBot AI ONNX model locally |
| `numpy` | AI captcha | Image tensor pre-processing for the solver |
| `Pillow` | AI captcha / `!ss` | PNG decoding for captcha images and screenshots |
| `cryptography` | AI captcha | Decrypts the shipped CatchBot AI model |
| `aiohttp_socks` | Optional | SOCKS5 proxy support (`socks5://...`) |
| `mss` | Optional | Screen capture for the Remote Control `!ss` command |

HTTP/HTTPS proxies work out of the box without `aiohttp_socks`.

</details>

### 4. Folder Layout

After extracting, your working folder should look like this:

```
CatchBot-v6.2-Modular/
  CatchBot.py                         ← Entry script (run this)
  launcher.py                         ← Multi-account launcher
  README.md                           ← This file
  data/
    Pokemon_Names.txt                 ← Master list of Pokemon names (shipped)
  catchbot_model_onnx_encrypted/      ← CatchBot AI ONNX model (shipped, encrypted)
  core/ config/ ui/ utils/ captcha/ catching/ features/ webhooks/
  logs/                               ← Auto-created on first run
  config.json                         ← Auto-created on first run
  stats.json                          ← Auto-created on first run
```

> The `config.json`, `stats.json`, and `logs/` are generated on first run.

### 5. Windows Antivirus

> [!NOTE]
> Running Python source does **not** trigger the same false-positive warnings as a compiled `.exe`. You normally do not need antivirus exclusions for the source release. If Defender still flags something, exclude the project folder.

<br>

## 🚀 Usage

### First Start (Single Account)

1. **Launch** &mdash; open a terminal in `CatchBot-v6.2-Modular/` and run:
   ```powershell
   python CatchBot.py
   ```
2. **Configure** &mdash; in the main menu, press `[3]` to open the configuration and set your Discord token and channel ID.
3. **Start** &mdash; press `[1]` to start hunting, or `[2]` to start with daily tasks.

<details>
<summary><b>How to get your Discord Token</b></summary>

<br>

https://youtu.be/5SRwnLYdpJs

1. Open Discord in your browser &mdash; <https://discord.com/app>
2. Press `F12` (on Opera/GX: `CTRL+Shift+I`) for Developer Tools
3. Go to the **Network** tab
4. Type anything in any channel to trigger a network request
5. Find the **Authorization** header in the request headers section
6. That value is your token

> [!WARNING]
> **Never share your Discord token with anyone!** It grants full access to your account.

</details>

<details>
<summary><b>How to get your Channel ID</b></summary>

<br>

1. Enable Developer Mode in Discord &mdash; Settings > Advanced > Developer Mode
2. Right-click on the channel you want to use
3. Click **Copy Channel ID**

</details>

### Main Menu

| Key | Function |
|:---:|:---------|
| `1` | Start hunting (without daily tasks) |
| `2` | Start + Daily Tasks (`;daily`, `;h`, `;swap`, `;q` first) |
| `3` | Open configuration menu |
| `4` | View log files |
| `5` | Exit |

### Hotkeys (while running)

| Key | Function |
|:---:|:---------|
| `P` | Pause / Resume / Lift Temp-Ban / Catch Limit |
| `I` | Show session statistics |
| `Q` / `ESC` | Return to main menu |

<br>

## 👥 Multi-Account Launcher

Run multiple accounts simultaneously, each in its own console window with separate config, stats, and logs.

Start it with:

```powershell
python launcher.py
```

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
1. python launcher.py
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

Under the hood, the launcher starts each account with `python CatchBot.py --account <name>` in its own console window.

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
socks5://host:port                  # SOCKS5  (requires aiohttp_socks)
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
| Fish Interval | `4` | Fish every Nx `;p` (2-10) | 2 |
| | | **=== Systems ===** | |
| AutoBuyer | `B` | Ball purchase config | Off |
| AutoEgg | `E` | Toggle egg hatch/hold | Off |
| Quest Settings | `Q` | AutoQuestRenewer + AutoQuestClaimer | Off |
| &nbsp;&nbsp;&nbsp;&nbsp;↳ AutoQuestRenewer | `[Q] > [1]` | Auto-renew unwanted quests (Daily Tasks) | Off |
| &nbsp;&nbsp;&nbsp;&nbsp;↳ AutoQuestClaimer | `[Q] > [2]` | Every 2h+ send `;q` and auto-reroll (min 120m / 20s) | Off |
| Webhook | `W` | Discord webhook setup | Off |
| Remote Control | `C` | Discord command control (16 commands) | Off |
| Custom Message ;f | `N` | Custom messages for `;fish` command | Off |
| Rate Limit Protection | `R` | Auto-detect spam & pause | On |
| Alarm Volume | `L` | Alarm volume (0-100%) | 50% |
| | | **=== Captcha ===** | |
| Captcha Service | `D` | CatchBot AI / 2Captcha / Anti-Captcha / Manual | CatchBot AI |
| 2Captcha Key | `C` | Set API key | - |
| Anti-Captcha Key | `K` | Set API key | - |
| Balance | `G` | Check balance of both services | - |
| | | **=== Auto-Release ===** | |
| Auto-Release | `X` | Toggle duplicate release | Off |
| Interval | `V` | Release every X catches | 50 |
| | | **=== Startup Commands ===** | |
| Open Lootboxes | `T` | Send `;lb all` on startup | Off |
| Use Razz Berries | `I` | Send `;grazz all` on startup | Off |
| | | **=== Anti-Ban (Config > `[A]`) ===** | |
| Spawn Command | `W` | `;p` only / `;find` only / Both random | `;p` only |
| Custom Message | `1` | Append custom text to spawn commands | Off |
| Activity Messages | `2` | Send random casual messages | Off |
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
| Event (Common-Super Rare) | Premierball | 4th | Red embed |
| Event (Legendary/Shiny) | Masterball | 5th (far right) | Red embed |
| **Fishing (any rod)** | **PokeMeow recommendation** | Matched via `*_unlocked` emoji | Bypasses rarity rules |

**Available Balls:** `pb` (Pokeball), `gb` (Greatball), `ub` (Ultraball), `prb` (Premierball), `mb` (Masterball)

> Event Pokemon are detected by their **red embed border** from PokeMeow. Both event overrides can be toggled individually in Ball Rules (`[E]` and `[V]`).
>
> **Fishing** uses PokeMeow's own ball suggestion shown via the `:xxball_unlocked:` emoji on the spawn message &mdash; rarity rules, whitelist, and event overrides are bypassed while fishing. Dive Ball / Beast Ball recommendations are mapped to Masterball (no `db`/`bb` shortcut exists in PokeMeow's fishing prompt).

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

| Ball | Buy when ≤ | Amount | Command |
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

> The "Shared Success Feed" webhook that existed in earlier builds has been removed from the public source &mdash; it sent anonymized catches to a community feed whose URL was a credential we don't ship publicly. Your personal webhook is unaffected.

</details>

<details>
<summary><b>Captcha Auto-Solve Setup</b></summary>

<br>

Detection is optimized for PokeMeow: numbers only 1-9, 3-6 digits.

**Option A: CatchBot AI (Recommended)**
1. Make sure `pip3 install -U onnxruntime numpy Pillow cryptography` has been run
2. Confirm the `catchbot_model_onnx_encrypted/` folder is next to `CatchBot.py`
3. Config > `[D]` > Select "CatchBot AI" (Option 1)
4. Done &mdash; runs locally for free (~98% accuracy), no API key needed

**Option B: 2Captcha**
1. Create an account at <https://2captcha.com>
2. Config > `[D]` > Select "2Captcha"
3. Config > `[C]` > Paste API key

**Option C: Anti-Captcha**
1. Create an account at <https://anti-captcha.com>
2. Config > `[D]` > Select "Anti-Captcha"
3. Config > `[K]` > Paste API key

**Option D: Manual**
- Config > `[D]` > Select "Manual"
- The bot will play an alarm and show a Windows toast when a captcha appears. Solve it in Discord yourself, then press `P` to resume.

Check balance (2Captcha / Anti-Captcha only): Config > `[G]` &mdash; color-coded: Green >$1, Yellow >$0.20, Red <$0.20

After each captcha attempt, the bot automatically reports whether the solution was correct or incorrect. With 2Captcha this improves worker quality; with Anti-Captcha an incorrect solution can lead to a refund.

</details>

<details>
<summary><b>Session Statistics & Tracking</b></summary>

<br>

Press `[I]` while the bot is running to view current stats. On exit, they are displayed automatically.

**Session Stats (per bot start):**
- Encounters, Caught, Fled, Catch Rate %
- Catch rate broken down by rarity
- Fished / Fished Fled (separate fish stats)
- Best catches (Shiny, Legendary, Super Rare)
- Session duration

**All-Time Stats (persistent in `stats.json`):**
- Total caught/fled across all sessions
- Total fished / fished fled across all sessions
- Shinies caught (with name + date)
- Legendaries caught (with name + date)
- Eggs hatched (total count, Pokemon list, shiny/normal breakdown)
- Number of sessions

</details>

<br>

## 🗂 Project Layout

```
CatchBot-v6.2-Modular/
├── CatchBot.py              # Entry stub: imports core.entry.main() and calls it
├── launcher.py              # Multi-account launcher
├── README.md                # This file
│
├── data/
│   └── Pokemon_Names.txt    # Master list of Pokemon names for text detection
│
├── core/                    # Bot lifecycle
│   ├── entry.py             # main() — update check, CatchBot(...).run()
│   ├── bot.py               # CatchBot class — composes every mixin, __init__, _setup_client
│   └── main_loop.py         # MainLoopMixin — hotkey_listener, run_daily_tasks, run_main_loop
│
├── config/
│   └── io.py                # ConfigMixin — load_config, save_config, load_persistent_stats
│
├── ui/
│   ├── header.py            # HeaderMixin — clear_screen, print_header (ASCII banner)
│   ├── logs.py              # LogsMixin — log, save_logs_on_stop, show_logs
│   └── menus.py             # MenuMixin — main menu, config menu, ball rules, whitelist
│
├── utils/
│   ├── platform.py          # Shared constants & helpers
│   ├── updates.py           # check_for_updates_sync (GitHub version check at startup)
│   ├── pokemon_names.py     # Name list loader, text cleaner, name extractor
│   ├── discord_io.py        # wait_for_message*, send_command
│   ├── stats.py             # Session duration, stats printout
│   └── net.py               # check_ip (real vs. proxy IP)
│
├── captcha/
│   ├── solver.py            # CatchBot AI (ONNX) — loads the encrypted model
│   ├── detection.py         # Detection, alarms, watchdog, auto-solve dispatch
│   ├── services.py          # 2Captcha / AntiCaptcha integration and reporting
│   └── menus.py             # Captcha config menu
│
├── catching/
│   ├── catch.py             # check_and_catch_pokemon, catch_pokemon
│   ├── results.py           # check_catch_limit, check_catch_result, record_catch
│   └── fishing.py           # handle_fishing (;f pipeline)
│
├── features/
│   ├── egg.py               # AutoEgg + egg-hatch webhooks
│   ├── autobuyer.py         # Ball stock monitoring and ;shop buy
│   ├── auto_release.py      # Periodic ;release duplicates
│   ├── anti_ban.py          # Random pauses, idle, night mode, typing delay
│   ├── rate_limit.py        # No-response watchdog and sleep
│   ├── quests.py            # AutoQuestRenewer + AutoQuestClaimer
│   └── remote_control.py    # Discord control-channel command handler
│
└── webhooks/
    └── sender.py            # Private webhook, alert embeds
```

**Design notes:**
- Every feature set is a `XxxMixin` class; `core.bot.CatchBot` multi-inherits from all of them.
- Method bodies are byte-identical to the original monolithic `catchbot.py` &mdash; only the surrounding imports and class headers are new.
- No KeyAuth / license gate. The bot runs without any key.
- `config.json`, `stats.json`, and `logs/` live relative to the working directory (set to the script's folder by `core/entry.py`).

<br>

## 🔧 Troubleshooting

<details>
<summary><b>Click to expand full troubleshooting table</b></summary>

<br>

| Problem | Solution |
|:--------|:---------|
| `'python' is not recognized` | Python is not on your PATH. Reinstall Python and tick "Add Python to PATH". |
| `ModuleNotFoundError: discord` | Run `pip3 install -U discord.py-self` (note the `-self` suffix &mdash; do NOT install plain `discord.py`). |
| `ModuleNotFoundError: colorama` / `requests` / `aiohttp` | Run the `pip3 install` command from the Installation section. |
| `ModuleNotFoundError: onnxruntime` / `numpy` / `cryptography` | You want AI captcha &mdash; run `pip3 install -U onnxruntime numpy Pillow cryptography`. |
| CatchBot AI says "model not found" | The AI model is not in the GitHub repo. Download it from the **[Releases page](https://github.com/MyNameIsKillua/pokemeow-selfbot/releases)** and place the `catchbot_model_onnx_encrypted/` folder next to `CatchBot.py`. |
| SOCKS5 proxy fails | Run `pip3 install -U aiohttp_socks`. |
| `!ss` Remote Control command fails | Run `pip3 install -U mss Pillow`. |
| Login failed | Check token or get a new one. |
| Channel not found | Check channel ID. |
| Bot throws wrong ball | Check ball rules in Config `[2]`. |
| Pokemon name not recognized | Make sure `data/Pokemon_Names.txt` exists next to the launcher. |
| AutoBuyer not buying | Config > `[B]` > Enable + check thresholds. |
| Auto-Release not working | Config > `[X]` > Enable + check interval. |
| Webhook not working | Check URL starts with `https://discord.com/api/webhooks/`. |
| Captcha balance empty | Config > `[G]` > Top up if needed. |
| Stats not saving | Check write permissions in the folder. |
| Auto-Solve not working | Check API key and balance. |
| Bot pauses after temp-ban | Wait until ban expires, then press `[P]`. |
| Bot pauses after catch limit | Vote/Patreon or wait, then press `[P]`. |
| Multi-Acc not starting | Use `python launcher.py`. |
| Proxy not working | Check format: `http://host:port` or `socks5://host:port`. |
| IP Check shows same IPs | Proxy is not forwarding, try a different proxy/port. |
| Connection error with proxy | Is the proxy reachable? Are credentials correct? |

</details>

<br>

## ⚠️ Important Notes

- **Detection** &mdash; The bot appears to be detectable in its current state. That's why this source is public. Contributions welcome.
- **Account Safety** &mdash; Use an alt account, not your main.
- **Token Safety** &mdash; Never share your token or `config.json`.
- **Multi-Account** &mdash; Use different proxies per account to minimize ban risk.
- **Rate Limiting** &mdash; The bot uses random intervals, but Discord may still rate limit.

<br>

---

<div align="center">

**v6.2 Source Release** &mdash; Created by **MyNameIsKillua**

### 💬 Contact / Contribute / Donate
**Discord DM: `MyNameIsKillua`**

*(The public Discord server has been closed. DMs are the only contact channel.)*

</div>
