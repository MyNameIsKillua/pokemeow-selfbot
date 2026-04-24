"""CatchingMixin: check_and_catch_pokemon + catch_pokemon."""
import asyncio
import random
import re
import time as time_module
from datetime import datetime, timedelta
from colorama import Fore, Style

import discord


class CatchingMixin:
    async def check_and_catch_pokemon(self, message):
        """Prüft ob eine Pokemon-Spawn Nachricht vorliegt und fängt es automatisch"""
        self.log(f"[CATCH-CHECK] Funktion aufgerufen! catching={self.catching}, author={message.author}, embeds={len(message.embeds)}")
        if self.catching:
            self.log(f"[CATCH-CHECK] Abort: catching=True (last catch still running)")
            return
        
        rarity = None
        pokemon_name = None
        
        # Sammle allen sichtbaren Text
        all_text = ""
        raw_text = ""  # Originaltext (nicht lowercase) fuer Pokemon-Name Extraktion
        
        if message.embeds:
            for embed in message.embeds:
                embed_dict = embed.to_dict()
                
                if 'title' in embed_dict:
                    all_text += str(embed_dict['title']).lower() + " "
                    raw_text += str(embed_dict['title']) + " "
                
                if 'description' in embed_dict:
                    desc = str(embed_dict['description'])
                    all_text += desc.lower() + " "
                    raw_text += desc + " "
                
                if 'fields' in embed_dict:
                    for field in embed_dict['fields']:
                        if 'name' in field:
                            all_text += str(field['name']).lower() + " "
                            raw_text += str(field['name']) + " "
                        if 'value' in field:
                            all_text += str(field['value']).lower() + " "
                            raw_text += str(field['value']) + " "
                
                if 'footer' in embed_dict and 'text' in embed_dict['footer']:
                    all_text += str(embed_dict['footer']['text']).lower() + " "
                    raw_text += str(embed_dict['footer']['text']) + " "
        
        # WICHTIG: message.content wird NICHT verwendet!
        # PokeMeow-Spawns haben alles im Embed. message.content kann andere Pokemon-Namen
        # enthalten (z.B. Buddy-Text) und verursacht false positives bei der Name-Erkennung.
        
        # === NEUE METHODE: Pokemon-Name aus der Namensliste suchen (NUR Embed-Text) ===
        found_name = self.find_pokemon_name_in_text(raw_text)
        if found_name:
            pokemon_name = found_name
            self.log(f"[NAME] Pokemon from name list detected: '{pokemon_name}'")
        else:
            # Fallback: Regex-Extraktion (alte Methode)
            # Use cleaned text (markdown stripped) so **Iron-Leaves**! becomes Iron-Leaves!
            cleaned_raw = self.clean_discord_text(raw_text)
            name_match = re.search(r'(?:found|fished) a wild\s+([A-Za-z][\w\s\-\'\.]*?)\s*!', cleaned_raw)
            if name_match:
                pokemon_name = name_match.group(1).strip()
                self.log(f"[NAME] Pokemon per Regex erkannt (Fallback): '{pokemon_name}'")
        
        # DEBUG: Logge Nachrichten mit Embeds
        if message.embeds:
            has_components = hasattr(message, 'components') and message.components
            num_buttons = 0
            if has_components:
                try:
                    num_buttons = len(message.components[0].children)
                except Exception:
                    pass
            self.log(f"[DEBUG] Nachricht von {message.author}: Embeds={len(message.embeds)}, Buttons={num_buttons}, Text(100)={all_text[:100]}")
        
        # FILTER 1: Catch-Bestätigungen ignorieren
        if 'you caught' in all_text or 'well done' in all_text or 'catch rate' in all_text:
            self.log(f"[CATCH-CHECK] Filter 1: Catch confirmation detected, ignored")
            return
        
        # FILTER 2: Captcha-Nachrichten ignorieren (werden separat behandelt)
        if 'captcha' in all_text:
            self.log(f"[CATCH-CHECK] Filter 2: Captcha detected, ignored")
            return
        
        # FILTER 3: Nur Nachrichten mit Buttons
        if not hasattr(message, 'components') or not message.components:
            self.log(f"[CATCH-CHECK] Filter 3: No Buttons/Components found, ignored")
            return
        
        try:
            first_row = message.components[0]
            num_buttons = len(first_row.children)
        except Exception as e:
            self.log(f"[DEBUG] Error reading buttons: {str(e)}")
            return
        
        # FILTER 4: Spawn-Nachrichten haben 3-5 Ball-Buttons
        # (PokeMeow zeigt weniger Buttons wenn man bestimmte Baelle nicht besitzt)
        if num_buttons < 3 or num_buttons > 5:
            self.log(f"[CATCH-CHECK] Filter 4: {num_buttons} Buttons (expected 3-5), ignored")
            return
        
        # FILTER 5: Lootbox-Emojis aus Text entfernen (verursachen false positives)
        # Diese Emojis tauchen bei Vote-Rewards auf: :rare_lootbox: :superrare_lootbox: etc.
        clean_text = re.sub(r':(?:rare|superrare|legendary|shiny|common|uncommon)_lootbox:', '', all_text)
        # Auch andere potenzielle Emoji-Patterns entfernen die Rarity-Keywords enthalten
        clean_text = re.sub(r':\w*(?:rare|legendary|shiny|uncommon|common)\w*:', '', clean_text)
        
        # === EVENT POKEMON DETECTION ===
        # PokeMeow uses a RED embed border for Event Pokemon.
        # Check embed color to detect event spawns.
        is_event = False
        if message.embeds:
            for embed in message.embeds:
                embed_dict = embed.to_dict()
                embed_color = embed_dict.get('color', 0)
                # Red embed color range: high red component, low green/blue
                r = (embed_color >> 16) & 0xFF
                g = (embed_color >> 8) & 0xFF
                b = embed_color & 0xFF
                if r > 180 and g < 80 and b < 80:
                    is_event = True
                    self.log(f"[EVENT] Red embed detected (color=#{embed_color:06X}, RGB={r},{g},{b}) -> Event Pokemon!")
                    break
        
        # Rarity erkennen (auf bereinigtem Text)
        if 'shiny' in clean_text:
            rarity = 'shiny'
        elif 'legendary' in clean_text:
            rarity = 'legendary'
        elif 'super rare' in clean_text or 'super-rare' in clean_text:
            rarity = 'super_rare'
        elif 'uncommon' in clean_text:
            rarity = 'uncommon'
        elif 'rare' in clean_text and 'super' not in clean_text and 'uncommon' not in clean_text:
            rarity = 'rare'
        elif 'common' in clean_text and 'uncommon' not in clean_text:
            rarity = 'common'
        
        if not rarity:
            # No rarity keyword found -- this happens for fishing spawns where
            # the rarity is only shown by MeowHelper in a separate message.
            # Use MeowHelper rarity if available, otherwise default to 'common'.
            fish_rarity = getattr(self, '_fish_rarity', None)
            if fish_rarity:
                rarity = fish_rarity
                self.log(f"Using MeowHelper rarity for fish spawn: {rarity}")
            else:
                rarity = 'common'
                self.log(f"No rarity keyword and no MeowHelper rarity, defaulting to '{rarity}'. Text: {all_text[:200]}")
        
        self.log(f"✅ SPAWN DETECTED! Rarity={rarity}, Pokemon={pokemon_name}, Buttons={num_buttons}, Event={is_event}")
        
        # PokeMeow responded! Reset rate limit counter
        self.on_pokemeow_response()
        
        await self.catch_pokemon(message, rarity, pokemon_name, is_event=is_event)
    
    async def catch_pokemon(self, message, rarity, pokemon_name=None, is_event=False):
        """Klickt den passenden Pokeball-Button basierend auf der Rarity"""
        if self.catching:
            return
        
        self.catching = True

        try:
            # === FISH FORCED BALL: Highest priority override for fishing ===
            # When a fish spawn is detected, PokeMeow marks the recommended ball
            # with a *_unlocked emoji. handle_fishing parses this and sets
            # self._fish_forced_ball. This bypasses whitelist/event/rarity rules
            # since the PokeMeow recommendation is 100% reliable for fishing.
            fish_forced = getattr(self, '_fish_forced_ball', None) if getattr(self, 'fishing_active', False) else None

            # === POKEMON WHITELIST: Highest priority override (for non-fishing) ===
            # If the pokemon name matches a whitelisted entry, use that ball regardless of rarity/event
            whitelist = self.config.get('pokemon_whitelist', {})
            whitelist_match = None
            if pokemon_name and whitelist and not fish_forced:
                # Case-insensitive lookup
                name_lower = pokemon_name.lower()
                for wl_name, wl_ball in whitelist.items():
                    if wl_name.lower() == name_lower:
                        whitelist_match = wl_ball
                        break

            if fish_forced:
                ball_command = fish_forced
                self.log(f"[FISH-FORCED] {pokemon_name or 'fish'} -> Using {ball_command} (PokeMeow recommended)")
                print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] [FISH] Recommended ball -> {ball_command}{Style.RESET_ALL}")
            elif whitelist_match:
                ball_command = whitelist_match
                self.log(f"[WHITELIST] {pokemon_name} -> Using {ball_command} (whitelist override)")
                print(f"{Fore.MAGENTA}[{datetime.now().strftime('%H:%M:%S')}] [WHITELIST] {pokemon_name} -> {ball_command}{Style.RESET_ALL}")
            else:
                # === EVENT POKEMON: Override ball selection ===
                # If event pokemon detected (red embed), use special ball rules:
                #   - Common/Uncommon/Rare/Super Rare -> Premier Ball (if enabled)
                #   - Legendary/Shiny -> Masterball (if enabled)
                event_config = self.config.get('event_pokemon', {})
                if is_event and rarity in ('common', 'uncommon', 'rare', 'super_rare') and event_config.get('premierball_enabled', True):
                    ball_command = event_config.get('event_ball_lower', 'prb')
                    self.log(f"[EVENT] Event Pokemon ({rarity}) -> Using {ball_command} override")
                elif is_event and rarity in ('legendary', 'shiny') and event_config.get('masterball_enabled', True):
                    ball_command = event_config.get('event_ball_upper', 'mb')
                    self.log(f"[EVENT] Event Pokemon ({rarity}) -> Using {ball_command} override")
                else:
                    ball_command = self.config['catch_rules'].get(rarity, 'pb')
            
            ball_names = {
                'pb': 'Pokeball',
                'gb': 'Greatball',
                'ub': 'Ultraball',
                'prb': 'Premierball',
                'mb': 'Masterball'
            }
            
            ball_name = ball_names.get(ball_command, ball_command)
            pokemon_info = f" ({pokemon_name})" if pokemon_name else ""
            
            # === DYNAMIC BALL DETECTION: Read button emojis to find exact ball positions ===
            # PokeMeow shows only buttons for balls the user owns.
            # Order is always: PB, GB, UB, PRB, MB but missing balls are skipped.
            # We read emoji names to map each button to its ball type.
            try:
                action_row = message.components[0]
                num_buttons = len(action_row.children)
            except Exception:
                num_buttons = 0
            
            # Map ball emoji names / custom_id patterns to ball codes
            ball_emoji_map = {
                'pokeball': 'pb', 'poke_ball': 'pb', 'pokéball': 'pb',
                'greatball': 'gb', 'great_ball': 'gb',
                'ultraball': 'ub', 'ultra_ball': 'ub',
                'premierball': 'prb', 'premier_ball': 'prb', 'premier': 'prb',
                'masterball': 'mb', 'master_ball': 'mb',
                'moonball': 'mnb', 'moon_ball': 'mnb',
                'friendball': 'fb', 'friend_ball': 'fb',
            }
            
            # Detect balls from button emoji names
            detected_balls = {}
            try:
                for idx, btn in enumerate(action_row.children):
                    btn_id = ''
                    if hasattr(btn, 'emoji') and btn.emoji:
                        emoji_name = str(btn.emoji.name).lower() if hasattr(btn.emoji, 'name') else str(btn.emoji).lower()
                        btn_id = emoji_name
                    if hasattr(btn, 'custom_id') and btn.custom_id:
                        btn_id += ' ' + str(btn.custom_id).lower()
                    if hasattr(btn, 'label') and btn.label:
                        btn_id += ' ' + str(btn.label).lower()
                    
                    for key, ball_code in ball_emoji_map.items():
                        if key in btn_id:
                            detected_balls[ball_code] = idx
                            self.log(f"[BALL-DETECT] Button {idx}: '{btn_id}' -> {ball_code}")
                            break
            except Exception as e:
                self.log(f"[BALL-DETECT] Error reading buttons: {str(e)}")
            
            # Use detected mapping if we found balls, otherwise fall back to position-based
            if detected_balls and ball_command in detected_balls:
                button_index = detected_balls[ball_command]
                self.log(f"[BALL-DETECT] Detected {ball_command} at index {button_index}")
            elif detected_balls:
                # Desired ball not available, find best fallback
                fallback_order = {'mb': ['ub', 'gb', 'pb'], 'prb': ['ub', 'gb', 'pb'], 
                                  'ub': ['gb', 'pb'], 'gb': ['pb'], 'pb': []}
                fallback = fallback_order.get(ball_command, [])
                found_fallback = False
                for fb in fallback:
                    if fb in detected_balls:
                        button_index = detected_balls[fb]
                        ball_name = f"{ball_names.get(fb, fb)} (Fallback)"
                        self.log(f"[BALL-DETECT] {ball_command} not found, falling back to {fb} at index {button_index}")
                        found_fallback = True
                        break
                if not found_fallback:
                    button_index = 0
                    ball_name = "Pokeball (Fallback)"
            else:
                # No emoji detection worked, use position-based fallback
                if num_buttons >= 7:
                    ball_button_index = {'pb': 0, 'gb': 1, 'ub': 2, 'prb': 3, 'mb': 4, 'mnb': 5, 'fb': 6}
                elif num_buttons == 5:
                    ball_button_index = {'pb': 0, 'gb': 1, 'ub': 2, 'prb': 3, 'mb': 4}
                elif num_buttons == 4:
                    ball_button_index = {'pb': 0, 'gb': 1, 'ub': 2, 'prb': 3, 'mb': 2}
                else:
                    ball_button_index = {'pb': 0, 'gb': 1, 'ub': 2, 'prb': 2, 'mb': 2}
                button_index = ball_button_index.get(ball_command, 0)
                if button_index >= num_buttons:
                    button_index = 0
                    ball_name = f"Pokeball (Fallback)"
            
            self.log(f"Rarity: {rarity} -> Ball: {ball_name} -> Button-Index: {button_index} (of {num_buttons} Buttons)")
            
            try:
                button = action_row.children[button_index]
                
                # === CATCH REACTION DELAY (always active) ===
                # Simulate human reaction time before clicking the ball
                ab = self.config.get('anti_ban', {})
                react_min = ab.get('catch_reaction_min', 1)
                react_max = ab.get('catch_reaction_max', 3)
                react_delay = random.uniform(react_min, react_max)
                self.log(f"🛡️ Catch Reaction: Waiting {react_delay:.1f}s before clicking ball...")
                await asyncio.sleep(react_delay)
                
                # Catch-Result VORHER zurücksetzen (bevor button.click() aufgerufen wird,
                # da das Edit-Event schon während des click() feuern kann)
                self.last_catch_result = None
                self.last_catch_is_event = is_event
                
                await button.click()
                
                pokemon_display = f" {pokemon_name}" if pokemon_name else ""
                # Shiny highlight in catch log
                if rarity == 'shiny':
                    log_msg = f"\u2728 SHINY{pokemon_display} \u2192 {ball_name} clicked!"
                else:
                    log_msg = f"\U0001f3af {rarity.upper()}{pokemon_display} \u2192 {ball_name} clicked!"
                self.log(log_msg)
                
                # Farbige Ausgabe je nach Rarity
                rarity_colors = {
                    'common': Fore.CYAN,           # Blau
                    'uncommon': Fore.CYAN,          # Blau
                    'rare': Fore.YELLOW,            # Orange/Gelb
                    'super_rare': Fore.LIGHTYELLOW_EX,  # Hellgelb
                    'legendary': Fore.MAGENTA,      # Lila
                    'shiny': Fore.LIGHTMAGENTA_EX,  # Pink/Rosa
                }
                color = rarity_colors.get(rarity, Fore.GREEN)
                
                # Event Pokemon -> RED font in console
                if is_event:
                    color = Fore.RED
                
                # Zeile OHNE Newline drucken, warten auf Catch-Result
                event_tag = f"{Fore.RED}[EVENT] {Style.RESET_ALL}" if is_event else ""
                print(f"{event_tag}{color}[{datetime.now().strftime('%H:%M:%S')}] {log_msg}{Style.RESET_ALL}", end="", flush=True)
                
                # Warten bis PokeMeow das Ergebnis schickt (max 8 Sekunden)
                for _ in range(40):
                    if self.last_catch_result is not None:
                        break
                    await asyncio.sleep(0.2)
                
                # Catch-Result anhängen
                is_fish = getattr(self, 'fishing_active', False)
                if self.last_catch_result == "caught":
                    result_label = "Fished" if is_fish else "Caught"
                    print(f" {Fore.GREEN}\u2705 {result_label}{Style.RESET_ALL}")
                elif self.last_catch_result == "fled":
                    print(f" {Fore.RED}\u274c Fled{Style.RESET_ALL}")
                else:
                    print()  # Nur Newline wenn kein Result kam
                
                self.last_catch_result = None
                
            except Exception as e:
                self.log(f"ERROR during button click: {str(e)}")
                print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] Button click error: {str(e)}{Style.RESET_ALL}")
            
            await asyncio.sleep(2)
            
        except Exception as e:
            self.log(f"Error during catch: {str(e)}")
            print(f"{Fore.RED}Error during catch: {str(e)}{Style.RESET_ALL}")
        
        finally:
            self.catching = False
    
    # ════════════════════════════════════════════════════════════════
    #  HOTKEY SYSTEM
    # ════════════════════════════════════════════════════════════════
    
