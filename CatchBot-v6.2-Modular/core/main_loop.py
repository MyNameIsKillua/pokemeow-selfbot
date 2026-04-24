"""Main loop mixin: hotkey listener, daily tasks, main loop, start_bot, run."""
import os
import sys
import re
import json
import asyncio
import random
import threading
import atexit
import base64
import time as time_module
from datetime import datetime, timedelta
from urllib.parse import urlparse

import discord
from colorama import Fore, Style

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from utils.platform import (
    WINDOWS,
    HAS_TOAST,
    HAS_AIOHTTP_SOCKS,
    _show_windows_toast,
    _generate_alarm_wav,
)

try:
    import winsound
    import msvcrt
except ImportError:
    winsound = None
    msvcrt = None

if HAS_AIOHTTP_SOCKS:
    try:
        from aiohttp_socks import ProxyConnector
    except ImportError:
        ProxyConnector = None
else:
    ProxyConnector = None


class MainLoopMixin:
    async def hotkey_listener(self):
        """Lauscht auf Tastendruck im Terminal (Windows)"""
        if not WINDOWS:
            self.log("Hotkeys only available on Windows.")
            return
        
        while self.running:
            try:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    
                    # P = Pause/Resume (auch zum Fortsetzen nach Temp-Ban)
                    if key in (b'p', b'P'):
                        if self.catch_limit_reached:
                            self.catch_limit_reached = False
                            self.log("Catch limit pause lifted, bot continues (Key P)")
                            print(f"\n{Fore.GREEN}  Catch limit pause lifted! Bot continues!{Style.RESET_ALL}\n")
                        elif self.temp_banned:
                            self.temp_banned = False
                            self.log("▶️ Temp-Ban lifted, bot continues (Key P)")
                            print(f"\n{Fore.GREEN}  ▶️  Temp-Ban lifted! Bot continues!{Style.RESET_ALL}\n")
                        elif self.captcha_active:
                            print(f"{Fore.YELLOW}  Bot is paused due to captcha. Solve the captcha first!{Style.RESET_ALL}")
                        else:
                            self.paused = not self.paused
                            if self.paused:
                                self.log("⏸️ Bot manually PAUSED (Key P)")
                                print(f"\n{Fore.YELLOW}  ⏸️  Bot PAUSED! Press [P] to resume.{Style.RESET_ALL}\n")
                            else:
                                self.log("▶️ Bot manually RESUMED (Key P)")
                                print(f"\n{Fore.GREEN}  ▶️  Bot continues!{Style.RESET_ALL}\n")
                    
                    # Q oder ESC = Back ins Hauptmenü
                    elif key in (b'q', b'Q', b'\x1b'):
                        self.log("Bot stopped (Key Q/ESC)")
                        print(f"\n{Fore.YELLOW}  Bot stopping... Back to main menu.{Style.RESET_ALL}\n")
                        self.running = False
                        return
                    
                    # I = Session-Statistiken anzeigen
                    elif key in (b'i', b'I'):
                        self.print_session_stats()
                
                await asyncio.sleep(0.1)  # 100ms Polling
                
            except Exception:
                await asyncio.sleep(0.5)
    
    # ═════════════════════════════════════════════════════════════════
    #  UI / MENÜS
    # ═════════════════════════════════════════════════════════════════
    
    async def run_daily_tasks(self, channel):
        """Fuehrt alle taeglichen Aufgaben aus (;daily, ;h, ;swap, ;q) + AutoQuestRenewer"""
        self.doing_dailys = True
        print(f"\n{Fore.CYAN}═══ Starting Daily Tasks ═══{Style.RESET_ALL}\n")
        
        tasks = [
            (';daily', 'Daily Reward'),
            (';h', 'Hunt'),
            (';swap', 'Swap Tickets'),
            (';q', 'Quests')
        ]
        
        try:
            for command, name in tasks:
                await self.send_command(channel, command)
                
                # After ;q: trigger AutoQuestRenewer if enabled
                if command == ';q' and self.config.get('auto_quest_renewer', {}).get('enabled', False):
                    await self.process_quest_renew(channel)
                else:
                    await asyncio.sleep(4)
        finally:
            self.doing_dailys = False
        
        print(f"\n{Fore.GREEN}✓ Daily Tasks completed!{Style.RESET_ALL}\n")
    
    async def run_main_loop(self, channel):
        """Hauptschleife für Pokemon Hunting"""
        if self.pokemon_names:
            print(f"{Fore.GREEN}✓ Pokemon name list successfully loaded! ({len(self.pokemon_names)} names){Style.RESET_ALL}\n")
        else:
            print(f"{Fore.RED}⚠ Pokemon name list could not be loaded! Name detection limited.{Style.RESET_ALL}\n")
        
        self.startup_phase = False
        print(f"{Fore.CYAN}\u2550\u2550\u2550 Starting Hunting Loop \u2550\u2550\u2550{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}  Hotkeys: [P] Pause/Resume  |  [I] Stats  |  [Q/ESC] Stop{Style.RESET_ALL}\n")
        self.p_counter = 0
        skip_next_wait = True  # First ;p fires quickly after startup
        
        # Schedule first anti-ban pause if enabled
        if self.config.get('anti_ban', {}).get('enabled', False):
            self.schedule_next_anti_ban_pause()
        
        while self.running:
            try:
                # Wenn pausiert, Captcha aktiv oder Egg-Aktion läuft → warten
                if self.paused or self.anti_ban_paused or self.captcha_active or self.egg_busy or self.temp_banned or self.buying_balls or self.catch_limit_reached or self.releasing or self.doing_dailys:
                    await asyncio.sleep(1)
                    continue

                # --- AutoQuestClaim tick (only runs when idle; waits for next
                # loop iteration if another busy-flag gets set mid-check). ---
                await self._autoquestclaim_tick(channel)
                if not self.running:
                    continue

                # --- Night Mode check ---
                if await self.anti_ban_night_mode_check():
                    continue  # Just woke up, re-check everything
                
                # --- Anti-Ban random pause check ---
                await self.anti_ban_pause_check()
                if self.anti_ban_paused or not self.running:
                    continue
                
                # --- Random idle moment check ---
                await self.anti_ban_idle_check()
                if not self.running or self.paused or self.anti_ban_paused:
                    continue
                
                if skip_next_wait:
                    skip_next_wait = False
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                else:
                    # Use configurable spawn delay from anti-ban settings
                    ab = self.config.get('anti_ban', {})
                    delay_min = ab.get('spawn_delay_min', 11)
                    delay_max = ab.get('spawn_delay_max', 15)
                    wait_time = random.randint(delay_min, delay_max)
                    await asyncio.sleep(wait_time)
                
                # Nochmal prüfen nach dem Warten (könnte sich geändert haben)
                if not self.running or self.paused or self.anti_ban_paused or self.captcha_active or self.egg_busy or self.temp_banned or self.buying_balls or self.catch_limit_reached or self.releasing:
                    continue
                
                # --- Skip Spawn check ---
                if self.should_skip_spawn():
                    continue
                
                # --- Pick base spawn command (;p or ;find) ---
                ab = self.config.get('anti_ban', {})
                spawn_mode = ab.get('spawn_command', 'p_only')
                if spawn_mode == 'find_only':
                    base_cmd = ';find'
                elif spawn_mode == 'both_random':
                    p_chance = ab.get('spawn_p_chance', 50)
                    base_cmd = ';p' if random.randint(1, 100) <= p_chance else ';find'
                else:
                    base_cmd = ';p'
                
                # --- Apply custom message (independent command choice) ---
                cm_cfg = self.config.get('custom_message', {})
                if cm_cfg.get('enabled', False) and cm_cfg.get('message', ''):
                    cm_chance = cm_cfg.get('chance', 50)
                    if random.randint(1, 100) <= cm_chance:
                        # Custom message has its own command preference
                        cm_mode = cm_cfg.get('command', 'p_only')
                        if cm_mode == 'find_only':
                            cm_base = ';find'
                        elif cm_mode == 'both_random':
                            cm_p_chance = cm_cfg.get('p_chance', 50)
                            cm_base = ';p' if random.randint(1, 100) <= cm_p_chance else ';find'
                        else:
                            cm_base = ';p'
                        spawn_cmd = f"{cm_base} {cm_cfg['message']}"
                        self.log(f"Custom message: {spawn_cmd}")
                    else:
                        spawn_cmd = base_cmd
                else:
                    spawn_cmd = base_cmd
                
                # --- Rate Limit Protection Check (before sending command) ---
                if await self.check_rate_limit_protection():
                    continue  # After sleep, re-check everything
                
                # --- Typing Simulation ---
                await self.get_typing_delay(spawn_cmd)
                
                await self.send_command(channel, spawn_cmd)
                self.increment_no_response()  # Track that we sent a command without response yet
                self.p_counter += 1
                
                fish_iv = self.config.get('fish_interval', 2)
                if self.config['fish_enabled'] and self.p_counter % fish_iv == 0:
                    # Wait before fishing (extra delay to avoid rapid commands)
                    fish_wait = random.uniform(6, 8)
                    await asyncio.sleep(fish_wait)
                    if self.running and not self.paused and not self.anti_ban_paused and not self.captcha_active and not self.egg_busy and not self.temp_banned and not self.buying_balls and not self.catch_limit_reached and not self.releasing:
                        # Typing sim for fish command
                        await self.get_typing_delay(';f')
                        await self.handle_fishing(channel)
                        # After fishing, skip the normal wait -- next ;p in 0.5-2s
                        skip_next_wait = True
                
            except Exception as e:
                self.log(f"Error in Main Loop: {str(e)}")
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
                await asyncio.sleep(5)
    
    async def start_bot(self, with_dailys=False):
        """Startet den Bot. with_dailys=True fuehrt Daily Tasks vor dem Hunting aus."""
        # Ensure startup_phase is True so on_message won't catch Pokemon
        # during inventory check, egg check, dailys, etc.
        self.startup_phase = True
        self.catching = False
        self.fishing_active = False
        self.anti_ban_paused = False
        self.anti_ban_next_pause = None
        
        if not self.config['token'] or self.config['token'] == 'Your_Discord_Token_Here':
            print(f"{Fore.RED}Error: No token set! Please set it in the config.{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return
        
        if not self.config['channel_id'] or self.config['channel_id'] == 'Your_Channel_ID_Here':
            print(f"{Fore.RED}Error: No Channel ID set! Please set it in the config.{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return
        
        # Neuen Client erstellen (damit Restart sauber funktioniert)
        self._setup_client()
        
        # Start-Zeit für Log-Datei
        self.start_time = datetime.now().strftime('%d.%m.%Y %H-%M-%S')
        self.log(f"=== Bot started (v6.2) ===")
        self.log(f"Auto-Catch: {self.config.get('auto_catch_enabled', True)}")
        self.log(f"Catch-Rules: {json.dumps(self.config.get('catch_rules', {}))}")
        
        service_name = self.get_captcha_service_name()
        service = self.config.get('captcha_service', 'manual')
        self.log(f"Captcha-Service: {service_name}")
        self.log(f"Auto-Solve: {self.config.get('auto_solve_captcha', False)}")
        if self.config.get('auto_solve_captcha', False) and self.get_active_captcha_api_key():
            self.log(f"{service_name} API Key: {'*' * 8} (set)")
        
        if not HAS_PLYER and not HAS_TOAST:
            self.log("⚠️ Desktop notifications not available on this platform")
        
        self.print_header()
        print(f"\n{Fore.YELLOW}Starting Bot...{Style.RESET_ALL}\n")
        print(f"{Fore.GREEN}Logs: logs/Logs {self.start_time}.txt{Style.RESET_ALL}")
        
        if os.name == 'nt':
            print(f"{Fore.GREEN}✓ Desktop Notifications enabled (native Windows toast){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Desktop Notifications not available (Windows only){Style.RESET_ALL}")
        
        service = self.config.get('captcha_service', 'manual')
        service_name = self.get_captcha_service_name()
        if service != 'manual' and self.config.get('auto_solve_captcha', False) and self.get_active_captcha_api_key():
            print(f"{Fore.GREEN}✓ {service_name} Auto-Solve enabled{Style.RESET_ALL}")
        elif service != 'manual' and self.config.get('auto_solve_captcha', False) and not self.get_active_captcha_api_key():
            print(f"{Fore.YELLOW}⚠ {service_name} Auto-Solve enabled but no API Key set!{Style.RESET_ALL}")
        elif service == 'manual':
            print(f"{Fore.YELLOW}⚠ Captcha Service: Manual (no Auto-Solve){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Auto-Solve disabled (manual captcha solving){Style.RESET_ALL}")
        
        # Preload CatchBot AI model at startup (so first captcha solves instantly)
        if service == 'catchbot_ai' and self.config.get('auto_solve_captcha', False):
            print(f"{Fore.CYAN}  Loading CatchBot AI model...{Style.RESET_ALL}", end=" ", flush=True)
            solver = self._load_ai_solver()
            if solver:
                print(f"{Fore.GREEN}Ready!{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}Failed!{Style.RESET_ALL}")
        
        if not HAS_REQUESTS:
            print(f"{Fore.YELLOW}⚠ 'requests' not installed -> Auto-Solve not available{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  Install with: py -m pip install requests{Style.RESET_ALL}")
        
        # AutoBuyer Status
        ab = self.config.get('autobuyer', {})
        if ab.get('enabled', False):
            print(f"{Fore.GREEN}✓ AutoBuyer enabled (PB≤{ab.get('pb',{}).get('threshold',10)} GB≤{ab.get('gb',{}).get('threshold',10)} UB≤{ab.get('ub',{}).get('threshold',10)} MB≤{ab.get('mb',{}).get('threshold',1)}){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ AutoBuyer disabled{Style.RESET_ALL}")
        
        # Auto-Release Status
        ar = self.config.get('auto_release', {})
        if ar.get('enabled', False):
            print(f"{Fore.GREEN}✓ Auto-Release enabled (every {ar.get('interval', 50)} catches → ;release duplicates){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Auto-Release disabled{Style.RESET_ALL}")
        
        # Startup Commands Status
        startup_items = []
        if self.config.get('startup_lootbox', False):
            startup_items.append(';lb all')
        if self.config.get('startup_grazz', False):
            startup_items.append(';grazz all')
        if startup_items:
            print(f"{Fore.GREEN}✓ Startup Commands: {', '.join(startup_items)}{Style.RESET_ALL}")
        
        # AutoQuestRenewer Status
        aqr = self.config.get('auto_quest_renewer', {})
        if aqr.get('enabled', False):
            cats = []
            if aqr.get('battle_quests', True): cats.append('Battle')
            if aqr.get('fish_quests', True): cats.append('Fish')
            if aqr.get('receive_quests', True): cats.append('Receive')
            if aqr.get('catch_quests', True): cats.append('Catch')
            print(f"{Fore.GREEN}✓ AutoQuestRenewer enabled (renewing: {', '.join(cats)}){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ AutoQuestRenewer disabled{Style.RESET_ALL}")
        
        # Rate Limit Protection Status
        rl_cfg = self.config.get('rate_limit_protection', {})
        if rl_cfg.get('enabled', True):
            rl_max = rl_cfg.get('max_no_response', 3)
            rl_sleep = f"{rl_cfg.get('sleep_min', 30)}-{rl_cfg.get('sleep_max', 90)}s"
            print(f"{Fore.GREEN}✓ Rate Limit Protection enabled (sleep after {rl_max} no-response, {rl_sleep}){Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Rate Limit Protection disabled{Style.RESET_ALL}")
        
        # Remote Control Status
        rc_cfg = self.config.get('remote_control', {})
        if rc_cfg.get('enabled', False) and rc_cfg.get('control_channel_id', ''):
            rc_prefix = rc_cfg.get('prefix', '!')
            print(f"{Fore.GREEN}✓ Remote Control enabled - Try {rc_prefix}help in your control channel{Style.RESET_ALL}")
        
        # Proxy Status
        proxy_url = self.config.get('proxy', '')
        if proxy_url:
            parsed = urlparse(proxy_url)
            proxy_type = 'SOCKS5' if parsed.scheme.startswith('socks') else 'HTTP'
            proxy_host = f"{parsed.hostname}:{parsed.port}" if parsed.hostname else proxy_url
            print(f"{Fore.GREEN}✓ Proxy active: {proxy_type} → {proxy_host}{Style.RESET_ALL}")
            if parsed.scheme.startswith('socks') and not HAS_AIOHTTP_SOCKS:
                print(f"{Fore.RED}⚠ aiohttp_socks missing! SOCKS Proxy will not work!{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}  Install with: py -m pip install aiohttp_socks{Style.RESET_ALL}")
        else:
            if self.account_name:
                print(f"{Fore.YELLOW}⚠ No proxy set (recommended for Multi-Acc! Config → [Y]){Style.RESET_ALL}")
        print()
        
        try:
            # Ready-Event erstellen (muss im async context sein)
            self.ready_event = asyncio.Event()
            
            login_task = asyncio.create_task(self.client.start(self.config['token']))
            
            # Warte bis on_ready gefeuert hat (max 30 Sekunden)
            print(f"{Fore.YELLOW}Waiting for login...{Style.RESET_ALL}")
            
            # Give login a moment to fail fast before waiting the full 30s
            await asyncio.sleep(3)
            if login_task.done() and login_task.exception():
                exc = login_task.exception()
                if 'LoginFailure' in type(exc).__name__ or 'Unauthorized' in str(exc):
                    print(f"\n{Fore.RED}{'═' * 66}{Style.RESET_ALL}")
                    print(f"{Fore.RED}  LOGIN FAILED - Invalid Token{Style.RESET_ALL}")
                    print(f"{Fore.RED}{'═' * 66}{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}  Your Discord user token in your config file ({self.config_path}){Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}  is either invalid, expired, or incorrect.{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}  Replace it with your current, valid Discord user token.{Style.RESET_ALL}")
                    print(f"{Fore.RED}{'═' * 66}{Style.RESET_ALL}\n")
                    input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                    return
            
            try:
                await asyncio.wait_for(self.ready_event.wait(), timeout=27)
            except asyncio.TimeoutError:
                # Check if the login task failed with LoginFailure
                if login_task.done() and login_task.exception():
                    exc = login_task.exception()
                    if 'LoginFailure' in type(exc).__name__ or 'Unauthorized' in str(exc):
                        print(f"\n{Fore.RED}{'���' * 66}{Style.RESET_ALL}")
                        print(f"{Fore.RED}  LOGIN FAILED - Invalid Token{Style.RESET_ALL}")
                        print(f"{Fore.RED}{'═' * 66}{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}  Your Discord user token in your config file ({self.config_path}){Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}  is either invalid, expired, or incorrect.{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}  Replace it with your current, valid Discord user token.{Style.RESET_ALL}")
                        print(f"{Fore.RED}{'═' * 66}{Style.RESET_ALL}\n")
                        input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                        return
                print(f"{Fore.RED}Error: Login Timeout (30s)! Check your token.{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return
            
            # Kurz warten damit alle Channels gecacht werden
            await asyncio.sleep(2)
            
            # Hole Channel (mehrere Versuche)
            channel = None
            for attempt in range(5):
                channel = self.client.get_channel(int(self.config['channel_id']))
                if channel:
                    break
                self.log(f"Channel not found, attempt {attempt + 1}/5...")
                print(f"{Fore.YELLOW}Channel not found, attempt {attempt + 1}/5...{Style.RESET_ALL}")
                await asyncio.sleep(2)
            
            if not channel:
                # Fallback: Channel über API holen (nicht nur aus Cache)
                try:
                    channel = await self.client.fetch_channel(int(self.config['channel_id']))
                    if channel:
                        self.log(f"Channel found via API: {channel.name}")
                except Exception as e:
                    self.log(f"fetch_channel also failed: {str(e)}")
            
            if not channel:
                print(f"{Fore.RED}Error: Channel not found after 5 attempts!{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Channel ID: {self.config['channel_id']}{Style.RESET_ALL}")
                input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
                return
            
            self.running = True
            self.paused = False
            self.captcha_active = False
            self.captcha_solve_attempts = 0
            self.captcha_last_message = None
            self.egg_busy = False
            self.temp_banned = False
            self.buying_balls = False
            self.catch_limit_reached = False
            self.releasing = False
            self.release_counter = 0
            self.doing_dailys = False
            
            # Session-Stats zuruecksetzen
            self.session_stats = {
                'total_caught': 0,
                'total_fled': 0,
                'total_encounters': 0,
                'total_fished': 0,
                'total_fished_fled': 0,
                'caught_by_rarity': {},
                'fled_by_rarity': {},
                'best_catches': [],
                'session_start': datetime.now(),
            }
            self.persistent_stats['sessions'] = self.persistent_stats.get('sessions', 0) + 1
            self.save_persistent_stats()
            
            # Starte Hotkey-Listener als parallelen Task
            hotkey_task = asyncio.create_task(self.hotkey_listener())
            
            if with_dailys:
                await self.run_daily_tasks(channel)
            else:
                print(f"{Fore.YELLOW}Daily Tasks skipped (start with [2] for Dailys){Style.RESET_ALL}\n")
            
            # === Startup Inventory Check: ;inv -> parse -> conditionally ;lb all / ;grazz all ===
            wants_lootbox = self.config.get('startup_lootbox', False)
            wants_grazz = self.config.get('startup_grazz', False)
            
            if wants_lootbox or wants_grazz:
                await asyncio.sleep(3)
                print(f"{Fore.MAGENTA}[{datetime.now().strftime('%H:%M:%S')}] Checking inventory...{Style.RESET_ALL}")
                # Start listening BEFORE sending the command to avoid race condition
                # (PokeMeow may respond before wait_for starts if we send first)
                inv_future = asyncio.ensure_future(
                    self.wait_for_message_return(channel, 'item inventory', timeout=15)
                )
                await asyncio.sleep(0.3)
                await self.send_command(channel, ';inv')
                self.log("Startup: ;inv sent")
                
                inv_response = await inv_future
                
                inv_lootboxes = 0
                inv_grazz = 0
                
                if inv_response and inv_response.embeds:
                    inv_text = ''
                    for embed in inv_response.embeds:
                        embed_dict = embed.to_dict()
                        if 'description' in embed_dict:
                            inv_text += str(embed_dict['description']) + '\n'
                        for field in embed_dict.get('fields', []):
                            inv_text += str(field.get('name', '')) + ' ' + str(field.get('value', '')) + '\n'
                        # Also check author
                        author = embed_dict.get('author', {})
                        if 'name' in author:
                            inv_text += str(author['name']) + '\n'
                    
                    # Strip markdown bold markers (**text**) so regex can match numbers
                    inv_text_clean = inv_text.replace('**', '')
                    inv_text_lower = inv_text_clean.lower()
                    
                    # Parse lootbox count: "12x Lootboxes"
                    lootbox_match = re.search(r'([\d,]+)x\s*lootbox', inv_text_lower)
                    if lootbox_match:
                        inv_lootboxes = int(lootbox_match.group(1).replace(',', ''))
                    
                    # Parse grazz count: "1x GRazz Berries"
                    grazz_match = re.search(r'([\d,]+)x\s*grazz\s*berr', inv_text_lower)
                    if grazz_match:
                        inv_grazz = int(grazz_match.group(1).replace(',', ''))
                    
                    # Parse ball counts
                    ball_counts = {}
                    ball_names_map = {
                        'pb': ('poke ball', 'Pokeballs'),
                        'gb': ('great ball', 'Greatballs'),
                        'ub': ('ultra ball', 'Ultraballs'),
                        'mb': ('master ball', 'Masterballs'),
                    }
                    # Note: Premier Balls excluded - cannot be purchased
                    for ball_key, (ball_pattern, ball_display) in ball_names_map.items():
                        ball_match = re.search(r'([\d,]+)x\s*' + ball_pattern, inv_text_lower)
                        if ball_match:
                            ball_counts[ball_key] = int(ball_match.group(1).replace(',', ''))
                    
                    # Parse other items
                    honey_match = re.search(r'([\d,]+)x\s*honey', inv_text_lower)
                    inv_honey = int(honey_match.group(1).replace(',', '')) if honey_match else 0
                    incense_match = re.search(r'([\d,]+)x\s*incense', inv_text_lower)
                    inv_incense = int(incense_match.group(1).replace(',', '')) if incense_match else 0
                    repel_match = re.search(r'([\d,]+)x\s*repel', inv_text_lower)
                    inv_repels = int(repel_match.group(1).replace(',', '')) if repel_match else 0
                    
                    # Get autobuyer config for threshold comparison
                    autobuyer = self.config.get('autobuyer', {})
                    ts = datetime.now().strftime('%H:%M:%S')
                    
                    # Print header
                    print(f"{Fore.CYAN}[{ts}] === Inventory Check ==={Style.RESET_ALL}")
                    
                    # Print each ball with AutoBuy status
                    for ball_key, (ball_pattern, ball_display) in ball_names_map.items():
                        count = ball_counts.get(ball_key, 0)
                        ab_settings = autobuyer.get(ball_key, {})
                        ab_threshold = ab_settings.get('threshold', 10)
                        ab_amount = ab_settings.get('amount', 0)
                        
                        if ab_amount > 0:
                            if count <= ab_threshold:
                                status = f"{Fore.RED}AutoBuy will trigger (threshold: {ab_threshold}){Style.RESET_ALL}"
                            else:
                                status = f"{Fore.GREEN}OK (AutoBuy threshold: {ab_threshold}){Style.RESET_ALL}"
                        else:
                            status = f"{Fore.YELLOW}no AutoBuy configured{Style.RESET_ALL}"
                        
                        print(f"{Fore.CYAN}[{ts}]   {ball_display}: {count} --> {status}")
                    
                    # Print items
                    print(f"{Fore.CYAN}[{ts}]   Lootboxes: {inv_lootboxes} | GRazz: {inv_grazz} | Honey: {inv_honey} | Incense: {inv_incense} | Repels: {inv_repels}{Style.RESET_ALL}")
                    
                    self.log(f"Startup Inventory: PB:{ball_counts.get('pb',0)} GB:{ball_counts.get('gb',0)} UB:{ball_counts.get('ub',0)} MB:{ball_counts.get('mb',0)} | LB:{inv_lootboxes} GRazz:{inv_grazz}")
                else:
                    self.log("Startup: No inventory response received, skipping ;lb all / ;grazz all")
                    print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] No inventory response, skipping startup commands.{Style.RESET_ALL}")
                
                # Open lootboxes if any exist
                if wants_lootbox and inv_lootboxes > 0:
                    await asyncio.sleep(3)
                    print(f"{Fore.MAGENTA}[{datetime.now().strftime('%H:%M:%S')}] Opening {inv_lootboxes} Lootboxes...{Style.RESET_ALL}")
                    await self.send_command(channel, ';lb all')
                    self.log(f"Startup: ;lb all sent ({inv_lootboxes} lootboxes)")
                    await asyncio.sleep(3)
                elif wants_lootbox:
                    print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] No Lootboxes found, skipping ;lb all{Style.RESET_ALL}")
                
                # Use grazz berries if any exist
                if wants_grazz and inv_grazz > 0:
                    await asyncio.sleep(3)
                    print(f"{Fore.MAGENTA}[{datetime.now().strftime('%H:%M:%S')}] Using {inv_grazz} GRazz Berries...{Style.RESET_ALL}")
                    await self.send_command(channel, ';grazz all')
                    self.log(f"Startup: ;grazz all sent ({inv_grazz} grazz berries)")
                    await asyncio.sleep(3)
                elif wants_grazz:
                    print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] No GRazz Berries found, skipping ;grazz all{Style.RESET_ALL}")
            
            # Egg beim Start: check status first, then hatch/hold only if needed
            if self.config.get('egg_enabled', False):
                # Wait before egg check so PokeMeow doesn't ignore rapid commands
                await asyncio.sleep(3)
                print(f"{Fore.MAGENTA}[{datetime.now().strftime('%H:%M:%S')}] Egg check on startup...{Style.RESET_ALL}")
                
                # Try to hatch (in case one is ready from before)
                await self.send_command(channel, ';egg hatch')
                self.log(";egg hatch sent on startup (checking if one is ready)")
                
                # Wait for PokeMeow response and check what it says
                hatch_response = await self.wait_for_message_return(channel, '', timeout=10)
                hatch_text = ""
                if hatch_response:
                    if hatch_response.content:
                        hatch_text += hatch_response.content.lower()
                    if hatch_response.embeds:
                        for embed in hatch_response.embeds:
                            embed_dict = embed.to_dict()
                            if 'description' in embed_dict:
                                hatch_text += str(embed_dict['description']).lower()
                            if 'title' in embed_dict:
                                hatch_text += str(embed_dict['title']).lower()
                
                if 'not ready to hatch' in hatch_text:
                    # Egg exists but not ready - already holding one, skip ;egg hold
                    self.log("Egg not ready yet, already holding one - skipping ;egg hold")
                    print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] Egg not ready yet (already holding one){Style.RESET_ALL}")
                elif "aren't holding" in hatch_text or "not holding" in hatch_text:
                    # No egg held - try to equip one
                    self.log("No egg held, trying to equip one...")
                    await asyncio.sleep(4)
                    await self.send_command(channel, ';egg hold')
                    self.log(";egg hold sent on startup")
                    await asyncio.sleep(4)
                elif 'just hatched a' in hatch_text:
                    # Egg hatched successfully! Extract Pokemon name
                    hatched_name = "Unknown"
                    if hatch_response:
                        full_text = ""
                        if hatch_response.content:
                            full_text += hatch_response.content
                        if hatch_response.embeds:
                            for embed in hatch_response.embeds:
                                embed_dict = embed.to_dict()
                                if 'description' in embed_dict:
                                    full_text += str(embed_dict['description']) + " "
                        # Clean: remove EXP/level lines that contain other Pokemon names
                        clean_lines = []
                        for line in full_text.split('\n'):
                            line_lower = line.strip().lower()
                            if ' gained ' in line_lower or ' is now level' in line_lower or 'congratulations' in line_lower:
                                continue
                            clean_lines.append(line)
                        full_text_clean = ' '.join(clean_lines)
                        
                        hatch_match = re.search(r'just hatched a\s+(?:[^\w]*\s*)?([A-Z][a-zA-Z\s\-\'\.]+?)(?:\s*!|\s*You|\s*\*)', full_text_clean)
                        if hatch_match:
                            hatched_name = hatch_match.group(1).strip()
                        elif hasattr(self, 'pokemon_names') and self.pokemon_names:
                            for pname in self.pokemon_names:
                                if pname.lower() in full_text_clean.lower():
                                    hatched_name = pname
                                    break
                    
                    # Shiny detection for startup egg hatch
                    startup_hatch_shiny = 'shiny' in hatch_text.lower()
                    if startup_hatch_shiny and hatched_name.lower().startswith('shiny '):
                        hatched_name = hatched_name[6:].strip()
                    
                    if startup_hatch_shiny:
                        self.log(f"Egg hatched on startup! **Shiny {hatched_name}**!")
                        print(f"\n{Fore.LIGHTMAGENTA_EX}{'*' * 66}{Style.RESET_ALL}")
                        print(f"{Fore.LIGHTMAGENTA_EX}  \u2728\u2728  SHINY EGG HATCH (startup)! **Shiny {hatched_name}**!  \u2728\u2728{Style.RESET_ALL}")
                        print(f"{Fore.LIGHTMAGENTA_EX}{'*' * 66}{Style.RESET_ALL}")
                        # Track shiny in persistent stats
                        now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
                        self.persistent_stats['shinys_caught'] += 1
                        self.persistent_stats['shiny_list'].append({
                            'name': f"{hatched_name} (Egg)", 'date': now_str, 'rarity': 'Shiny (Egg Hatch)'
                        })
                    else:
                        self.log(f"Egg hatched on startup! Pokemon: {hatched_name}")
                        print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] Egg hatched on startup! -> {Fore.MAGENTA}{hatched_name}{Style.RESET_ALL}")
                    
                    # Track egg stats
                    self.persistent_stats['eggs_hatched'] = self.persistent_stats.get('eggs_hatched', 0) + 1
                    egg_pokemon_list = self.persistent_stats.get('egg_pokemon_list', [])
                    egg_pokemon_list.append({
                        'name': hatched_name,
                        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
                        'shiny': startup_hatch_shiny
                    })
                    self.persistent_stats['egg_pokemon_list'] = egg_pokemon_list
                    egg_rarity_stats = self.persistent_stats.get('egg_rarity_stats', {})
                    if startup_hatch_shiny:
                        egg_rarity_stats['Shiny'] = egg_rarity_stats.get('Shiny', 0) + 1
                    else:
                        egg_rarity_stats['Normal'] = egg_rarity_stats.get('Normal', 0) + 1
                    self.persistent_stats['egg_rarity_stats'] = egg_rarity_stats
                    self.save_persistent_stats()
                    
                    # Send egg hatch to shared webhook
                    self.send_egg_hatch_webhook(hatched_name, hatch_response, is_shiny=startup_hatch_shiny)
                    # Send egg hatch to private/config webhook
                    self.send_egg_hatch_private_webhook(hatched_name, is_shiny=startup_hatch_shiny, original_message=hatch_response)
                    # Equip a new egg
                    await asyncio.sleep(4)
                    await self.send_command(channel, ';egg hold')
                    self.log(";egg hold sent after hatching on startup")
                    await asyncio.sleep(4)
                else:
                    # Unknown response or timeout - try ;egg hold as fallback
                    self.log("Unknown hatch response on startup, trying ;egg hold as fallback")
                    await asyncio.sleep(4)
                    await self.send_command(channel, ';egg hold')
                    self.log(";egg hold sent on startup (fallback)")
                    await asyncio.sleep(4)
            
            await self.run_main_loop(channel)
            
            # Cleanup
            hotkey_task.cancel()
            self.save_logs_on_stop()
            
            # Discord-Verbindung sauber schließen
            try:
                await self.client.close()
            except Exception:
                pass
            
        except discord.LoginFailure:
            print(f"{Fore.RED}Error: Login failed! Check your token.{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
        finally:
            # Immer sauber aufräumen
            try:
                if not self.client.is_closed():
                    await self.client.close()
            except Exception:
                pass
    
    # ═══════════════════════════════════════════════════════════════════
    #  HAUPTPROGRAMM
    # ═══════════════════════════════════════════════════════════════════
    
    def run(self):
        """Hauptprogramm"""
        while True:
            self.show_main_menu()
            choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            if choice == '1':
                try:
                    asyncio.run(self.start_bot(with_dailys=False))
                except KeyboardInterrupt:
                    self.running = False
                    self.save_logs_on_stop()
                    print(f"\n{Fore.YELLOW}Bot stopped.{Style.RESET_ALL}")
                    input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            
            elif choice == '2':
                try:
                    asyncio.run(self.start_bot(with_dailys=True))
                except KeyboardInterrupt:
                    self.running = False
                    self.save_logs_on_stop()
                    print(f"\n{Fore.YELLOW}Bot stopped.{Style.RESET_ALL}")
                    input(f"{Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            
            elif choice == '3':
                while True:
                    self.show_config_menu()
                    config_choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
                    
                    if config_choice == '1':
                        self.config['auto_catch_enabled'] = not self.config.get('auto_catch_enabled', True)
                    elif config_choice == '2':
                        # Ball-Regeln (war vorher [7])
                        while True:
                            self.show_ball_rules_menu()
                            ball_choice = input(f"                    {Fore.CYAN}Choose a Rarity: {Style.RESET_ALL}")
                            
                            rarity_map = {
                                '1': 'common', '2': 'uncommon', '3': 'rare', 
                                '4': 'super_rare', '5': 'legendary', '6': 'shiny'
                            }
                            
                            if ball_choice in rarity_map:
                                rarity = rarity_map[ball_choice]
                                ball = input(f"           {Fore.CYAN}Ball for {rarity} (pb/gb/ub/prb/mb): {Style.RESET_ALL}").lower()
                                if ball in ['pb', 'gb', 'ub', 'prb', 'mb']:
                                    self.config['catch_rules'][rarity] = ball
                                    print(f"           {Fore.GREEN}Saved!{Style.RESET_ALL}")
                                    time_module.sleep(1)
                                else:
                                    print(f"           {Fore.RED}Invalid ball!{Style.RESET_ALL}")
                                    time_module.sleep(1)
                            elif ball_choice.lower() == 'e':
                                event_cfg = self.config.get('event_pokemon', {})
                                current_ball = event_cfg.get('event_ball_lower', 'prb')
                                ball_names_map = {'pb': 'Pokeball', 'gb': 'Greatball', 'ub': 'Ultraball', 'prb': 'Premierball', 'mb': 'Masterball'}
                                enabled = event_cfg.get('premierball_enabled', True)
                                print(f"\n           {Fore.YELLOW}Event (Common-Super Rare){Style.RESET_ALL}")
                                print(f"           Status: {'ON' if enabled else 'OFF'}  |  Ball: {ball_names_map.get(current_ball, current_ball)}")
                                print(f"           Enter ball (pb/gb/ub/prb/mb) or 'off'/'on' to toggle:")
                                ev_input = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip().lower()
                                if ev_input == 'off':
                                    event_cfg['premierball_enabled'] = False
                                    self.config['event_pokemon'] = event_cfg
                                    print(f"           {Fore.GREEN}Event (Common-Super Rare) override disabled!{Style.RESET_ALL}")
                                elif ev_input == 'on':
                                    event_cfg['premierball_enabled'] = True
                                    self.config['event_pokemon'] = event_cfg
                                    print(f"           {Fore.GREEN}Event (Common-Super Rare) override enabled!{Style.RESET_ALL}")
                                elif ev_input in ('pb', 'gb', 'ub', 'prb', 'mb'):
                                    event_cfg['event_ball_lower'] = ev_input
                                    event_cfg['premierball_enabled'] = True
                                    self.config['event_pokemon'] = event_cfg
                                    print(f"           {Fore.GREEN}Event (Common-Super Rare) -> {ball_names_map[ev_input]}!{Style.RESET_ALL}")
                                else:
                                    print(f"           {Fore.RED}Invalid! Use pb/gb/ub/prb/mb or on/off.{Style.RESET_ALL}")
                                time_module.sleep(1)
                            elif ball_choice.lower() == 'v':
                                event_cfg = self.config.get('event_pokemon', {})
                                current_ball = event_cfg.get('event_ball_upper', 'mb')
                                ball_names_map = {'pb': 'Pokeball', 'gb': 'Greatball', 'ub': 'Ultraball', 'prb': 'Premierball', 'mb': 'Masterball'}
                                enabled = event_cfg.get('masterball_enabled', True)
                                print(f"\n           {Fore.YELLOW}Event (Legendary & Shiny){Style.RESET_ALL}")
                                print(f"           Status: {'ON' if enabled else 'OFF'}  |  Ball: {ball_names_map.get(current_ball, current_ball)}")
                                print(f"           Enter ball (pb/gb/ub/prb/mb) or 'off'/'on' to toggle:")
                                ev_input = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip().lower()
                                if ev_input == 'off':
                                    event_cfg['masterball_enabled'] = False
                                    self.config['event_pokemon'] = event_cfg
                                    print(f"           {Fore.GREEN}Event (Legendary & Shiny) override disabled!{Style.RESET_ALL}")
                                elif ev_input == 'on':
                                    event_cfg['masterball_enabled'] = True
                                    self.config['event_pokemon'] = event_cfg
                                    print(f"           {Fore.GREEN}Event (Legendary & Shiny) override enabled!{Style.RESET_ALL}")
                                elif ev_input in ('pb', 'gb', 'ub', 'prb', 'mb'):
                                    event_cfg['event_ball_upper'] = ev_input
                                    event_cfg['masterball_enabled'] = True
                                    self.config['event_pokemon'] = event_cfg
                                    print(f"           {Fore.GREEN}Event (Legendary & Shiny) -> {ball_names_map[ev_input]}!{Style.RESET_ALL}")
                                else:
                                    print(f"           {Fore.RED}Invalid! Use pb/gb/ub/prb/mb or on/off.{Style.RESET_ALL}")
                                time_module.sleep(1)
                            elif ball_choice == '7':
                                self.config['catch_rules'] = {
                                    'common': 'pb', 'uncommon': 'pb', 'rare': 'gb',
                                    'super_rare': 'ub', 'legendary': 'mb', 'shiny': 'mb',
                                    'golden': 'mb'
                                }
                                self.config['event_pokemon'] = {
                                    'premierball_enabled': True,
                                    'masterball_enabled': True,
                                    'webhook_enabled': True,
                                    'event_ball_lower': 'prb',
                                    'event_ball_upper': 'mb',
                                }
                                print(f"           {Fore.GREEN}Default rules restored!{Style.RESET_ALL}")
                                time_module.sleep(1)
                            elif ball_choice.lower() == 'w':
                                self.handle_pokemon_whitelist_config()
                            elif ball_choice == '0':
                                break
                            
                            self.save_config()
                    elif config_choice == '3':
                        self.config['fish_enabled'] = not self.config['fish_enabled']
                        state = "enabled" if self.config['fish_enabled'] else "disabled"
                        fish_iv = self.config.get('fish_interval', 2)
                        print(f"           {Fore.GREEN}Fish (;f) {state}! Fires every {fish_iv}x ;p.{Style.RESET_ALL}")
                        time_module.sleep(1)
                    elif config_choice == '4':
                        fish_iv = self.config.get('fish_interval', 2)
                        print(f"\n           {Fore.CYAN}Fish Interval – ;f fires after every Nx ;p{Style.RESET_ALL}")
                        print(f"           {Fore.YELLOW}Current: every {fish_iv}x ;p{Style.RESET_ALL}")
                        iv_input = input(f"           {Fore.CYAN}New interval (2-10): {Style.RESET_ALL}").strip()
                        try:
                            iv = int(iv_input)
                            if 2 <= iv <= 10:
                                self.config['fish_interval'] = iv
                                print(f"           {Fore.GREEN}Fish interval set to every {iv}x ;p!{Style.RESET_ALL}")
                            else:
                                print(f"           {Fore.RED}Invalid! Must be between 2 and 10.{Style.RESET_ALL}")
                        except ValueError:
                            print(f"           {Fore.RED}Invalid input! Enter a number (2-10).{Style.RESET_ALL}")
                        time_module.sleep(1)
                    elif config_choice.lower() == 'f':
                        self.handle_captcha_config()
                    elif config_choice.lower() == 'x':
                        ar = self.config.get('auto_release', {'enabled': False, 'interval': 50})
                        ar['enabled'] = not ar.get('enabled', False)
                        self.config['auto_release'] = ar
                        state = "enabled" if ar['enabled'] else "disabled"
                        print(f"           {Fore.GREEN}Auto-Release {state}!{Style.RESET_ALL}")
                        if ar['enabled']:
                            print(f"           {Fore.YELLOW}Sends ';release duplicates' every {ar.get('interval', 50)} catches.{Style.RESET_ALL}")
                            print(f"           {Fore.YELLOW}Keeps Legendary & Shiny automatically!{Style.RESET_ALL}")
                        time_module.sleep(2)
                    elif config_choice.lower() == 'v':
                        ar = self.config.get('auto_release', {'enabled': False, 'interval': 50})
                        print(f"\n           {Fore.CYAN}Auto-Release Interval (every X Catches){Style.RESET_ALL}")
                        print(f"           {Fore.YELLOW}Current: every {ar.get('interval', 50)} catches{Style.RESET_ALL}")
                        print(f"           {Fore.YELLOW}';release duplicates' releases all duplicate Pokemon{Style.RESET_ALL}")
                        print(f"           {Fore.YELLOW}(Legendary & Shiny will NOT be released!){Style.RESET_ALL}")
                        interval_input = input(f"           {Fore.CYAN}Interval (10-200): {Style.RESET_ALL}").strip()
                        try:
                            interval = int(interval_input)
                            if 10 <= interval <= 200:
                                ar['interval'] = interval
                                self.config['auto_release'] = ar
                                print(f"           {Fore.GREEN}Interval set to {interval} catches!{Style.RESET_ALL}")
                            else:
                                print(f"           {Fore.RED}Invalid! Must be between 10 and 200.{Style.RESET_ALL}")
                        except ValueError:
                            print(f"           {Fore.RED}Invalid input! Enter a number (10-200).{Style.RESET_ALL}")
                        time_module.sleep(1)
                    elif config_choice.lower() == 't':
                        self.config['startup_lootbox'] = not self.config.get('startup_lootbox', False)
                        state = "enabled" if self.config['startup_lootbox'] else "disabled"
                        print(f"           {Fore.GREEN}Startup Lootbox opener {state}!{Style.RESET_ALL}")
                        if self.config['startup_lootbox']:
                            print(f"           {Fore.YELLOW}Will send ';lb all' on startup to open all lootboxes.{Style.RESET_ALL}")
                        time_module.sleep(1)
                    elif config_choice.lower() == 'i':
                        self.config['startup_grazz'] = not self.config.get('startup_grazz', False)
                        state = "enabled" if self.config['startup_grazz'] else "disabled"
                        print(f"           {Fore.GREEN}Startup Razz Berries {state}!{Style.RESET_ALL}")
                        if self.config['startup_grazz']:
                            print(f"           {Fore.YELLOW}Will send ';grazz all' on startup to use all razz berries.{Style.RESET_ALL}")
                        time_module.sleep(1)
                    elif config_choice.lower() == 'e':
                        self.config['egg_enabled'] = not self.config.get('egg_enabled', False)
                    elif config_choice.lower() == 'q':
                        self.handle_quest_settings_menu()
                    elif config_choice.lower() == 'a':
                        self.handle_anti_ban_config()
                    elif config_choice.lower() == 'm':
                        self.handle_custom_message_config()
                    elif config_choice.lower() == 'n':
                        self.handle_custom_message_fish_config()
                    elif config_choice.lower() == 'r':
                        self.handle_rate_limit_config()
                    elif config_choice.lower() == 'c':
                        self.handle_remote_control_config()
                    elif config_choice.lower() == 'b':
                        self.handle_autobuyer_config()
                    elif config_choice.lower() == 'w':
                        self.handle_webhook_config()
                    elif config_choice == '8':
                        token = input(f"           {Fore.CYAN}Enter your Discord Token: {Style.RESET_ALL}")
                        self.config['token'] = token
                        print(f"           {Fore.GREEN}Token saved!{Style.RESET_ALL}")
                        time_module.sleep(1)
                    elif config_choice == '9':
                        channel_id = input(f"           {Fore.CYAN}Enter the Channel ID: {Style.RESET_ALL}")
                        self.config['channel_id'] = channel_id
                        print(f"           {Fore.GREEN}Channel ID saved!{Style.RESET_ALL}")
                        time_module.sleep(1)
                    elif config_choice.lower() == 'y':
                        print(f"\n           {Fore.CYAN}Proxy Settings{Style.RESET_ALL}")
                        print(f"           {Fore.YELLOW}Recommended for Multi-Account: Each account its own IP!{Style.RESET_ALL}")
                        print(f"\n           {Fore.YELLOW}Supported Formats:{Style.RESET_ALL}")
                        print(f"           • http://host:port")
                        print(f"           -> http://user:pass@host:port")
                        print(f"           • socks5://host:port")
                        print(f"           • socks5://user:pass@host:port")
                        current = self.config.get('proxy', '')
                        if current:
                            print(f"\n           {Fore.GREEN}Current: {current}{Style.RESET_ALL}")
                            print(f"           {Fore.YELLOW}Leave empty to remove proxy.{Style.RESET_ALL}")
                        proxy_input = input(f"\n           {Fore.CYAN}Proxy URL (or empty to remove): {Style.RESET_ALL}").strip()
                        if proxy_input:
                            # Validierung
                            parsed = urlparse(proxy_input)
                            if parsed.scheme in ('http', 'https', 'socks4', 'socks5', 'socks5h') and parsed.hostname:
                                self.config['proxy'] = proxy_input
                                proxy_type = 'SOCKS5' if parsed.scheme.startswith('socks') else 'HTTP'
                                print(f"           {Fore.GREEN}{proxy_type} Proxy saved: {parsed.hostname}:{parsed.port}{Style.RESET_ALL}")
                                if parsed.scheme.startswith('socks') and not HAS_AIOHTTP_SOCKS:
                                    print(f"           {Fore.RED}⚠ Install aiohttp_socks for SOCKS support:{Style.RESET_ALL}")
                                    print(f"           {Fore.YELLOW}  py -m pip install aiohttp_socks{Style.RESET_ALL}")
                            else:
                                print(f"           {Fore.RED}Invalid format! Use e.g. http://host:port{Style.RESET_ALL}")
                        else:
                            self.config['proxy'] = ''
                            print(f"           {Fore.GREEN}Proxy removed!{Style.RESET_ALL}")
                        time_module.sleep(2)
                    elif config_choice.lower() == 'z':
                        self.check_ip()
                    elif config_choice == '0':
                        self.save_config()
                        break
                    
                    self.save_config()
            
            elif choice == '4':
                self.show_logs()
            
            elif choice == '5':
                self.save_logs_on_stop()
                print(f"\n{Fore.YELLOW}Goodbye!{Style.RESET_ALL}")
                sys.exit(0)

