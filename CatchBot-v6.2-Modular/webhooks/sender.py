"""Webhook dispatch: Discord webhooks for catches, alerts, and shared success feed."""
import os
import sys
import re
import json
import asyncio
import random
import threading
import time as time_module
from datetime import datetime, timedelta

import discord
from colorama import Fore, Style

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class WebhookMixin:
    def send_webhook(self, pokemon_name, rarity, caught, original_message=None, is_event=False):
        """Sendet eine Webhook-Nachricht an Discord (private/config webhook)"""
        wh_config = self.config.get('webhook', {})
        if not wh_config.get('enabled', False) or not wh_config.get('url', ''):
            return
        
        # Pruefen ob diese Rarity benachrichtigt werden soll
        notify_rarities = wh_config.get('notify_rarities', ['legendary', 'shiny'])
        rarity_lower = rarity.lower().strip() if rarity else ''
        
        # Event pokemon: check if event webhook is enabled in config
        event_webhook_enabled = self.config.get('event_pokemon', {}).get('webhook_enabled', True)
        should_notify = is_event and event_webhook_enabled
        if not should_notify:
            for nr in notify_rarities:
                if nr.lower() in rarity_lower:
                    should_notify = True
                    break
        
        if not should_notify:
            return
        
        # Bei Geflohen pruefen ob das auch gemeldet werden soll
        if not caught and not wh_config.get('notify_fled', True):
            return
        
        is_shiny = 'shiny' in rarity_lower
        is_legendary = 'legendary' in rarity_lower
        
        # Simply forward the original PokeMeow message (content + embeds) as-is
        embeds = []
        content_text = ""
        
        if original_message:
            if original_message.content:
                content_text = original_message.content
            if original_message.embeds:
                for embed in original_message.embeds:
                    try:
                        embed_dict = embed.to_dict()
                        # Event Pokemon -> override embed color to RED
                        if is_event:
                            embed_dict['color'] = 0xE74C3C  # Red
                        embeds.append(embed_dict)
                    except Exception:
                        pass
        
        status_text = "CAUGHT" if caught else "FLED"
        event_label = "[EVENT] " if is_event else ""
        
        # Minimal fallback if no original message
        if not embeds and not content_text:
            content_text = f"{event_label}{pokemon_name} - {status_text}"
        elif is_event and not content_text:
            content_text = f"\U0001f534 **Event Pokemon!**"
        
        # Discord erlaubt max 10 Embeds pro Nachricht
        embeds = embeds[:10]
        
        payload = {
            "embeds": embeds
        }
        if content_text:
            payload["content"] = content_text
        
        # Async-safe: in Thread ausfuehren damit der Bot nicht blockiert
        def _send():
            try:
                resp = requests.post(wh_config['url'], json=payload, timeout=5)
                if resp.status_code == 204:
                    self.log(f"Webhook sent: {event_label}{status_text} {pokemon_name}")
                else:
                    self.log(f"Webhook Error: HTTP {resp.status_code}")
            except Exception as e:
                self.log(f"Webhook Error: {str(e)}")
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_webhook_alert(self, title, description, color=0xE74C3C):
        """Sendet eine allgemeine Alert-Nachricht an den Webhook (z.B. Catch-Limit)"""
        wh_config = self.config.get('webhook', {})
        if not wh_config.get('enabled', False) or not wh_config.get('url', ''):
            return
        
        now_str = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
        s = self.session_stats
        total = s['total_encounters']
        c = s['total_caught']
        f = s['total_fled']
        duration = self.get_session_duration()
        
        embed = {
            "title": title,
            "description": description,
            "color": color,
            "fields": [
                {"name": "Session Duration", "value": duration, "inline": True},
                {"name": "Caught", "value": str(c), "inline": True},
                {"name": "Fled", "value": str(f), "inline": True},
            ],
            "footer": {"text": f"CatchBot | {now_str}"}
        }
        
        payload = {"embeds": [embed]}
        
        def _send():
            try:
                requests.post(wh_config['url'], json=payload, timeout=5)
            except Exception:
                pass
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_shared_success_webhook(self, pokemon_name, rarity="", original_message=None, catch_method="catch", is_event=False):
        """Sends a single rarity-colored embed to the shared webhook for each successful catch.
        
        Uses a time+name based dedup to guarantee only ONE webhook is sent per catch,
        even if PokeMeow edits the message multiple times or sends multiple messages.
        """
        if not HAS_REQUESTS:
            return
        # Shared feed disabled if no webhook URL is configured on the class.
        if not getattr(self, 'SHARED_SUCCESS_WEBHOOK', None):
            return

        # === DEDUP: Prevent duplicate sends ===
        # Key = lowercase pokemon name; value = timestamp of last send.
        # If the same pokemon was sent within the last 15 seconds, skip it.
        if not hasattr(self, '_shared_webhook_dedup'):
            self._shared_webhook_dedup = {}
        
        now = datetime.now()
        dedup_key = pokemon_name.lower().strip()
        last_sent = self._shared_webhook_dedup.get(dedup_key)
        if last_sent and (now - last_sent).total_seconds() < 15:
            self.log(f"[SHARED-WEBHOOK] Skipping duplicate for '{pokemon_name}' (sent {(now - last_sent).total_seconds():.1f}s ago)")
            return
        
        # Mark as sent IMMEDIATELY (before the thread) to block any racing duplicates
        self._shared_webhook_dedup[dedup_key] = now
        
        # Cleanup old entries (keep only last 60 seconds worth)
        cutoff = now - timedelta(seconds=60)
        self._shared_webhook_dedup = {
            k: v for k, v in self._shared_webhook_dedup.items() if v > cutoff
        }
        
        # === BUILD EMBED ===
        now_str = now.strftime('%d.%m.%Y %H:%M')
        rarity_lower = rarity.lower().strip() if rarity else ""
        is_shiny = 'shiny' in rarity_lower
        is_legendary = 'legendary' in rarity_lower
        
        # Pokemon sprite (lowercase, special chars removed)
        pokemon_lower = pokemon_name.lower().strip().replace(' ', '-').replace("'", "").replace(".", "")
        sprite_url = f"https://img.pokemondb.net/sprites/home/normal/{pokemon_lower}.png"
        
        # Extract PokeMeow image URL as fallback (from original message embed thumbnail/image)
        pokemeow_image_url = None
        if original_message and hasattr(original_message, 'embeds') and original_message.embeds:
            for emb in original_message.embeds:
                emb_dict = emb.to_dict()
                if 'thumbnail' in emb_dict and 'url' in emb_dict['thumbnail']:
                    pokemeow_image_url = emb_dict['thumbnail']['url']
                    break
                if 'image' in emb_dict and 'url' in emb_dict['image']:
                    pokemeow_image_url = emb_dict['image']['url']
                    break
        
        # Detect special forms (forms that won't exist on PokemonDB with base name)
        # Examples: "Iron-Leaves", "Arceus-Fairy", "Necrozma Ultra", "Giratina-Origin", etc.
        is_special_form = (
            '-' in pokemon_name or  # Hyphenated forms: Arceus-Fairy, Iron-Leaves, etc.
            ' ' in pokemon_name.strip() or  # Multi-word forms: Necrozma Ultra, etc.
            any(form in pokemon_name.lower() for form in [
                'mega', 'gmax', 'primal', 'origin', 'altered', 'sky', 'land',
                'therian', 'incarnate', 'black', 'white', 'dawn', 'dusk',
                'ultra', 'crowned', 'eternamax', 'zen', 'galarian', 'alolan',
                'hisuian', 'paldean', 'iron', 'roaring', 'walking', 'raging',
                'great', 'scream', 'brute', 'flutter', 'slither', 'sandy',
                'bloodmoon', 'teal', 'cornerstone', 'hearthflame', 'wellspring'
            ])
        )
        
        # For shiny Pokemon OR special forms, ALWAYS use the original PokeMeow image
        # because PokemonDB won't have the correct sprite
        use_original_image = is_shiny or is_special_form
        
        # Rarity-based embed color mapping (NO green fallback)
        RARITY_COLORS = {
            'golden':     0xFFD700,   # Gold
            'shiny':      0xFF69B4,   # Pink   (check first - "Shiny Legendary" should be pink)
            'legendary':  0x9B59B6,   # Purple
            'super rare': 0xF1C40F,   # Yellow
            'rare':       0xE67E22,   # Orange
            'uncommon':   0x5DADE2,   # Light Blue
            'common':     0x1A3A6B,   # Dark Blue
        }
        
        # Determine embed color from rarity (ordered check, first match wins)
        embed_color = 0x1A3A6B  # Default: Dark Blue (common)
        for rarity_key, color in RARITY_COLORS.items():
            if rarity_key in rarity_lower:
                embed_color = color
                break
        
        # Event Pokemon -> override embed color to RED
        if is_event:
            embed_color = 0xE74C3C  # Red for Event Pokemon
        
        # Title and description based on rarity and catch method
        fish_emoji = "\U0001f3a3"  # fishing pole
        event_prefix = "\U0001f534 Event " if is_event else ""
        if catch_method == "fish":
            if is_shiny:
                title = f"{fish_emoji} {event_prefix}Shiny Fishing Catch!"
                description = f"Someone just fished a **{event_prefix}Shiny {pokemon_name}** using catchbot! {fish_emoji}"
            elif is_legendary:
                title = f"{fish_emoji} {event_prefix}Legendary Fishing Catch!"
                description = f"Someone just fished a **{event_prefix}Legendary {pokemon_name}** using catchbot! {fish_emoji}"
            else:
                title = f"{fish_emoji} {event_prefix}Successful Catch"
                description = f"Someone just fished **{event_prefix}{pokemon_name}** using catchbot! {fish_emoji}"
        else:
            if is_shiny:
                title = f"\u2728 {event_prefix}Shiny Catch!"
                description = f"Someone just caught a **{event_prefix}Shiny {pokemon_name}** using catchbot! \u2728"
            elif is_legendary:
                title = f"\U0001f31f {event_prefix}Legendary Catch!"
                description = f"Someone just caught a **{event_prefix}Legendary {pokemon_name}** using catchbot! \U0001f31f"
            else:
                title = f"\U0001f389 {event_prefix}Successful Catch"
                description = f"Someone just caught a **{event_prefix}{pokemon_name}** using catchbot! \U0001f389"
        
        embed = {
            "title": title,
            "description": description,
            "color": embed_color,
            "thumbnail": {
                "url": sprite_url
            },
            "footer": {
                "text": f"CatchBot {self.CATCHBOT_VERSION} \u2022 {now_str}"
            }
        }
        
        payload = {
            "embeds": [embed]
        }
        
        def _send():
            try:
                # For shiny/special forms, use PokeMeow image directly (more accurate)
                # For regular Pokemon, check if PokemonDB sprite exists first
                if use_original_image and pokemeow_image_url:
                    payload['embeds'][0]['thumbnail']['url'] = pokemeow_image_url
                    reason = "shiny" if is_shiny else "special form"
                    self.log(f"[SHARED-WEBHOOK] Using original PokeMeow image for {reason}: '{pokemon_name}'")
                else:
                    # Check if pokemondb sprite exists, fallback to PokeMeow image
                    use_fallback = False
                    try:
                        head_resp = requests.head(sprite_url, timeout=3, allow_redirects=True)
                        if head_resp.status_code != 200:
                            use_fallback = True
                    except Exception:
                        use_fallback = True
                    
                    if use_fallback and pokemeow_image_url:
                        payload['embeds'][0]['thumbnail']['url'] = pokemeow_image_url
                        self.log(f"[SHARED-WEBHOOK] Sprite not found for '{pokemon_name}', using PokeMeow image fallback")
                
                resp = requests.post(self.SHARED_SUCCESS_WEBHOOK, json=payload, timeout=5)
                if resp.status_code == 204:
                    event_log = "Event " if is_event else ""
                    log_label = "Shiny " if is_shiny else ("Legendary " if is_legendary else "")
                    method_label = "Fished" if catch_method == "fish" else "Caught"
                    self.log(f"[SHARED-WEBHOOK] Sent: {event_log}{log_label}{method_label} {pokemon_name} (Rarity: {rarity}, Color: #{embed_color:06X})")
                else:
                    self.log(f"[SHARED-WEBHOOK] Error: HTTP {resp.status_code}")
            except Exception as e:
                self.log(f"[SHARED-WEBHOOK] Error: {str(e)}")
        
        threading.Thread(target=_send, daemon=True).start()
    
    def show_webhook_menu(self):
        """Zeigt das Webhook Konfigurations-Menue"""
        self.print_header()
        
        wh = self.config.get('webhook', {})
        enabled = wh.get('enabled', False)
        url = wh.get('url', '')
        notify_rarities = wh.get('notify_rarities', ['legendary', 'shiny'])
        notify_fled = wh.get('notify_fled', True)
        notify_limit = wh.get('notify_catch_limit', True)
        
        def status(on):
            return f"{Fore.GREEN}V{Style.RESET_ALL}" if on else f"{Fore.RED}X{Style.RESET_ALL}"
        
        print(f"\n{Fore.CYAN}+=================== WEBHOOK ===========================+{Style.RESET_ALL}")
        print(f"\n           {status(enabled)} Webhook {'enabled' if enabled else 'disabled'}")
        
        print(f"\n           {Fore.YELLOW}Sends notifications to a Discord channel{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}when rare Pokemon are caught/fled.{Style.RESET_ALL}")
        
        print(f"\n           {Fore.YELLOW}=== Settings ==={Style.RESET_ALL}")
        print(f"           [1] {status(enabled)} Webhook on/off")
        print(f"           [2] Set Webhook URL")
        
        # URL Anzeige
        if url:
            masked_url = url[:40] + '...' if len(url) > 40 else url
            print(f"               {Fore.GREEN}URL: {masked_url}{Style.RESET_ALL}")
        else:
            print(f"               {Fore.RED}URL: Not set{Style.RESET_ALL}")
        
        print(f"\n           {Fore.YELLOW}=== Notifications ==={Style.RESET_ALL}")
        
        all_rarities = ['common', 'uncommon', 'rare', 'super rare', 'legendary', 'shiny']
        rarity_colors = {
            'common': Fore.CYAN,
            'uncommon': Fore.GREEN,
            'rare': Fore.YELLOW,
            'super rare': Fore.LIGHTYELLOW_EX,
            'legendary': Fore.MAGENTA,
            'shiny': Fore.LIGHTMAGENTA_EX,
        }
        
        for i, r in enumerate(all_rarities, 3):
            is_active = r in [nr.lower() for nr in notify_rarities]
            color = rarity_colors.get(r, Fore.WHITE)
            print(f"           [{i}] {status(is_active)} {color}{r.title()}{Style.RESET_ALL}")
        
        event_cfg = self.config.get('event_pokemon', {})
        print(f"           [E] {status(event_cfg.get('webhook_enabled', True))} {Fore.RED}Event Pokemon{Style.RESET_ALL}")
        
        print(f"\n           {Fore.YELLOW}=== Egg Hatch Notifications ==={Style.RESET_ALL}")
        egg_on = wh.get('egg_hatch_enabled', False)
        egg_rarities = [r.lower() for r in wh.get('egg_hatch_notify_rarities', ['shiny'])]
        print(f"           [H] {status(egg_on)} Egg Hatch Webhook on/off")
        print(f"           [I] Shiny&Legendary Hatches: {status('shiny' in egg_rarities)}  |  Normal Hatches: {status('normal' in egg_rarities)}")
        
        print(f"\n           {Fore.YELLOW}=== Extras ==={Style.RESET_ALL}")
        print(f"           [9] {status(notify_fled)} Also notify on Fled")
        print(f"           [L] {status(notify_limit)} Catch Limit Warning")
        
        print(f"\n           [0] Back")
        
        print(f"\n{Fore.CYAN}+========================================================+{Style.RESET_ALL}\n")
    
    def handle_webhook_config(self):
        """Handler fuer Webhook Konfiguration"""
        all_rarities = ['common', 'uncommon', 'rare', 'super rare', 'legendary', 'shiny']
        
        while True:
            self.show_webhook_menu()
            choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}").strip()
            
            wh = self.config.get('webhook', {})
            
            if choice == '1':
                if not wh.get('url', '') and not wh.get('enabled', False):
                    print(f"           {Fore.RED}Set a Webhook URL first! (Option 2){Style.RESET_ALL}")
                    time_module.sleep(1.5)
                    continue
                wh['enabled'] = not wh.get('enabled', False)
                self.config['webhook'] = wh
                state = "enabled" if wh['enabled'] else "disabled"
                print(f"           {Fore.GREEN}Webhook {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice == '2':
                print(f"\n           {Fore.CYAN}Enter Discord Webhook URL{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}(Channel -> Edit -> Integrations -> Webhooks){Style.RESET_ALL}")
                url = input(f"           {Fore.CYAN}URL: {Style.RESET_ALL}").strip()
                if url and url.startswith('https://discord.com/api/webhooks/'):
                    wh['url'] = url
                    self.config['webhook'] = wh
                    print(f"           {Fore.GREEN}Webhook URL saved!{Style.RESET_ALL}")
                elif url:
                    print(f"           {Fore.RED}Invalid URL! Must start with https://discord.com/api/webhooks/{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.RED}No URL entered!{Style.RESET_ALL}")
                time_module.sleep(1.5)
            
            elif choice in ['3', '4', '5', '6', '7', '8']:
                idx = int(choice) - 3
                if idx < len(all_rarities):
                    rarity = all_rarities[idx]
                    current = [nr.lower() for nr in wh.get('notify_rarities', ['legendary', 'shiny'])]
                    
                    if rarity in current:
                        current.remove(rarity)
                        print(f"           {Fore.RED}{rarity.title()} removed{Style.RESET_ALL}")
                    else:
                        current.append(rarity)
                        print(f"           {Fore.GREEN}{rarity.title()} added{Style.RESET_ALL}")
                    
                    wh['notify_rarities'] = current
                    self.config['webhook'] = wh
                    time_module.sleep(0.8)
            
            elif choice == '9':
                wh['notify_fled'] = not wh.get('notify_fled', True)
                self.config['webhook'] = wh
                state = "enabled" if wh['notify_fled'] else "disabled"
                print(f"           {Fore.GREEN}Fled notification {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice.lower() == 'l':
                wh['notify_catch_limit'] = not wh.get('notify_catch_limit', True)
                self.config['webhook'] = wh
                state = "enabled" if wh['notify_catch_limit'] else "disabled"
                print(f"           {Fore.GREEN}Catch Limit Warning {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice.lower() == 'h':
                wh['egg_hatch_enabled'] = not wh.get('egg_hatch_enabled', False)
                self.config['webhook'] = wh
                state = "enabled" if wh['egg_hatch_enabled'] else "disabled"
                print(f"           {Fore.GREEN}Egg Hatch Webhook {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice.lower() == 'i':
                egg_rarities = [r.lower() for r in wh.get('egg_hatch_notify_rarities', ['shiny'])]
                print(f"\n           {Fore.CYAN}Toggle Egg Hatch Rarity Filter:{Style.RESET_ALL}")
                print(f"           [1] Shiny Eggs {'(active)' if 'shiny' in egg_rarities else '(inactive)'}")
                print(f"           [2] Normal Eggs {'(active)' if 'normal' in egg_rarities else '(inactive)'}")
                sub_choice = input(f"           {Fore.CYAN}Toggle (1/2): {Style.RESET_ALL}").strip()
                
                if sub_choice == '1':
                    if 'shiny' in egg_rarities:
                        egg_rarities.remove('shiny')
                        print(f"           {Fore.RED}Shiny Eggs removed{Style.RESET_ALL}")
                    else:
                        egg_rarities.append('shiny')
                        print(f"           {Fore.GREEN}Shiny Eggs added{Style.RESET_ALL}")
                elif sub_choice == '2':
                    if 'normal' in egg_rarities:
                        egg_rarities.remove('normal')
                        print(f"           {Fore.RED}Normal Eggs removed{Style.RESET_ALL}")
                    else:
                        egg_rarities.append('normal')
                        print(f"           {Fore.GREEN}Normal Eggs added{Style.RESET_ALL}")
                
                wh['egg_hatch_notify_rarities'] = egg_rarities
                self.config['webhook'] = wh
                time_module.sleep(1)
            
            elif choice.lower() == 'e':
                # Toggle Event Pokemon Webhook
                event_cfg = self.config.get('event_pokemon', {})
                event_cfg['webhook_enabled'] = not event_cfg.get('webhook_enabled', True)
                self.config['event_pokemon'] = event_cfg
                state = "enabled" if event_cfg['webhook_enabled'] else "disabled"
                print(f"           {Fore.GREEN}Event Pokemon Private Webhook {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice == '0':
                self.save_config()
                break
            
            self.save_config()
    
