"""Interactive console menus: main menu, config menu, ball rules, Pokemon whitelist, update checker."""
import os
import sys
import re
import json
import asyncio
import random
import threading
import time as time_module
from datetime import datetime, timedelta
from urllib.parse import urlparse

import discord
from colorama import Fore, Style


class MenuMixin:
    def show_main_menu(self):
        """Zeigt das Hauptmenü"""
        self.print_header()
        print(f"\n{Fore.YELLOW}{'═' * 66}{Style.RESET_ALL}")
        print(f"{Fore.GREEN}                         [1]{Style.RESET_ALL} Start")
        print(f"{Fore.GREEN}                         [2]{Style.RESET_ALL} Start + Daily Tasks")
        print(f"{Fore.GREEN}                         [3]{Style.RESET_ALL} Config")
        print(f"{Fore.GREEN}                         [4]{Style.RESET_ALL} Logs")
        print(f"{Fore.RED}                         [5]{Style.RESET_ALL} Exit")
        print(f"{Fore.YELLOW}{'═' * 66}{Style.RESET_ALL}\n")
    
    def show_config_menu(self):
        """Zeigt das Konfigurations-Menü"""
        self.print_header()
        print(f"\n{Fore.CYAN}╔═══════════════════════ CONFIGURATION ═══════════════════════╗{Style.RESET_ALL}")
        
        def status(enabled):
            return f"{Fore.GREEN}✓{Style.RESET_ALL}" if enabled else f"{Fore.RED}✗{Style.RESET_ALL}"
        
        print(f"\n           {Fore.YELLOW}═══ Auto-Catch ═══{Style.RESET_ALL}")
        print(f"           [1] {status(self.config.get('auto_catch_enabled', True))} Enable Auto-Catch")
        print(f"           [2] Adjust Ball Rules")
        fish_iv = self.config.get('fish_interval', 2)
        print(f"           [3] {status(self.config['fish_enabled'])} Fish (;f) after every {fish_iv}x ;p")
        if self.config['fish_enabled']:
            print(f"           [4] Fish Interval: every {fish_iv}x ;p  (min 2 / max 10)")
        
        print(f"\n           {Fore.YELLOW}═══ AutoEgg ═══{Style.RESET_ALL}")
        print(f"           [E] {status(self.config.get('egg_enabled', False))} Egg Auto-Hatch (;egg)")
        
        ab = self.config.get('autobuyer', {})
        print(f"\n           {Fore.YELLOW}=== AutoBuyer ==={Style.RESET_ALL}")
        print(f"           [B] {status(ab.get('enabled', False))} AutoBuyer Settings ->")
        
        wh = self.config.get('webhook', {})
        print(f"\n           {Fore.YELLOW}=== Webhook ==={Style.RESET_ALL}")
        print(f"           [W] {status(wh.get('enabled', False))} Webhook Settings ->")
        
        auto_solve_on = self.config.get('auto_solve_captcha', False)
        service_name = self.get_captcha_service_name()
        print(f"\n           {Fore.YELLOW}=== Captcha ==={Style.RESET_ALL}")
        print(f"           [F] {status(auto_solve_on)} Captcha Settings -> ({service_name})")
        
        ar = self.config.get('auto_release', {})
        print(f"\n           {Fore.YELLOW}═══ Auto-Release ═══{Style.RESET_ALL}")
        print(f"           [X] {status(ar.get('enabled', False))} Auto-Release Duplicates (;release duplicates)")
        print(f"           [V] Release Interval: every {ar.get('interval', 50)} Catches")
        
        print(f"\n           {Fore.YELLOW}═══ Startup Commands ═══{Style.RESET_ALL}")
        print(f"           [T] {status(self.config.get('startup_lootbox', False))} Open Lootboxes on start (checks ;inv first)")
        print(f"           [I] {status(self.config.get('startup_grazz', False))} Use GRazz Berries on start (checks ;inv first)")
        
        aqr = self.config.get('auto_quest_renewer', {})
        aqc = self.config.get('auto_quest_claim', {})
        _qstate = aqr.get('enabled', False) or aqc.get('enabled', False)
        _qlabel_bits = []
        if aqr.get('enabled', False): _qlabel_bits.append('Renewer')
        if aqc.get('enabled', False): _qlabel_bits.append('Claimer')
        _qlabel = ', '.join(_qlabel_bits) if _qlabel_bits else 'All OFF'
        print(f"\n           {Fore.YELLOW}═══ Quest Settings ═══{Style.RESET_ALL}")
        print(f"           [Q] {status(_qstate)} Quest Settings -> ({_qlabel})")
        
        ab_cfg = self.config.get('anti_ban', {})
        features = []
        if ab_cfg.get('enabled', False): features.append('Pauses')
        if ab_cfg.get('skip_spawn_enabled', False): features.append('Skip')
        if ab_cfg.get('idle_moments_enabled', False): features.append('Idle')
        if ab_cfg.get('typing_simulation_enabled', False): features.append('Typing')
        if ab_cfg.get('night_mode_enabled', False): features.append('Night')
        feat_str = ', '.join(features) if features else 'All OFF'
        any_on = len(features) > 0
        print(f"\n           {Fore.YELLOW}═══ Anti-Ban Options ═══{Style.RESET_ALL}")
        print(f"           [A] {status(any_on)} Anti-Ban Settings -> ({feat_str})")
        
        cm_cfg = self.config.get('custom_message', {})
        cm_status = status(cm_cfg.get('enabled', False))
        cm_chance = cm_cfg.get('chance', 50)
        cm_msg = cm_cfg.get('message', '')[:20] + '...' if len(cm_cfg.get('message', '')) > 20 else cm_cfg.get('message', '')
        print(f"\n           {Fore.YELLOW}═══ Custom Message ═══{Style.RESET_ALL}")
        print(f"           [M] {cm_status} Custom Message ;p ({cm_chance}% chance) {Fore.CYAN}{cm_msg}{Style.RESET_ALL}")
        
        cmf_cfg = self.config.get('custom_message_fish', {})
        cmf_status = status(cmf_cfg.get('enabled', False))
        cmf_chance = cmf_cfg.get('chance', 50)
        cmf_msg = cmf_cfg.get('message', '')[:20] + '...' if len(cmf_cfg.get('message', '')) > 20 else cmf_cfg.get('message', '')
        print(f"           [N] {cmf_status} Custom Message ;f ({cmf_chance}% chance) {Fore.CYAN}{cmf_msg}{Style.RESET_ALL}")
        
        rl_cfg = self.config.get('rate_limit_protection', {})
        rl_status = status(rl_cfg.get('enabled', True))
        rl_max = rl_cfg.get('max_no_response', 3)
        rl_sleep = f"{rl_cfg.get('sleep_min', 30)}-{rl_cfg.get('sleep_max', 90)}s"
        print(f"\n           {Fore.YELLOW}═══ Rate Limit Protection ═══{Style.RESET_ALL}")
        print(f"           [R] {rl_status} Rate Limit Protection (sleep after {rl_max} no-response, {rl_sleep})")
        
        # Remote Control
        rc = self.config.get('remote_control', {})
        rc_enabled = rc.get('enabled', False)
        rc_status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if rc_enabled else f"{Fore.RED}✗{Style.RESET_ALL}"
        rc_channel = rc.get('control_channel_id', '')
        rc_info = f"(#{rc_channel[-4:]})" if rc_channel else "(not set)"
        print(f"\n           {Fore.YELLOW}═══ Remote Control ═══{Style.RESET_ALL}")
        print(f"           [C] {rc_status} Remote Control Settings -> {rc_info}")
        
        print(f"\n           {Fore.YELLOW}═══ Settings ═══{Style.RESET_ALL}")
        print(f"           [8] Set Token")
        print(f"           [9] Set Channel ID")
        
        # Proxy Anzeige
        proxy_url = self.config.get('proxy', '')
        if proxy_url:
            parsed = urlparse(proxy_url)
            proxy_display = f"{parsed.scheme}://{parsed.hostname}:{parsed.port}" if parsed.hostname else proxy_url
            print(f"           [Y] {Fore.GREEN}✓{Style.RESET_ALL} Proxy: {Fore.GREEN}{proxy_display}{Style.RESET_ALL}")
        else:
            print(f"           [Y] {Fore.RED}✗{Style.RESET_ALL} Set Proxy (recommended for Multi-Acc)")
        print(f"           [Z] IP Check (real IP vs. Proxy IP)")
        
        print(f"           [0] Back")
        print(f"\n{Fore.CYAN}╚═════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
        
        print(f"           {Fore.YELLOW}Token: {Style.RESET_ALL}{'*' * 20 if self.config['token'] and self.config['token'] != 'Your_Discord_Token_Here' else 'Not set'}")
        print(f"           {Fore.YELLOW}Channel ID: {Style.RESET_ALL}{self.config['channel_id'] if self.config['channel_id'] and self.config['channel_id'] != 'Your_Channel_ID_Here' else 'Not set'}")
        
        # Proxy Info
        proxy_url = self.config.get('proxy', '')
        if proxy_url:
            parsed = urlparse(proxy_url)
            proxy_type = 'SOCKS5' if parsed.scheme.startswith('socks') else 'HTTP'
            proxy_masked = f"{parsed.scheme}://"
            if parsed.username:
                proxy_masked += f"{parsed.username}:****@"
            proxy_masked += f"{parsed.hostname}:{parsed.port}" if parsed.hostname else proxy_url
            print(f"           {Fore.YELLOW}Proxy: {Style.RESET_ALL}{Fore.GREEN}{proxy_type} → {proxy_masked}{Style.RESET_ALL}")
            if parsed.scheme.startswith('socks') and not HAS_AIOHTTP_SOCKS:
                print(f"           {Fore.RED}⚠ aiohttp_socks missing! → py -m pip install aiohttp_socks{Style.RESET_ALL}")
        else:
            print(f"           {Fore.YELLOW}Proxy: {Style.RESET_ALL}Not set")
        
        # 2Captcha Key
        api_key_2c = self.config.get('twocaptcha_api_key', '')
        if api_key_2c:
            masked = api_key_2c[:4] + '*' * (len(api_key_2c) - 8) + api_key_2c[-4:] if len(api_key_2c) > 8 else '*' * len(api_key_2c)
            print(f"           {Fore.YELLOW}2Captcha Key: {Style.RESET_ALL}{masked}")
        else:
            print(f"           {Fore.YELLOW}2Captcha Key: {Style.RESET_ALL}Not set")
        
        # Anti-Captcha Key
        api_key_ac = self.config.get('anticaptcha_api_key', '')
        if api_key_ac:
            masked = api_key_ac[:4] + '*' * (len(api_key_ac) - 8) + api_key_ac[-4:] if len(api_key_ac) > 8 else '*' * len(api_key_ac)
            print(f"           {Fore.YELLOW}Anti-Captcha Key: {Style.RESET_ALL}{masked}")
        else:
            print(f"           {Fore.YELLOW}Anti-Captcha Key: {Style.RESET_ALL}Not set")
        
        # Active Service Hinweis
        service = self.config.get('captcha_service', 'manual')
        service_name = self.get_captcha_service_name()
        if service == 'catchbot_ai':
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            model_path = os.path.join(script_dir, 'catchbot_model_onnx')
            encrypted_path = os.path.join(script_dir, 'catchbot_model_onnx_encrypted')
            if os.path.exists(model_path) or os.path.exists(encrypted_path):
                tta_str = "TTA ON" if self.config.get('catchbot_ai_tta', False) else "TTA OFF"
                delay_min = self.config.get('catchbot_ai_delay_min', 7)
                delay_max = self.config.get('catchbot_ai_delay_max', 15)
                enc_str = " [encrypted]" if os.path.exists(encrypted_path) and not os.path.exists(model_path) else ""
                print(f"           {Fore.GREEN}Active Service: CatchBot AI ({tta_str}, {delay_min}-{delay_max}s delay){enc_str} ✓{Style.RESET_ALL}")
            else:
                print(f"           {Fore.RED}Active Service: CatchBot AI (MODEL NOT FOUND!){Style.RESET_ALL}")
        elif service != 'manual':
            active_key = self.get_active_captcha_api_key()
            if active_key:
                print(f"           {Fore.GREEN}Active Service: {service_name} ✓{Style.RESET_ALL}")
            else:
                print(f"           {Fore.RED}Active Service: {service_name} (NO KEY!){Style.RESET_ALL}")
        else:
            print(f"           {Fore.YELLOW}Active Service: Manual (no Auto-Solve){Style.RESET_ALL}")
        print()
    
    def show_ball_rules_menu(self):
        """Zeigt das Ball-Regeln Menü"""
        self.print_header()
        print(f"\n{Fore.CYAN}╔═══════════════════ BALL-REGELN ═══════════════════════╗{Style.RESET_ALL}")
        
        rules = self.config.get('catch_rules', {})
        ball_names = {'pb': 'Pokeball', 'gb': 'Greatball', 'ub': 'Ultraball', 'prb': 'Premierball', 'mb': 'Masterball'}
        
        def status(on):
            return f"{Fore.GREEN}V{Style.RESET_ALL}" if on else f"{Fore.RED}X{Style.RESET_ALL}"
        
        print(f"\n           {Fore.YELLOW}Current Rules:{Style.RESET_ALL}")
        print(f"           [1] Common      -> {ball_names.get(rules.get('common', 'pb'), 'pb')}")
        print(f"           [2] Uncommon    -> {ball_names.get(rules.get('uncommon', 'pb'), 'pb')}")
        print(f"           [3] Rare        -> {ball_names.get(rules.get('rare', 'gb'), 'gb')}")
        print(f"           [4] Super Rare  -> {ball_names.get(rules.get('super_rare', 'ub'), 'ub')}")
        print(f"           [5] Legendary   -> {ball_names.get(rules.get('legendary', 'mb'), 'mb')}")
        print(f"           [6] Shiny       -> {ball_names.get(rules.get('shiny', 'mb'), 'mb')}")
        
        event_cfg = self.config.get('event_pokemon', {})
        event_ball_lower = ball_names.get(event_cfg.get('event_ball_lower', 'prb'), 'Premierball')
        event_ball_upper = ball_names.get(event_cfg.get('event_ball_upper', 'mb'), 'Masterball')
        print(f"\n           {Fore.RED}=== Event Pokemon (Red Embed) ==={Style.RESET_ALL}")
        print(f"           [E] {status(event_cfg.get('premierball_enabled', True))} Event (Common-Super Rare) -> {event_ball_lower}")
        print(f"           [V] {status(event_cfg.get('masterball_enabled', True))} Event (Legendary & Shiny) -> {event_ball_upper}")
        
        print(f"\n           [7] Restore Default Rules")
        
        # Pokemon Whitelist
        whitelist = self.config.get('pokemon_whitelist', {})
        print(f"\n           {Fore.MAGENTA}=== Pokemon Whitelist (Priority Override) ==={Style.RESET_ALL}")
        if whitelist:
            for pname, pball in whitelist.items():
                print(f"           {Fore.WHITE}  {pname} -> {ball_names.get(pball, pball)}{Style.RESET_ALL}")
        else:
            print(f"           {Fore.YELLOW}  (empty){Style.RESET_ALL}")
        print(f"           [W] Manage Whitelist ({len(whitelist)} Pokemon)")
        
        print(f"\n           [0] Back")
        
        print(f"\n{Fore.CYAN}╚════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
        print(f"           {Fore.YELLOW}Available Balls: pb (Pokeball), gb (Greatball),{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}  ub (Ultraball), prb (Premierball), mb (Masterball){Style.RESET_ALL}\n")
    
    def handle_pokemon_whitelist_config(self):
        """Manage Pokemon Whitelist - force specific balls for specific Pokemon names"""
        ball_names = {'pb': 'Pokeball', 'gb': 'Greatball', 'ub': 'Ultraball', 'prb': 'Premierball', 'mb': 'Masterball'}
        
        while True:
            whitelist = self.config.get('pokemon_whitelist', {})
            
            self.print_header()
            print(f"\n{Fore.MAGENTA}{'=' * 20} POKEMON WHITELIST {'=' * 20}{Style.RESET_ALL}")
            print(f"\n           {Fore.YELLOW}Whitelisted Pokemon always use the assigned ball,{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}no matter what rarity or event status they have.{Style.RESET_ALL}")
            
            if whitelist:
                print(f"\n           {Fore.CYAN}Current Whitelist ({len(whitelist)}):{Style.RESET_ALL}")
                for idx, (pname, pball) in enumerate(whitelist.items(), 1):
                    print(f"           {Fore.WHITE}  {idx}. {pname} -> {ball_names.get(pball, pball)}{Style.RESET_ALL}")
            else:
                print(f"\n           {Fore.YELLOW}  (empty - no Pokemon whitelisted){Style.RESET_ALL}")
            
            print(f"\n           [1] Add Pokemon")
            print(f"           [2] Remove Pokemon")
            print(f"           [3] Clear All")
            print(f"           [0] Back")
            print(f"\n{Fore.MAGENTA}{'=' * 58}{Style.RESET_ALL}\n")
            
            choice = input(f"                    {Fore.CYAN}Choose: {Style.RESET_ALL}").strip()
            
            if choice == '1':
                print(f"\n           {Fore.CYAN}Pokemon Name (e.g. Mewtwo, Tapu Koko, Eevee):{Style.RESET_ALL}")
                name = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                if not name:
                    print(f"           {Fore.RED}No name entered!{Style.RESET_ALL}")
                    time_module.sleep(1)
                    continue
                
                # Check if already exists (case-insensitive)
                existing_key = None
                for k in whitelist:
                    if k.lower() == name.lower():
                        existing_key = k
                        break
                
                print(f"           {Fore.CYAN}Ball for {name} (pb/gb/ub/prb/mb):{Style.RESET_ALL}")
                ball = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip().lower()
                if ball not in ('pb', 'gb', 'ub', 'prb', 'mb'):
                    print(f"           {Fore.RED}Invalid ball! Use pb/gb/ub/prb/mb.{Style.RESET_ALL}")
                    time_module.sleep(1)
                    continue
                
                # Remove old key if exists with different case
                if existing_key:
                    del whitelist[existing_key]
                
                whitelist[name] = ball
                self.config['pokemon_whitelist'] = whitelist
                self.save_config()
                action = "Updated" if existing_key else "Added"
                print(f"           {Fore.GREEN}{action}: {name} -> {ball_names[ball]}!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice == '2':
                if not whitelist:
                    print(f"           {Fore.YELLOW}Whitelist is empty!{Style.RESET_ALL}")
                    time_module.sleep(1)
                    continue
                
                print(f"\n           {Fore.CYAN}Enter Pokemon name or number to remove:{Style.RESET_ALL}")
                wl_list = list(whitelist.keys())
                for idx, pname in enumerate(wl_list, 1):
                    print(f"           {idx}. {pname} -> {ball_names.get(whitelist[pname], whitelist[pname])}")
                
                rm_input = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                
                removed = False
                # Try by number
                try:
                    rm_idx = int(rm_input) - 1
                    if 0 <= rm_idx < len(wl_list):
                        rm_name = wl_list[rm_idx]
                        del whitelist[rm_name]
                        removed = True
                        print(f"           {Fore.GREEN}Removed: {rm_name}{Style.RESET_ALL}")
                except ValueError:
                    pass
                
                # Try by name (case-insensitive)
                if not removed:
                    for k in list(whitelist.keys()):
                        if k.lower() == rm_input.lower():
                            del whitelist[k]
                            removed = True
                            print(f"           {Fore.GREEN}Removed: {k}{Style.RESET_ALL}")
                            break
                
                if not removed:
                    print(f"           {Fore.RED}Pokemon not found!{Style.RESET_ALL}")
                else:
                    self.config['pokemon_whitelist'] = whitelist
                    self.save_config()
                time_module.sleep(1)
            
            elif choice == '3':
                if not whitelist:
                    print(f"           {Fore.YELLOW}Already empty!{Style.RESET_ALL}")
                else:
                    confirm = input(f"           {Fore.RED}Clear all {len(whitelist)} entries? (y/n): {Style.RESET_ALL}").strip().lower()
                    if confirm == 'y':
                        self.config['pokemon_whitelist'] = {}
                        self.save_config()
                        print(f"           {Fore.GREEN}Whitelist cleared!{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice == '0':
                break
    
    def show_update_checker(self):
        """Checks GitHub Releases for a newer version and offers to open the download page."""
        import re as _re
        self.print_header()
        print(f"\n{Fore.CYAN}+================== UPDATE CHECKER =======================+{Style.RESET_ALL}\n")
        print(f"           {Fore.YELLOW}Current Version: {self.CATCHBOT_VERSION}{Style.RESET_ALL}\n")
        print(f"           {Fore.YELLOW}Checking for updates...{Style.RESET_ALL}", end="", flush=True)

        _GH_API = "https://api.github.com/repos/MyNameIsKillua/pokemeow-selfbot/releases/latest"
        _GH_RELEASES = "https://github.com/MyNameIsKillua/pokemeow-selfbot/releases/latest"

        try:
            import requests as _req
            r = _req.get(_GH_API, timeout=15, headers={"Accept": "application/vnd.github+json"})
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"\n\n           {Fore.RED}Failed to check for updates: {e}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}+=========================================================+{Style.RESET_ALL}\n")
            input(f"           {Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
            return

        tag = data.get("tag_name", "")
        release_name = data.get("name", tag)

        # Extract version numbers from both strings for comparison
        # Handles formats like "v2.5-stable", "Beta Ver. 2.5", "2.6", etc.
        def _extract_version(s):
            m = _re.search(r'(\d+(?:\.\d+)*)', s)
            if m:
                return tuple(int(x) for x in m.group(1).split('.'))
            return (0,)

        local_ver = _extract_version(self.CATCHBOT_VERSION)
        remote_ver = _extract_version(tag)

        if remote_ver > local_ver:
            # Find the download asset (Catchbot.zip or first asset)
            assets = data.get("assets", [])
            download_url = None
            download_name = None
            for asset in assets:
                download_url = asset.get("browser_download_url")
                download_name = asset.get("name")
                break  # Use the first asset

            print(f"\n\n           {Fore.RED}NEW VERSION AVAILABLE!{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}Latest: {release_name} ({tag}){Style.RESET_ALL}")
            if download_name:
                print(f"           {Fore.YELLOW}File:   {download_name}{Style.RESET_ALL}")
            print(f"\n           {Fore.CYAN}Download: {_GH_RELEASES}{Style.RESET_ALL}")

            print(f"\n{Fore.CYAN}+=========================================================+{Style.RESET_ALL}\n")
            open_choice = input(f"           {Fore.YELLOW}You want to Update? (y/n): {Style.RESET_ALL}").strip().lower()
            if open_choice in ('y', 'yes'):
                import webbrowser
                target = download_url if download_url else _GH_RELEASES
                webbrowser.open(target)
                print(f"           {Fore.GREEN}Opened in browser!{Style.RESET_ALL}\n")
            else:
                print()
        else:
            print(f"\n\n           {Fore.GREEN}You are using the latest version!{Style.RESET_ALL}")
            print(f"           {Fore.GREEN}Latest release: {release_name} ({tag}){Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}+=========================================================+{Style.RESET_ALL}\n")
            input(f"           {Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
    # ═════════════════════════════════════════════════════════════════
    #  BOT LOGIK
    # ═════════════════════════════════════════════════════════════════
    
    # ═════════════════════════════════════════════════════════════════
    #  AUTO QUEST RENEWER SYSTEM
    # ═════════════════════════════════════════════════════════════════
    
