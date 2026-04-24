"""FishingMixin: handle_fishing (;f fishing sequence)."""
import asyncio
import random
import re
import time as time_module
from datetime import datetime, timedelta
from colorama import Fore, Style

import discord


class FishingMixin:
    async def handle_fishing(self, channel):
        """Full fishing flow: ;f -> wait for bite/nibble -> click rod -> detect rarity from MeowHelper -> throw ball -> handle result.
        
        Flow:
        1. Send ;f
        2. PokeMeow edits its embed:
           - "Not even a nibble" -> no fish, return (main loop will wait 7-10s before next ;p)
           - "Oh! A bite!" -> rod button appears, click it
        3. After clicking rod, PokeMeow sends a NEW message with the Pokemon spawn (with ball buttons)
           - The check_and_catch_pokemon handler in on_message picks this up automatically
           - It reads the rarity from the spawn embed text (PokeMeow includes rarity emojis)
        4. If PokeMeow says "got away" or the Pokemon breaks free -> return
        5. If caught -> return (record_catch already handles webhooks including shared fishing webhook)
        """
        if self.fishing_active:
            return
        
        self.fishing_active = True
        try:
            # Build fish command (with optional custom message)
            fish_cmd = ';f'
            cmf_cfg = self.config.get('custom_message_fish', {})
            if cmf_cfg.get('enabled', False) and cmf_cfg.get('message', ''):
                cmf_chance = cmf_cfg.get('chance', 50)
                if random.randint(1, 100) <= cmf_chance:
                    fish_cmd = f";f {cmf_cfg['message']}"
                    self.log(f"[FISH] Custom fish message: {fish_cmd}")
            
            self.log(f"[FISH] Sending {fish_cmd} command...")
            await self.send_command(channel, fish_cmd)
            
            # Wait for PokeMeow to edit its embed with bite/nibble result (up to 20s)
            # PokeMeow first sends an embed, then EDITS it to add the result
            # We need to detect EITHER "bite" OR "nibble" in the edited message
            bite_msg = None
            nibble = False
            
            # Use a combined check: wait for any edit that contains "bite" or "nibble"
            def fish_check(before, after):
                if str(after.channel.id) != str(channel.id):
                    return False
                if self.client and self.client.user and after.author.id == self.client.user.id:
                    return False
                
                text = ""
                if after.embeds:
                    for embed in after.embeds:
                        embed_dict = embed.to_dict()
                        if 'description' in embed_dict:
                            text += str(embed_dict['description']).lower()
                        if 'title' in embed_dict:
                            text += str(embed_dict['title']).lower()
                if after.content:
                    text += after.content.lower()
                
                return 'bite' in text or 'nibble' in text
            
            try:
                before, after = await self.client.wait_for('message_edit', check=fish_check, timeout=20)
                bite_msg = after
            except asyncio.TimeoutError:
                self.log(f"[FISH] Timeout waiting for PokeMeow fish response")
                return
            
            if not bite_msg:
                self.log(f"[FISH] No response from PokeMeow")
                return
            
            # Check the text of the response
            fish_text = ""
            if bite_msg.embeds:
                for embed in bite_msg.embeds:
                    embed_dict = embed.to_dict()
                    if 'description' in embed_dict:
                        fish_text += str(embed_dict['description']).lower()
            if bite_msg.content:
                fish_text += bite_msg.content.lower()
            
            # "Not even a nibble" -> no fish
            if 'nibble' in fish_text:
                self.log(f"[FISH] Not even a nibble! No fish this time.")
                print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] \U0001f3a3 Not even a nibble...{Style.RESET_ALL}")
                return
            
            # "Oh! A bite!" -> click the rod button
            if 'bite' in fish_text:
                self.log(f"[FISH] Oh! A bite! Looking for rod button...")
                
                # Find and click the rod button (should be the only button)
                rod_clicked = False
                if hasattr(bite_msg, 'components') and bite_msg.components:
                    try:
                        for row in bite_msg.components:
                            for btn in row.children:
                                # Click the first button (rod button)
                                await asyncio.sleep(random.uniform(0.3, 0.8))
                                await btn.click()
                                rod_clicked = True
                                self.log(f"[FISH] Rod button clicked!")
                                print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] \U0001f3a3 Bite! Rod button clicked!{Style.RESET_ALL}")
                                break
                            if rod_clicked:
                                break
                    except Exception as e:
                        self.log(f"[FISH] Error clicking rod button: {str(e)}")
                        return
                
                if not rod_clicked:
                    self.log(f"[FISH] No rod button found!")
                    return
                
                # After clicking the rod button, PokeMeow EDITS the same message to show
                # the fish Pokemon spawn with ball buttons.
                # on_message_edit does NOT call check_and_catch_pokemon, so we must
                # detect the edit ourselves and call check_and_catch_pokemon directly.
                self.log(f"[FISH] Rod clicked, waiting for Pokemon spawn edit...")
                
                # Wait for the message to be edited with the Pokemon spawn
                # PokeMeow edits the same message: content has "found a wild" or "fished a wild"
                def spawn_edit_check(before, after):
                    if str(after.channel.id) != str(channel.id):
                        return False
                    if self.client and self.client.user and after.author.id == self.client.user.id:
                        return False
                    
                    text = ""
                    if after.content:
                        text += after.content.lower()
                    if after.embeds:
                        for embed in after.embeds:
                            embed_dict = embed.to_dict()
                            if 'description' in embed_dict:
                                text += str(embed_dict['description']).lower()
                            if 'title' in embed_dict:
                                text += str(embed_dict['title']).lower()
                    
                    # Just need spawn text -- buttons may or may not be present in the edit
                    return 'found a wild' in text or 'fished a wild' in text or 'to catch it' in text
                
                try:
                    before, spawn_msg = await self.client.wait_for('message_edit', check=spawn_edit_check, timeout=15)
                    
                    # Small delay to ensure components/buttons are fully loaded on the edited message
                    await asyncio.sleep(0.5)
                    
                    # Re-fetch the message to get the latest state with buttons
                    try:
                        spawn_msg = await channel.fetch_message(spawn_msg.id)
                    except Exception as e:
                        self.log(f"[FISH] Could not re-fetch message: {str(e)}, using original")
                    
                    has_buttons = hasattr(spawn_msg, 'components') and spawn_msg.components
                    btn_count = 0
                    if has_buttons:
                        try:
                            btn_count = len(spawn_msg.components[0].children)
                        except Exception:
                            pass
                    
                    spawn_content = spawn_msg.content[:150] if spawn_msg.content else 'no content'
                    self.log(f"[FISH] Spawn edit detected! Buttons={btn_count}, Content={spawn_content}")

                    # === FISH BALL RECOMMENDATION ===
                    # PokeMeow marks the recommended ball with a custom emoji ending in
                    # "_unlocked" (e.g. :pokeball_unlocked:). All other balls get
                    # "_locked". We parse message.content for the unlocked ball and
                    # force that ball in catch_pokemon, bypassing rarity/whitelist/event rules.
                    # Dive/Beast recommendations are mapped to Masterball (user policy).
                    self._fish_forced_ball = None
                    try:
                        full_content = spawn_msg.content or ''
                        import re as _re_fb
                        unlocked_match = _re_fb.search(
                            r'(pokeball|greatball|ultraball|premierball|diveball|masterball|beastball)_unlocked',
                            full_content,
                            _re_fb.IGNORECASE,
                        )
                        if unlocked_match:
                            unlocked_ball = unlocked_match.group(1).lower()
                            unlocked_to_cmd = {
                                'pokeball': 'pb',
                                'greatball': 'gb',
                                'ultraball': 'ub',
                                'premierball': 'prb',
                                'masterball': 'mb',
                                'diveball': 'mb',    # user policy: dive -> masterball
                                'beastball': 'mb',   # user policy: beast -> masterball
                            }
                            self._fish_forced_ball = unlocked_to_cmd.get(unlocked_ball)
                            self.log(f"[FISH] Recommended ball from PokeMeow: :{unlocked_ball}_unlocked: -> {self._fish_forced_ball}")
                        else:
                            self.log(f"[FISH] No *_unlocked emoji found in spawn content; falling back to rarity rules")
                    except Exception as _e_fb:
                        self.log(f"[FISH] Error parsing recommended ball: {str(_e_fb)}")

                    if btn_count >= 3:
                        self.fishing_active = True
                        
                        # Wait for MeowHelper to post the rarity before clicking a ball
                        # MeowHelper posts an embed with a custom emoji indicating rarity
                        # e.g. <:Common:123456>, <:Uncommon:123456>, <:Superrare:123456>, etc.
                        fish_rarity = None
                        self.log(f"[FISH] Waiting for MeowHelper rarity message...")
                        
                        # Rarity emoji names -> internal rarity keys
                        _meow_emoji_map = {
                            'common': 'common',
                            'uncommon': 'uncommon',
                            'rare': 'rare',
                            'superrare': 'super_rare',
                            'super_rare': 'super_rare',
                            'legendary': 'legendary',
                            'shiny': 'shiny',
                            'golden': 'golden',
                            'mythical': 'legendary',
                            'ultrabeast': 'legendary',
                            'ultra_beast': 'legendary',
                            'event': 'legendary',
                        }
                        
                        def meowhelper_rarity_check(msg):
                            """Check if this is MeowHelper's rarity message for our fish Pokemon"""
                            if str(msg.channel.id) != str(channel.id):
                                return False
                            if not msg.author.bot:
                                return False
                            # Skip PokeMeow itself (it's the one with the spawn)
                            if msg.author.id == spawn_msg.author.id:
                                return False
                            # Collect all text from message (embeds + content)
                            all_msg_text = ''
                            if msg.embeds:
                                for emb in msg.embeds:
                                    emb_dict = emb.to_dict()
                                    all_msg_text += str(emb_dict.get('description', '')) + ' '
                                    all_msg_text += str(emb_dict.get('title', '')) + ' '
                                    for field in emb_dict.get('fields', []):
                                        all_msg_text += str(field.get('name', '')) + ' ' + str(field.get('value', '')) + ' '
                            if msg.content:
                                all_msg_text += msg.content
                            # Check for custom emoji rarity pattern: <:Common:ID> or <a:Common:ID>
                            # Also check for :Common: style text (without < > wrapper)
                            all_lower = all_msg_text.lower()
                            for ename in _meow_emoji_map:
                                if f':{ename}:' in all_lower:
                                    return True
                            # Fallback: check for old-style 'rarity' keyword
                            if 'rarity' in all_lower:
                                return True
                            return False
                        
                        try:
                            meow_msg = await self.client.wait_for('message', check=meowhelper_rarity_check, timeout=0.5)
                            
                            # Extract all text from MeowHelper's message
                            meow_text = ''
                            if meow_msg.embeds:
                                for emb in meow_msg.embeds:
                                    emb_dict = emb.to_dict()
                                    meow_text += str(emb_dict.get('description', '')) + ' '
                                    meow_text += str(emb_dict.get('title', '')) + ' '
                                    for field in emb_dict.get('fields', []):
                                        meow_text += str(field.get('name', '')) + ' ' + str(field.get('value', '')) + ' '
                            if meow_msg.content:
                                meow_text += meow_msg.content
                            
                            meow_lower = meow_text.lower()
                            self.log(f"[FISH] MeowHelper raw text: {meow_text[:300]}")
                            
                            # Parse rarity from custom emoji names: <:Common:123456> or <a:Superrare:123456>
                            # Also matches :Common: without angle brackets
                            import re as _re
                            emoji_matches = _re.findall(r'<a?:(\w+):\d+>', meow_text)
                            if not emoji_matches:
                                # Fallback: try bare :EmojiName: patterns
                                emoji_matches = _re.findall(r':(\w+):', meow_text)
                            
                            for emoji_name in emoji_matches:
                                mapped = _meow_emoji_map.get(emoji_name.lower())
                                if mapped:
                                    fish_rarity = mapped
                                    self.log(f"[FISH] MeowHelper emoji rarity: :{emoji_name}: -> {fish_rarity}")
                                    break
                            
                            # Fallback: check for rarity words in text (old MeowHelper format)
                            if not fish_rarity:
                                word_map = {
                                    'golden': 'golden',
                                    'shiny': 'shiny',
                                    'legendary': 'legendary',
                                    'mythical': 'legendary',
                                    'ultra beast': 'legendary',
                                    'super rare': 'super_rare',
                                    'superrare': 'super_rare',
                                    'rare': 'rare',
                                    'uncommon': 'uncommon',
                                    'common': 'common',
                                }
                                for key, val in word_map.items():
                                    if key in meow_lower:
                                        fish_rarity = val
                                        self.log(f"[FISH] MeowHelper word rarity: '{key}' -> {fish_rarity}")
                                        break
                            
                            if not fish_rarity:
                                self.log(f"[FISH] MeowHelper message found but could not parse rarity. Text: {meow_text[:300]}")
                        except asyncio.TimeoutError:
                            self.log(f"[FISH] No MeowHelper rarity message received (timeout 0.5s)")
                        
                        # Store fish rarity so check_and_catch_pokemon can use it
                        self._fish_rarity = fish_rarity
                        
                        await self.check_and_catch_pokemon(spawn_msg)
                        
                        # Wait for catching to complete
                        wait_start = asyncio.get_event_loop().time()
                        while self.catching and asyncio.get_event_loop().time() - wait_start < 20:
                            await asyncio.sleep(0.3)
                        
                        self.fishing_active = False
                        self._fish_rarity = None
                        self._fish_forced_ball = None
                        self.log(f"[FISH] Catch sequence completed!")
                    else:
                        self.fishing_active = False
                        self._fish_rarity = None
                        self._fish_forced_ball = None
                        self.log(f"[FISH] Spawn detected but no ball buttons found ({btn_count} buttons)")
                        print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] \U0001f3a3 Spawn detected but no buttons to click{Style.RESET_ALL}")
                except asyncio.TimeoutError:
                    self.log(f"[FISH] No spawn edit detected after clicking rod (timeout)")
                    print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] \U0001f3a3 No spawn after rod click{Style.RESET_ALL}")
        
        except Exception as e:
            self.log(f"[FISH] Error in fishing flow: {str(e)}")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] Fishing error: {str(e)}{Style.RESET_ALL}")
        
        finally:
            self.fishing_active = False
            self._fish_forced_ball = None

