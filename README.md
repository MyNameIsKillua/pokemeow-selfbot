<div align="center">

# Changelog

**All notable changes to CatchBot are documented here.**

[![Current Version](https://img.shields.io/badge/Latest-v3.0-blue?style=for-the-badge)]()
[![Release Date](https://img.shields.io/badge/Updated-21.02.2026-green?style=for-the-badge)]()

---

</div>

## v3.0 &mdash; Official Release

> First official release! Desktop notifications fixed, softer alarm sounds, AutoQuestRenewer, egg hatch tracking, shiny/legendary highlights everywhere.

<details>
<summary><b>Desktop Notifications (Fixed)</b></summary>

&nbsp;

- Replaced `plyer` (which broke in compiled .exe builds) with native Windows toast notifications via PowerShell
- Works reliably in Nuitka .exe builds -- no external Python packages needed

</details>

<details>
<summary><b>Alarm Sound Rework</b></summary>

&nbsp;

- Replaced harsh `winsound.Beep()` with a custom WAV generator using smooth sine-wave tones with fade-in/fade-out
- New config option: **Alarm Volume** (0-100%, default 50%) -- adjustable in config menu
- Plays a test tone when changing volume so you hear the result immediately
- Even at 100% the volume is capped so it won't destroy your ears

</details>

<details>
<summary><b>AutoQuestRenewer (New)</b></summary>

&nbsp;

Automatically renews unwanted quests after `;q` during Daily Tasks.

| Config Key | What it filters |
|:-----------|:----------------|
| `[1]` | Toggle on/off |
| `[2]` | Battle Quests ("Defeat", "Battle") |
| `[3]` | Fish Quests ("Pokemon from Fishing", "Fish") |
| `[4]` | Receive from Player ("from another player") |
| `[5]` | Catch Quests ("Encounter", "Catch") |

- Parses quest embed, matches keywords, sends `;q r {number}` automatically
- Stops when no quest scrolls are left ("You don't have any quest reset scrolls!")
- Re-scans the `;q r` response and renews again if the replacement quest also matches
- 6-second cooldown between each renewal command

</details>

<details>
<summary><b>Shiny & Legendary Highlights</b></summary>

&nbsp;

- **Console logs**: Shiny catches print as `**Shiny (Pokemon)**` with a highlighted magenta banner
- **Shiny egg hatches**: Print as `**Shiny (Pokemon)**!` with the same highlight
- **Private webhook** (your config webhook): Shiny catches get a gold embed color, Legendaries get purple, plus a header line so you never miss them
- **Shared webhook** (`#successful-catches`): Same gold/purple embed color for Shiny/Legendary catches and Shiny egg hatches

</details>

<details>
<summary><b>Egg Hatch Tracking</b></summary>

&nbsp;

- Hatched Pokemon name now extracted and shown in both console and log file
- EXP/level-up lines are filtered out to prevent false name matches (e.g. Buddy name instead of hatched Pokemon)
- Egg hatches sent to both shared and private webhooks
- **Egg stats in `stats.json`**: Total eggs hatched, full hatch history (name + date + shiny), rarity breakdown (Normal vs Shiny)
- Session and all-time egg stats shown in `[I]` statistics view

</details>

<details>
<summary><b>Egg Startup Logic Improved</b></summary>

&nbsp;

- Bot now reads PokeMeow's response before deciding what to do
- If egg is "not ready to hatch yet", it knows an egg is already held and skips `;egg hold`
- Only sends `;egg hold` when no egg is held or after a successful hatch
- 3-second delay before egg check to avoid rapid command rejection

</details>

<details>
<summary><b>Other Changes</b></summary>

&nbsp;

- Version bumped from Beta 2.6 to **v3.0** (official release, no longer beta)
- Quest parser now strips markdown formatting (`**`, `__`, `*`) before matching
- Quest parser no longer creates phantom quests from reward/progress lines

</details>

---

## Beta v2.6 &mdash; 

> update checker functional, daily task scanning fix, stability improvements.

<details>
<summary><b>Update Checker (Now Functional)</b></summary>

&nbsp;

#### Menu option `[5]` now checks GitHub Releases for updates

| Detail | Description |
|:-------|:------------|
| **Source** | GitHub Releases (`MyNameIsKillua/pokemeow-selfbot`) |
| **Comparison** | Extracts version numbers from local + remote, compares numerically |
| **Download** | If a newer version exists, offers to open the download page in browser |
| **No Update** | Shows confirmation + current release info |

> Previously this was a placeholder that always showed "You are using the latest version".

</details>

<details>
<summary><b>Bug Fixes & Stability</b></summary>

&nbsp;

- **Daily task scanning fix** &mdash; Bot no longer scans for shinies/legendaries during daily tasks (`;daily`, `;h`, `;swap`, `;q`). Previously the bot would detect a shiny or legendary in the daily/quest response and try to click a Masterball button on it.
- Added `doing_dailys` guard flag &mdash; blocks `check_and_catch_pokemon` while daily tasks are running
- Daily task wrapper uses `try/finally` to ensure the flag is always reset, even on errors
- Guard flag reset on bot startup for clean state
- Version bumped to **2.6** across all files (catchbot, launcher, README, changelogs)

</details>

---

## Beta v2.5 &mdash; 

> Captcha system overhaul &mdash; CapSolver removed, Anti-Captcha added, report feedback for both services.

<details>
<summary><b>Captcha System Reworked</b></summary>

&nbsp;

#### CapSolver removed, Anti-Captcha added

| Detail | Description |
|:-------|:------------|
| **New Service** | [Anti-Captcha](https://anti-captcha.com) replaces CapSolver as the second captcha option |
| **API Endpoints** | `createTask`, `getTaskResult`, `getBalance`, `reportIncorrectImageCaptcha` |
| **Config `[D]`** | Select service: 2Captcha / Anti-Captcha / Manual |
| **Config `[K]`** | Set Anti-Captcha API key (was previously CapSolver) |
| **Balance `[G]`** | Now shows 2Captcha + Anti-Captcha balance |
| **Migration** | Old `capsolver_api_key` entries are automatically removed |

#### Report Feedback (New)

Reports are sent automatically when PokeMeow responds:
- `"thank you"` = correct &rarr; `reportCorrect`
- `"incorrect"` = wrong &rarr; `reportIncorrect` / `reportIncorrectImageCaptcha`

| Service | Feedback |
|:--------|:---------|
| **2Captcha** | `reportCorrect` + `reportIncorrect` |
| **Anti-Captcha** | `reportIncorrectImageCaptcha` (refund within 60s) |

> [!NOTE]
> Reports improve solution quality over time &mdash; services use them to optimize their workers.

#### Captcha Numbers Optimized

```
minLength:   3      (was 3)
maxLength:   6      (was 8 -- PokeMeow only uses 3-6 digits)
numeric:     1      (numbers only, 1-9)
comment:     improved description for better recognition
```

</details>

<details>
<summary><b>Other Changes</b></summary>

&nbsp;

- Version bumped to **2.5**
- Config migration: `capsolver_api_key` automatically removed, service reset to `"Manual"` if CapSolver was active

</details>

---

## Beta v2.4 &mdash;

> Start menu reworked, config simplified, proxy safety warning.

<details>
<summary><b>New Features</b></summary>

&nbsp;

#### Start Menu Reworked

| Option | Action |
|:-------|:-------|
| `[1] Start` | Hunting + auto-catch only |
| `[2] Start + Daily Tasks` | Runs all dailies first (`;daily`, `;h`, `;swap`, `;q`), then hunting |

- Daily tasks are no longer individually toggleable in config &mdash; decided at startup
- Fewer clicks, faster workflow

#### Config Menu Simplified

| Key | Function |
|:----|:---------|
| `[1]` | Auto-Catch |
| `[2]` | Ball Rules |
| `[3]` | Fish |

- Daily task toggles `[1]-[4]` removed &mdash; now controlled via start menu

</details>

<details>
<summary><b>Proxy Warning</b></summary>

&nbsp;

> [!WARNING]
> **Only use a proxy if browser + bot use the same proxy!**
>
> If the bot runs through a proxy in Tokyo, but your browser uses your real IP in Germany, Discord sees IP jumps between continents &mdash; **this is a ban risk!**
>
> - Every device and browser on the same account must use the **same proxy**
> - **Exception:** Residential proxies from your own country are less suspicious
> - **No proxy is safer than a misconfigured proxy**

</details>

<details>
<summary><b>Other Changes</b></summary>

&nbsp;

- Main menu rearranged: Config=`[3]`, Logs=`[4]`, Update Checker=`[5]`, Exit=`[6]`
- Version bumped to **2.4**

</details>

---

## Beta v2.3 &mdash; 

> Proxy support and IP check for multi-account safety.

<details>
<summary><b>New Features</b></summary>

&nbsp;

#### Proxy Support

| Feature | Detail |
|:--------|:-------|
| **Protocols** | HTTP / HTTPS / SOCKS5 |
| **Config `[Y]`** | Set proxy URL (`http://host:port` or `socks5://user:pass@host:port`) |
| **Auth** | Username + password supported |
| **Launcher** | Proxy status shown per account: `[HTTP: host:port]` / `[No Proxy]` |
| **SOCKS5** | Via optional `aiohttp_socks` dependency |

> [!IMPORTANT]
> **Recommended for multi-acc:** Each account with its own IP significantly reduces ban risk.

#### IP Check

- Config `[Z]` &mdash; shows real IP vs. proxy IP
- Automatically compares both: **Different = Proxy working**
- Warning if IPs are identical (proxy not forwarding)
- Fallback chain: `ipify` &rarr; `icanhazip` &rarr; `checkip.amazonaws`
- Works with HTTP and SOCKS5

</details>

<details>
<summary><b>Other Changes</b></summary>

&nbsp;

- `requirements.txt` extended with `aiohttp_socks` (optional)
- Config menu extended: `[Y]` Proxy, `[Z]` IP Check
- Proxy info displayed in config overview under Token/Channel

</details>

---

## Beta v2.2 &mdash; 

> Multi-account launcher, auto-release duplicates, balance check, Pokemon name recognition.

<details>
<summary><b>New Features</b></summary>

&nbsp;

#### Multi-Account Launcher

```
[A]   Add account (e.g. "main", "alt1", "alt2")
[K]   Configure account (opens CatchBot config menu)
[S]   Start all ready accounts simultaneously
[1-9] Start or configure individual account
[P]   Show running processes / terminate all
[R]   Remove account from list
```

- Each account gets its own files: `config_<name>.json`, `stats_<name>.json`, `logs/<name>/`
- Automatically checks if token + channel ID are set

#### Auto-Release Duplicates

| Setting | Detail |
|:--------|:-------|
| **Command** | `;release duplicates` |
| **Keeps** | Legendary + Shiny automatically |
| **Interval** | Configurable (default: every 50 catches) |
| **Config** | `[X]` on/off, `[V]` set interval |

#### Captcha Balance Check

Config `[G]` &mdash; shows current balance of both services:

| Balance | Color |
|:--------|:------|
| > $1.00 | Green |
| > $0.20 | Yellow |
| < $0.20 | Red |

#### Pokemon Name Recognition

- Names displayed in log + console via `Pokemon_Names.txt` database
- Cleans Discord markdown and emojis automatically
- Recognizes multi-part names (Tapu Koko, Mr. Mime, Iron Hands, etc.)

```
[23:49:57] UNCOMMON (Wingull) > Pokeball clicked! (Button 0) Caught
```

</details>

<details>
<summary><b>Bug Fixes & Stability</b></summary>

&nbsp;

- Various bug fixes and stability improvements
- Auto-Catch guard logging for better debugging
- Main loop now pauses during auto-release
- Multi-Account support: `--account` argument for separate configs

</details>

---

## Beta v2.1 &mdash; 

> Catch limit detection, result tracking, session stats, and Discord webhooks.

<details>
<summary><b>New Features</b></summary>

&nbsp;

#### Daily Catch Limit Detection

- Detects `"you have reached the daily catch limit"` automatically
- Bot pauses completely + red warning + alarm + webhook alert
- Resume with `[P]` after limit resets

#### Catch Result Detection

Clean single-line log with result appended:

```
[23:49:57] UNCOMMON > Pokeball clicked! (Button 0) Caught
[23:50:12] RARE     > Greatball clicked! (Button 1) Fled
```

Waits up to 8 seconds for PokeMeow response.

#### Session Statistics & Tracking

| Feature | Detail |
|:--------|:-------|
| **Hotkey `[I]`** | Live session summary at any time |
| **Tracked** | Total caught/fled, catch rate %, rate per rarity, duration, best catches |
| **Counters** | Shiny + Legendary (session + all-time) |
| **Persistent** | Saved in `stats.json` |

#### Discord Webhook Notifications

- Send catch results to a Discord webhook
- Configurable which rarities are reported
- Catch limit warning via webhook
- Dedicated config window: Config `[W]`

</details>

<details>
<summary><b>Bug Fixes</b></summary>

&nbsp;

- AutoBuyer fix: 5s cooldown after purchase
- AutoBuyer also triggers on `on_message_edit`

</details>

---

## Beta v2.0 &mdash; 

> AutoEgg, captcha auto-solve, temp-ban detection, colored messages, AutoBuyer.

<details>
<summary><b>New Features</b></summary>

&nbsp;

#### AutoEgg System

- Automatic egg hatch + hold on bot startup
- Detects `"egg is ready to hatch"` during hunting
- Config `[E]` to toggle

#### Captcha Auto-Solve

| Setting | Value |
|:--------|:------|
| **Services** | 2Captcha + CapSolver |
| **Optimized** | Numbers only (`numeric=1`), 3-8 digits |
| **Retries** | Configurable 1-5 attempts |

#### Temp-Ban Detection

- Bot pauses completely + warning + alarm
- Resume with `[P]` after ban expires

#### Colored Catch Messages

| Rarity | Color |
|:-------|:------|
| Common / Uncommon | Blue |
| Rare | Orange / Yellow |
| Super Rare | Light Yellow |
| Legendary | Purple |
| Shiny | Pink |

#### AutoBuyer System

- Monitors ball inventory after each catch
- Dedicated config window: Config `[B]`

</details>

<details>
<summary><b>Bug Fixes</b></summary>

&nbsp;

- Lootbox emoji false positives fixed
- Egg startup improved
- Captcha retry + numeric fix
- Deprecated asyncio fix, code cleanup

</details>

---

## Beta v1.9 &mdash; 

> Captcha detection with auto-pause, alarm system, hotkeys.

<details>
<summary><b>Features</b></summary>

&nbsp;

- Captcha detection with auto-pause
- Captcha alarm: Desktop notification + sound
- Captcha auto-resume on edited messages
- Hotkeys: `[P]` Pause/Resume, `[Q/ESC]` Back

</details>

---

## Beta v1.8

> Core auto-catch system, ball rules, logging, daily tasks.

<details>
<summary><b>Features</b></summary>

&nbsp;

- Auto-Catch with rarity detection (button click)
- Configurable ball rules
- Live logging in `logs/` folder
- Daily tasks: `;daily`, `;h`, `;swap`, `;q`
- Hunting loop with random intervals (11-15s)
- Optional fishing (`;f`)

</details>

---

## Beta v1.3

> Initial release.

<details>
<summary><b>Features</b></summary>

&nbsp;

- Automatic daily tasks
- Automatic Pokemon hunting
- Auto-Catch based on rarity (text commands)
- Basic logging system

</details>

---

<div align="center">

<sub>CatchBot by MyNameIsKillua</sub>

</div>
