"""Egg hatching detection and egg-hatch webhook dispatch."""
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

from utils.platform import (
    WINDOWS,
    HAS_TOAST,
    _show_windows_toast,
    _generate_alarm_wav,
)

try:
    import winsound
except ImportError:
    winsound = None


class EggMixin:
    async def check_egg(self, message):
        """Prüft ob ein Egg bereit ist zum Hatchen"""
        if self.egg_busy:
            return
        
        all_text = ""
        
        # Text aus Embeds
        if message.embeds:
            for embed in message.embeds:
                embed_dict = embed.to_dict()
                if 'title' in embed_dict:
                    all_text += str(embed_dict['title']).lower() + " "
                if 'description' in embed_dict:
                    all_text += str(embed_dict['description']).lower() + " "
        
        # Text aus Nachricht
        if message.content:
            all_text += message.content.lower()
        
        # Egg bereit zum Hatchen?
        if 'egg is ready to hatch' in all_text:
            self.egg_busy = True
            self.log(f"🥚 Egg is ready to hatch!")
            print(f"{Fore.MAGENTA}[{datetime.now().strftime('%H:%M:%S')}] 🥚 Egg ready! Starting hatch sequence...{Style.RESET_ALL}")
            
            try:
                channel = message.channel
                
                # Step 1: Hatch egg
                await asyncio.sleep(3)
                await self.send_command(channel, ';egg hatch')
                self.log("🥚 ;egg hatch sent, waiting for confirmation...")
                
                # Step 2: Wait for "just hatched a" (max 15 seconds) and capture the Pokemon name
                hatched_msg = await self.wait_for_message_return(channel, 'just hatched a', timeout=15)
                hatched = hatched_msg is not None
                
                if hatched:
                    # Extract the Pokemon name from the hatch message
                    hatched_name = "Unknown"
                    hatch_text = ""
                    if hatched_msg.embeds:
                        for embed in hatched_msg.embeds:
                            embed_dict = embed.to_dict()
                            if 'description' in embed_dict:
                                hatch_text += str(embed_dict['description']) + " "
                            if 'title' in embed_dict:
                                hatch_text += str(embed_dict['title']) + " "
                    if hatched_msg.content:
                        hatch_text += hatched_msg.content
                    
                    # Clean hatch text: remove EXP/level lines that contain other Pokemon names
                    clean_lines = []
                    for line in hatch_text.split('\n'):
                        line_lower = line.strip().lower()
                        if ' gained ' in line_lower or ' is now level' in line_lower or 'congratulations' in line_lower:
                            continue
                        clean_lines.append(line)
                    hatch_text_clean = ' '.join(clean_lines)
                    
                    # === SHINY EGG DETECTION ===
                    # Primary: Detect via PokeMeow embed border color
                    # Pink/Magenta border = Shiny, Orange = normal rare, etc.
                    # Fallback: text-based detection
                    hatch_is_shiny = False
                    egg_rarity = 'normal'
                    
                    if hatched_msg.embeds:
                        for embed in hatched_msg.embeds:
                            try:
                                embed_color = embed.color.value if embed.color else 0
                                # PokeMeow embed color ranges for egg hatches:
                                # Pink/Magenta (0xFF00FF area / 0xF8A5C2 area) = Shiny
                                # Gold (0xFFD700 area) = Shiny (alternate)
                                r = (embed_color >> 16) & 0xFF
                                g = (embed_color >> 8) & 0xFF
                                b = embed_color & 0xFF
                                
                                # Detect shiny ONLY by pink/magenta hue (high red, low green, high blue)
                                # Gold/yellow border = Super Rare (NOT shiny!)
                                # PokeMeow egg hatch embed colors:
                                #   Pink/Magenta = Shiny
                                #   Gold/Yellow  = Super Rare
                                #   Orange       = Rare
                                #   Purple       = Legendary
                                if (r > 200 and g < 130 and b > 150):  # Pink/Magenta range = Shiny
                                    hatch_is_shiny = True
                                    egg_rarity = 'shiny'
                                
                                if hatch_is_shiny:
                                    self.log(f"[EGG-COLOR] Shiny detected via embed color: #{embed_color:06X} (R={r} G={g} B={b})")
                                    break
                            except Exception:
                                pass
                    
                    # Fallback: text-based shiny detection
                    # PokeMeow format: "just hatched a <emoji> **Shiny Pokemon**!"
                    if not hatch_is_shiny:
                        hatch_is_shiny = 'shiny' in hatch_text_clean.lower()
                        if hatch_is_shiny:
                            egg_rarity = 'shiny'
                            self.log(f"[EGG-COLOR] Shiny detected via text fallback")
                    
                    # Extract Pokemon name from "just hatched a <emoji> <Name>!" pattern
                    # Also handle "Shiny Name" by stripping "Shiny " prefix
                    hatch_match = re.search(r'just hatched a\s+(?:[^\w]*\s*)?([A-Z][a-zA-Z\s\-\'\.]+?)(?:\s*!|\s*You|\s*\*)', hatch_text_clean)
                    if hatch_match:
                        hatched_name = hatch_match.group(1).strip()
                        # Remove "Shiny " prefix from name if present (we track shiny separately)
                        if hatched_name.lower().startswith('shiny '):
                            hatched_name = hatched_name[6:].strip()
                    else:
                        # Fallback: search pokemon name list only in the clean text
                        if hasattr(self, 'pokemon_names') and self.pokemon_names:
                            for pname in self.pokemon_names:
                                if pname.lower() in hatch_text_clean.lower():
                                    hatched_name = pname
                                    break
                    
                    # === SHINY EGG HATCH HIGHLIGHT ===
                    if hatch_is_shiny:
                        self.log(f"Egg hatched! **Shiny {hatched_name}**!")
                        print(f"\n{Fore.LIGHTMAGENTA_EX}{'*' * 66}{Style.RESET_ALL}")
                        print(f"{Fore.LIGHTMAGENTA_EX}  \u2728\u2728  SHINY EGG HATCH! **Shiny {hatched_name}**!  \u2728\u2728{Style.RESET_ALL}")
                        print(f"{Fore.LIGHTMAGENTA_EX}{'*' * 66}{Style.RESET_ALL}")
                        
                        # Track shiny egg hatch in persistent stats
                        now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
                        self.persistent_stats['shinys_caught'] += 1
                        self.persistent_stats['shiny_list'].append({
                            'name': f"{hatched_name} (Egg)", 'date': now_str, 'rarity': 'Shiny (Egg Hatch)'
                        })
                        self.session_stats['best_catches'].append(
                            f"SHINY {hatched_name} - Egg Hatch ({now_str})"
                        )
                    else:
                        self.log(f"Egg hatched! Pokemon: {hatched_name}")
                        print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] Egg hatched! -> {Fore.MAGENTA}{hatched_name}{Style.RESET_ALL}")
                    
                    # === EGG STATS TRACKING ===
                    self.persistent_stats['eggs_hatched'] = self.persistent_stats.get('eggs_hatched', 0) + 1
                    # Track which Pokemon hatched
                    egg_pokemon_list = self.persistent_stats.get('egg_pokemon_list', [])
                    egg_pokemon_list.append({
                        'name': hatched_name,
                        'date': datetime.now().strftime('%d.%m.%Y %H:%M'),
                        'shiny': hatch_is_shiny
                    })
                    self.persistent_stats['egg_pokemon_list'] = egg_pokemon_list
                    # Track egg rarity breakdown (uses color-detected rarity)
                    egg_rarity_stats = self.persistent_stats.get('egg_rarity_stats', {})
                    rarity_label = egg_rarity.title()  # 'Shiny' or 'Normal'
                    egg_rarity_stats[rarity_label] = egg_rarity_stats.get(rarity_label, 0) + 1
                    self.persistent_stats['egg_rarity_stats'] = egg_rarity_stats
                    
                    # Session egg counter
                    self.session_stats['eggs_hatched'] = self.session_stats.get('eggs_hatched', 0) + 1
                    
                    self.save_persistent_stats()
                    
                    # Send egg hatch to shared webhook (with shiny flag)
                    self.send_egg_hatch_webhook(hatched_name, hatched_msg, is_shiny=hatch_is_shiny)
                    # Send egg hatch to private/config webhook (with shiny flag)
                    self.send_egg_hatch_private_webhook(hatched_name, is_shiny=hatch_is_shiny, original_message=hatched_msg)
                    
                    # Step 3: Equip new egg
                    await asyncio.sleep(4)
                    await self.send_command(channel, ';egg hold')
                    self.log("🥚 ;egg hold sent, waiting for confirmation...")
                    
                    # Wait for confirmation
                    held = await self.wait_for_message(channel, 'now holding an egg', timeout=15)
                    
                    if held:
                        self.log(f"🥚 New egg is being held!")
                        print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] 🥚 New egg equipped!{Style.RESET_ALL}")
                    else:
                        self.log(f"🥚 Egg hold confirmation not received (no problem)")
                else:
                    self.log(f"🥚 Hatch confirmation not received")
                    print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] 🥚 Hatch confirmation not received{Style.RESET_ALL}")
                
            except Exception as e:
                self.log(f"🥚 Error in egg system: {str(e)}")
                print(f"{Fore.RED}Egg Error: {str(e)}{Style.RESET_ALL}")
            finally:
                self.egg_busy = False
                await asyncio.sleep(3)  # Extra Cooldown nach Egg-Aktion
    
    def send_egg_hatch_private_webhook(self, pokemon_name, is_shiny=False, original_message=None):
        """Sends egg hatch info to the private/config webhook - forwards original PokeMeow message.
        Respects webhook egg_hatch_enabled toggle and egg_hatch_notify_rarities filter."""
        wh_config = self.config.get('webhook', {})
        if not wh_config.get('enabled', False) or not wh_config.get('url', ''):
            return
        if not wh_config.get('egg_hatch_enabled', False):
            return
        if not HAS_REQUESTS:
            return
        
        # Check rarity filter for egg hatches
        egg_notify = [r.lower() for r in wh_config.get('egg_hatch_notify_rarities', ['shiny'])]
        egg_rarity = 'shiny' if is_shiny else 'normal'
        
        should_notify = False
        for nr in egg_notify:
            if nr in egg_rarity:
                should_notify = True
                break
        
        if not should_notify:
            return
        
        # Simply forward the original PokeMeow message (content + embeds)
        embeds = []
        content_text = ""
        
        if original_message:
            if original_message.content:
                content_text = original_message.content
            if original_message.embeds:
                for embed in original_message.embeds:
                    try:
                        embeds.append(embed.to_dict())
                    except Exception:
                        pass
        
        # If no original message available, create minimal fallback
        if not embeds and not content_text:
            shiny_tag = "Shiny " if is_shiny else ""
            content_text = f"Egg hatched: {shiny_tag}{pokemon_name}"
        
        payload = {"embeds": embeds[:10]}
        if content_text:
            payload["content"] = content_text
        
        def _send():
            try:
                resp = requests.post(wh_config['url'], json=payload, timeout=5)
                if resp.status_code == 204:
                    shiny_label = "Shiny " if is_shiny else ""
                    self.log(f"Private Webhook sent: {shiny_label}Egg hatched -> {pokemon_name}")
                else:
                    self.log(f"Private Webhook Error (egg hatch): HTTP {resp.status_code}")
            except Exception as e:
                self.log(f"Private Webhook Error (egg hatch): {str(e)}")
        
        threading.Thread(target=_send, daemon=True).start()
    
    def send_egg_hatch_webhook(self, pokemon_name, original_message=None, is_shiny=False):
        """Sends egg hatch info to the shared catchbot webhook (successful-catches channel)"""
        if not HAS_REQUESTS:
            return
        # Shared feed disabled if no webhook URL is configured on the class.
        if not getattr(self, 'SHARED_SUCCESS_WEBHOOK', None):
            return

        # === DEDUP: Prevent duplicate egg hatch sends ===
        if not hasattr(self, '_shared_egg_dedup'):
            self._shared_egg_dedup = {}
        
        now = datetime.now()
        dedup_key = f"egg_{pokemon_name.lower().strip()}"
        last_sent = self._shared_egg_dedup.get(dedup_key)
        if last_sent and (now - last_sent).total_seconds() < 15:
            self.log(f"[SHARED-WEBHOOK] Skipping duplicate egg hatch for '{pokemon_name}'")
            return
        self._shared_egg_dedup[dedup_key] = now
        # Cleanup old entries
        cutoff = now - timedelta(seconds=60)
        self._shared_egg_dedup = {k: v for k, v in self._shared_egg_dedup.items() if v > cutoff}
        
        now_str = now.strftime('%d.%m.%Y %H:%M')
        
        # Pokemon sprite from PokemonDB
        pokemon_lower = pokemon_name.lower().strip().replace(' ', '-').replace("'", "").replace(".", "")
        sprite_url = f"https://img.pokemondb.net/sprites/home/normal/{pokemon_lower}.png"
        
        # Extract PokeMeow image URL as fallback
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
        
        # For shiny egg hatches, always use original PokeMeow image (GIF)
        use_original_image = is_shiny
        
        # Different embed color + title for Shiny egg hatches
        if is_shiny:
            embed_color = 0xFF69B4   # Pink for Shiny (matching rarity color scheme)
            title = "\u2728 Shiny Egg Hatch!"
            description = f"Someone just hatched a **Shiny {pokemon_name}** using catchbot! \u2728"
        else:
            embed_color = 0xE67E22   # Orange for normal egg hatch
            title = "\U0001f95a Egg Hatched!"
            description = f"Someone just hatched a **{pokemon_name}** using catchbot! \U0001f95a"
        
        # Use PokeMeow image (GIF) for shiny, PokemonDB sprite for normal
        thumbnail_url = pokemeow_image_url if (use_original_image and pokemeow_image_url) else sprite_url
        
        embed = {
            "title": title,
            "description": description,
            "color": embed_color,
            "thumbnail": {
                "url": thumbnail_url
            },
            "footer": {
                "text": f"CatchBot {self.CATCHBOT_VERSION} \u2022 {now_str}"
            }
        }
        
        payload = {"embeds": [embed]}
        
        def _send():
            try:
                # For shiny, we already set the PokeMeow image; for normal, check if sprite exists
                if not use_original_image or not pokemeow_image_url:
                    # Check if sprite exists, fallback to PokeMeow image
                    use_fallback = False
                    try:
                        head_resp = requests.head(sprite_url, timeout=3, allow_redirects=True)
                        if head_resp.status_code != 200:
                            use_fallback = True
                    except Exception:
                        use_fallback = True
                    
                    if use_fallback and pokemeow_image_url:
                        payload['embeds'][0]['thumbnail']['url'] = pokemeow_image_url
                        self.log(f"[SHARED-WEBHOOK] Egg sprite not found for '{pokemon_name}', using PokeMeow image fallback")
                else:
                    self.log(f"[SHARED-WEBHOOK] Using original PokeMeow image (GIF) for shiny egg hatch: '{pokemon_name}'")
                
                resp = requests.post(self.SHARED_SUCCESS_WEBHOOK, json=payload, timeout=5)
                if resp.status_code == 204:
                    shiny_label = "Shiny " if is_shiny else ""
                    self.log(f"Shared Webhook sent: {shiny_label}Egg hatched -> {pokemon_name}")
                else:
                    self.log(f"Shared Webhook Error (egg hatch): HTTP {resp.status_code}")
            except Exception as e:
                self.log(f"Shared Webhook Error (egg hatch): {str(e)}")
        
        threading.Thread(target=_send, daemon=True).start()
    
