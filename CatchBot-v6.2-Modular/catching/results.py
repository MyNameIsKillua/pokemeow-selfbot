"""CatchResultsMixin: check_catch_limit, check_catch_result, record_catch."""
import asyncio
import random
import re
import threading
import time as time_module
from datetime import datetime, timedelta
from colorama import Fore, Style

from utils.platform import WINDOWS, _show_windows_toast, _generate_alarm_wav

try:
    import winsound
except ImportError:
    winsound = None


class CatchResultsMixin:
    async def check_catch_limit(self, message):
        """Checks if the daily catch limit has been reached"""
        if self.catch_limit_reached:
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
                if 'fields' in embed_dict:
                    for field in embed_dict['fields']:
                        if 'name' in field:
                            all_text += str(field['name']).lower() + " "
                        if 'value' in field:
                            all_text += str(field['value']).lower() + " "
                if 'footer' in embed_dict and 'text' in embed_dict['footer']:
                    all_text += str(embed_dict['footer']['text']).lower() + " "
        
        if message.content:
            all_text += message.content.lower()
        
        # Catch Limit erkannt?
        if 'you have reached the daily catch limit' in all_text:
            self.catch_limit_reached = True
            self.log(f"🚫 DAILY CATCH LIMIT REACHED! Bot is pausing!")
            
            print(f"\n{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
            print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
            print(f"{Fore.RED}  ████████████████████████████████████████████████████████████{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   DAILY CATCH LIMIT REACHED!                           ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   Uh oh! You have reached the daily catch limit!       ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   Bot is COMPLETELY paused.                            ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   Vote or become a Patreon Supporter to remove         ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   the limit.                                           ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   Press [P] to continue after the reset.               ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ████████████████████████████████████████████████████████████{Style.RESET_ALL}")
            print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
            print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}\n")
            
            # Desktop-Notification (native toast - works in .exe)
            if self.config.get('notification_enabled', True):
                try:
                    _show_windows_toast(
                        '⛔ CatchBot - DAILY CATCH LIMIT!',
                        'You reached the daily catch limit! Bot is paused.',
                        timeout=60
                    )
                except Exception:
                    pass
            
            # Alarm-Sound (soft)
            if WINDOWS and self.config.get('sound_enabled', True):
                def limit_alert():
                    try:
                        volume = self.config.get('alarm_volume', 33)
                        for _ in range(3):
                            wav_data = _generate_alarm_wav(volume=volume, frequency=800, duration_ms=300)
                            winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                            time_module.sleep(0.15)
                        wav_data = _generate_alarm_wav(volume=volume, frequency=600, duration_ms=600)
                        winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                    except Exception:
                        pass
                threading.Thread(target=limit_alert, daemon=True).start()
            
            # Webhook-Alert senden
            if self.config.get('webhook', {}).get('notify_catch_limit', True):
                self.send_webhook_alert(
                    "DAILY CATCH LIMIT REACHED!",
                    "The daily catch limit has been reached. Bot is paused.\nVote or become a Patreon Supporter to remove the limit.",
                    color=0xE74C3C
                )
    
    # ═════════════════════════════════════════════════════════════════
    #  CATCH RESULT ERKENNUNG (Gefangen / Geflohen)
    # ═════════════════════════════════════════════════════════════════
    
    async def check_catch_result(self, message):
        """Checks if a Pokemon was caught or fled and saves the result"""
        # Deduplicate: skip if we already processed this message ID
        # (PokeMeow sends a message then edits it, so both on_message and on_message_edit fire)
        if not hasattr(self, '_processed_catch_ids'):
            self._processed_catch_ids = set()
        if message.id in self._processed_catch_ids:
            return
        # Prevent memory leak: keep only last 200 IDs
        if len(self._processed_catch_ids) > 200:
            self._processed_catch_ids = set(list(self._processed_catch_ids)[-100:])
        
        all_text = ""
        embed_only_text = ""  # NUR Embed-Text fuer Pokemon-Name-Extraktion (ohne message.content/Buddy-Spam)
        pokemon_name = "?"
        rarity = "?"
        
        if message.embeds:
            for embed in message.embeds:
                embed_dict = embed.to_dict()
                if 'title' in embed_dict:
                    all_text += str(embed_dict['title']) + " "
                    embed_only_text += str(embed_dict['title']) + " "
                if 'description' in embed_dict:
                    all_text += str(embed_dict['description']) + " "
                    embed_only_text += str(embed_dict['description']) + " "
                if 'fields' in embed_dict:
                    for field in embed_dict['fields']:
                        if 'name' in field:
                            all_text += str(field['name']) + " "
                            embed_only_text += str(field['name']) + " "
                        if 'value' in field:
                            all_text += str(field['value']) + " "
                            embed_only_text += str(field['value']) + " "
                if 'footer' in embed_dict and 'text' in embed_dict['footer']:
                    all_text += str(embed_dict['footer']['text']) + " "
                    embed_only_text += str(embed_dict['footer']['text']) + " "
        
        if message.content:
            all_text += message.content
        
        if not all_text.strip():
            return
        
        # === STRIP LOOTBOX EMOJIS from all text to prevent false positives ===
        # PokeMeow "Your vote is ready!" messages contain :shiny_lootbox:, :legendary_lootbox: etc.
        # These would falsely trigger shiny/legendary detection if not cleaned.
        all_text_clean = re.sub(r':(?:rare|superrare|legendary|shiny|common|uncommon)_lootbox:', '', all_text)
        all_text_clean = re.sub(r':\w*(?:rare|legendary|shiny|uncommon|common)\w*:', '', all_text_clean)
        
        all_text_lower = all_text_clean.lower()
        
        # Rarity aus dem Embed-Text extrahieren (nicht aus message.content)
        rarity_match = re.search(r'rarity:\s*([\w\s\-]+)\s*\(', embed_only_text, re.IGNORECASE)
        if rarity_match:
            rarity = rarity_match.group(1).strip()
        
        # === SHINY DETECTION: Check if "Shiny" appears in the catch/embed text ===
        # ONLY check embed text for shiny, NOT message.content (which has lootbox emojis)
        is_shiny = False
        if rarity and 'shiny' in rarity.lower():
            is_shiny = True
        elif 'shiny' in embed_only_text.lower():
            # Fallback: check EMBED text only for "Shiny" keyword (e.g. "Shiny Ferroseed")
            is_shiny = True
        
        # Pokemon gefangen?
        # IMPORTANT: PokeMeow sends TWO messages per catch:
        #   1) The actual catch result embed (contains "Rarity:" + "You caught")
        #   2) A "Great work/Congratulations" embed (contains "You caught" but NO "Rarity:")
        # We ONLY process message #1 by requiring "rarity:" to be present in the embed.
        embed_lower = embed_only_text.lower()
        has_rarity_info = 'rarity:' in embed_lower
        has_catch_result = 'you caught a' in embed_lower or 'you caught' in embed_lower
        has_flee_result = 'broke out of the' in embed_lower or 'got away' in embed_lower
        # Fish catch results have "balls left" but no "rarity:" -- use this to detect them
        # without triggering on the "Great work / Congratulations" message (which has neither)
        has_balls_left = 'balls left' in embed_lower
        is_fish_result = not has_rarity_info and has_balls_left
        
        # For fish catches with no rarity info, default to "Common"
        if is_fish_result and rarity == "?":
            rarity = "Common"
        
        if (has_rarity_info or is_fish_result) and has_catch_result:
            # Debug: Zeige bereinigten Text (NUR Embed)
            cleaned_debug = self.clean_discord_text(embed_only_text)
            self.log(f"[NAME-DEBUG] Embed-Text: '{cleaned_debug[:200]}'")
            
            # === Pokemon-Name NUR aus dem Embed-Text suchen (verhindert Buddy-Verwechslung) ===
            found_name = self.find_pokemon_name_in_text(embed_only_text)
            if found_name:
                pokemon_name = found_name
                self.log(f"[NAME-LOOKUP] Pokemon from Embed/name list detected: '{pokemon_name}'")
            else:
                # Fallback: Regex-Extraktion NUR aus Embed-Text (clean markdown first)
                cleaned_embed = self.clean_discord_text(embed_only_text)
                catch_match = re.search(r'[Yy]ou caught (?:a\s+)?([A-Za-z][\w\s\-\'\.]*?)\s*(?:with|!)', cleaned_embed)
                if catch_match:
                    pokemon_name = catch_match.group(1).strip()
                if pokemon_name == "?":
                    wild_match = re.search(r'(?:found|fished) a wild\s+([A-Za-z][\w\s\-\'\.]*?)\s*!', cleaned_embed)
                    if wild_match:
                        pokemon_name = wild_match.group(1).strip()
                self.log(f"[NAME-LOOKUP] Name list: no match, Regex fallback (Embed): '{pokemon_name}'")
            
            self.last_catch_result = "caught"
            self._processed_catch_ids.add(message.id)
            
            # Determine catch method for logging and webhook
            _method = "fish" if is_fish_result else "catch"
            _method_label = "FISHED" if is_fish_result else "CAUGHT"
            
            # === SHINY HIGHLIGHT in logs ===
            if is_shiny:
                self.log(f"{_method_label}! **Shiny {pokemon_name}** (Rarity: {rarity})")
                print(f"\n{Fore.LIGHTMAGENTA_EX}{'*' * 66}{Style.RESET_ALL}")
                print(f"{Fore.LIGHTMAGENTA_EX}  ✨✨  SHINY {_method_label}! **Shiny {pokemon_name}**  ✨✨{Style.RESET_ALL}")
                print(f"{Fore.LIGHTMAGENTA_EX}{'*' * 66}{Style.RESET_ALL}")
            else:
                self.log(f"{_method_label}! {pokemon_name} (Rarity: {rarity})")
            self.record_catch(pokemon_name, rarity, caught=True, original_message=message, catch_method=_method, is_event=self.last_catch_is_event)
        
        # Pokemon geflohen?
        elif (has_rarity_info or is_fish_result) and has_flee_result:
            # Debug: Zeige bereinigten Text (NUR Embed)
            cleaned_debug = self.clean_discord_text(embed_only_text)
            self.log(f"[NAME-DEBUG] Embed-Text: '{cleaned_debug[:200]}'")
            
            # === Pokemon-Name NUR aus dem Embed-Text suchen (verhindert Buddy-Verwechslung) ===
            found_name = self.find_pokemon_name_in_text(embed_only_text)
            if found_name:
                pokemon_name = found_name
                self.log(f"[NAME-LOOKUP] Pokemon from Embed/name list detected: '{pokemon_name}'")
            else:
                # Fallback: Regex-Extraktion NUR aus Embed-Text (clean markdown first)
                cleaned_embed = self.clean_discord_text(embed_only_text)
                flee_match = re.search(r'([A-Za-z][\w\s\-\'\.]*?)\s*broke out of the', cleaned_embed)
                if flee_match:
                    pokemon_name = flee_match.group(1).strip()
                if pokemon_name == "?":
                    wild_match = re.search(r'(?:found|fished) a wild\s+([A-Za-z][\w\s\-\'\.]*?)\s*!', cleaned_embed)
                    if wild_match:
                        pokemon_name = wild_match.group(1).strip()
                self.log(f"[NAME-LOOKUP] Name list: no match, Regex fallback (Embed): '{pokemon_name}'")
            
            self.last_catch_result = "fled"
            self._processed_catch_ids.add(message.id)
            _method = "fish" if is_fish_result else "catch"
            _method_label = "FISHED" if is_fish_result else ""
            _fled_prefix = f"{_method_label} & FLED" if _method_label else "FLED"
            if is_shiny:
                self.log(f"{_fled_prefix}! **Shiny {pokemon_name}** escaped! (Rarity: {rarity})")
                print(f"\n{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
                print(f"{Fore.RED}  ✨  SHINY {_fled_prefix}! **Shiny {pokemon_name}** escaped!  ✨{Style.RESET_ALL}")
                print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
            else:
                self.log(f"{_fled_prefix}! {pokemon_name} escaped! (Rarity: {rarity})")
            self.record_catch(pokemon_name, rarity, caught=False, original_message=message, catch_method=_method, is_event=self.last_catch_is_event)
    
    # ═════════════════════════════════════════════════════════════════
    #  STATISTIKEN & TRACKING
    # ═════════════════════════════════════════════════════════════════
    
    def record_catch(self, pokemon_name, rarity, caught, original_message=None, catch_method="catch", is_event=False):
        """Zeichnet einen Fang-Versuch in den Session- und Persistent-Stats auf"""
        rarity_clean = rarity.strip() if rarity else "?"
        
        self.session_stats['total_encounters'] += 1
        
        # Track fish stats separately
        is_fish = catch_method == "fish"
        
        if caught:
            self.session_stats['total_caught'] += 1
            self.session_stats['caught_by_rarity'][rarity_clean] = \
                self.session_stats['caught_by_rarity'].get(rarity_clean, 0) + 1
            self.persistent_stats['total_caught_alltime'] += 1
            
            if is_fish:
                self.session_stats['total_fished'] += 1
                self.persistent_stats['total_fished_alltime'] = \
                    self.persistent_stats.get('total_fished_alltime', 0) + 1
            
            # Shiny/Legendary tracken
            rarity_lower = rarity_clean.lower()
            now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
            
            if 'shiny' in rarity_lower:
                self.persistent_stats['shinys_caught'] += 1
                self.persistent_stats['shiny_list'].append({
                    'name': pokemon_name, 'date': now_str, 'rarity': rarity_clean
                })
                self.session_stats['best_catches'].append(
                    f"SHINY {pokemon_name} ({now_str})"
                )
            
            if 'legendary' in rarity_lower:
                self.persistent_stats['legendarys_caught'] += 1
                self.persistent_stats['legendary_list'].append({
                    'name': pokemon_name, 'date': now_str, 'rarity': rarity_clean
                })
                self.session_stats['best_catches'].append(
                    f"LEGENDARY {pokemon_name} ({now_str})"
                )
            
            # Only Shiny and Legendary are tracked as "best catches"
        else:
            self.session_stats['total_fled'] += 1
            self.session_stats['fled_by_rarity'][rarity_clean] = \
                self.session_stats['fled_by_rarity'].get(rarity_clean, 0) + 1
            self.persistent_stats['total_fled_alltime'] += 1
            
            if is_fish:
                self.session_stats['total_fished_fled'] += 1
                self.persistent_stats['total_fished_fled_alltime'] = \
                    self.persistent_stats.get('total_fished_fled_alltime', 0) + 1
        
        # Persistent speichern nach jedem Catch
        self.save_persistent_stats()
        
        # Webhook senden (prueft intern ob Rarity relevant ist)
        self.send_webhook(pokemon_name, rarity_clean, caught, original_message=original_message, is_event=is_event)
        
        # Shared Success Webhook senden (bei jedem erfolgreichen Catch)
        if caught:
            self.send_shared_success_webhook(pokemon_name, rarity=rarity_clean, original_message=original_message, catch_method=catch_method, is_event=is_event)
    
