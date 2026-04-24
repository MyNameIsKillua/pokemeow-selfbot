"""Quest system: renewal, claim, settings menus and quest response handling."""
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


class QuestsMixin:
    def show_quest_renewer_menu(self):
        """Shows the AutoQuestRenewer configuration menu (foldable like AutoBuyer)"""
        self.print_header()
        
        aqr = self.config.get('auto_quest_renewer', {})
        enabled = aqr.get('enabled', False)
        
        def status(on):
            return f"{Fore.GREEN}✓{Style.RESET_ALL}" if on else f"{Fore.RED}✗{Style.RESET_ALL}"
        
        print(f"\n{Fore.CYAN}╔══════════════════ AUTOQUEST RENEWER ═════════════════════╗{Style.RESET_ALL}")
        print(f"\n           {status(enabled)} AutoQuestRenewer {'enabled' if enabled else 'disabled'}")
        print(f"\n           {Fore.YELLOW}Automatically renews unwanted quests during Daily Tasks.{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}Scans ;q embed for keywords and renews matching quests.{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}Uses renewal scrolls (stops when 0 scrolls left).{Style.RESET_ALL}")
        
        print(f"\n           {Fore.YELLOW}═══ Settings ═══{Style.RESET_ALL}")
        print(f"           [1] {status(enabled)} AutoQuestRenewer on/off")
        
        print(f"\n           {Fore.YELLOW}═══ Quest Categories to Renew ═══{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}Enable = quest gets RENEWED (replaced){Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}Disable = quest is KEPT{Style.RESET_ALL}")
        print(f"           {'─' * 50}")
        print(f"           [2] {status(aqr.get('battle_quests', True))} Battle Quests (Defeat, Battle, Battles)")
        print(f"           [3] {status(aqr.get('fish_quests', True))} Fish Quests (Pokemon from Fishing, Fish)")
        print(f"           [4] {status(aqr.get('receive_quests', True))} Receive from Player (from another player)")
        print(f"           [5] {status(aqr.get('catch_quests', True))} Catch Quests (Encounter, Catch)")
        
        print(f"\n           [0] Back")
        
        print(f"\n{Fore.CYAN}╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    def handle_quest_renewer_config(self):
        """Handler for AutoQuestRenewer configuration (foldable sub-menu)"""
        category_keys = {
            '2': 'battle_quests',
            '3': 'fish_quests',
            '4': 'receive_quests',
            '5': 'catch_quests',
        }
        category_names = {
            'battle_quests': 'Battle Quests',
            'fish_quests': 'Fish Quests',
            'receive_quests': 'Receive from Player Quests',
            'catch_quests': 'Catch Quests',
        }
        
        while True:
            self.show_quest_renewer_menu()
            choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            aqr = self.config.get('auto_quest_renewer', {})
            
            if choice == '1':
                aqr['enabled'] = not aqr.get('enabled', False)
                self.config['auto_quest_renewer'] = aqr
                state = "enabled" if aqr['enabled'] else "disabled"
                print(f"           {Fore.GREEN}AutoQuestRenewer {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice in category_keys:
                key = category_keys[choice]
                name = category_names[key]
                aqr[key] = not aqr.get(key, True)
                self.config['auto_quest_renewer'] = aqr
                state = "enabled (will be RENEWED)" if aqr[key] else "disabled (will be KEPT)"
                print(f"           {Fore.GREEN}{name}: {state}{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice == '0':
                self.save_config()
                break

            self.save_config()

    # ──────────────────────────────────────────────────────────
    # Quest Settings (parent menu) + AutoQuestClaimer sub-menu
    # ──────────────────────────────────────────────────────────
    def show_quest_settings_menu(self):
        """Parent menu: container for Renewer + Claimer sub-menus."""
        self.print_header()

        aqr = self.config.get('auto_quest_renewer', {})
        aqc = self.config.get('auto_quest_claim', {})

        def status(on):
            return f"{Fore.GREEN}✓{Style.RESET_ALL}" if on else f"{Fore.RED}✗{Style.RESET_ALL}"

        print(f"\n{Fore.CYAN}╔════════════════════ QUEST SETTINGS ══════════════════════╗{Style.RESET_ALL}")
        print(f"\n           {Fore.YELLOW}Configure quest-related automation features.{Style.RESET_ALL}")

        print(f"\n           {Fore.YELLOW}═══ Features ═══{Style.RESET_ALL}")
        print(f"           [1] {status(aqr.get('enabled', False))} AutoQuestRenewer Settings ->")
        print(f"               {Fore.YELLOW}Rerolls unwanted quests during Daily Tasks.{Style.RESET_ALL}")
        print(f"           [2] {status(aqc.get('enabled', False))} AutoQuestClaimer Settings ->")
        iv = max(120, int(aqc.get('interval_minutes', 130) or 130))
        ps = max(20, int(aqc.get('pause_seconds', 20) or 20))
        print(f"               {Fore.YELLOW}Every {iv}m sends ;q, then uses Renewer logic.{Style.RESET_ALL}")
        print(f"               {Fore.YELLOW}Pause: {ps}s  |  Interval: {iv}m  (min 120m / 20s){Style.RESET_ALL}")

        print(f"\n           [0] Back")
        print(f"\n{Fore.CYAN}╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")

    def handle_quest_settings_menu(self):
        """Top-level Quest Settings handler."""
        while True:
            self.show_quest_settings_menu()
            choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}").strip()

            if choice == '1':
                self.handle_quest_renewer_config()
            elif choice == '2':
                self.handle_quest_claim_config()
            elif choice == '0':
                self.save_config()
                break

    def show_quest_claim_menu(self):
        """AutoQuestClaimer configuration menu."""
        self.print_header()

        aqc = self.config.get('auto_quest_claim', {})
        enabled = aqc.get('enabled', False)
        interval_min = max(120, int(aqc.get('interval_minutes', 130) or 130))
        pause_sec = max(20, int(aqc.get('pause_seconds', 20) or 20))

        def status(on):
            return f"{Fore.GREEN}✓{Style.RESET_ALL}" if on else f"{Fore.RED}✗{Style.RESET_ALL}"

        print(f"\n{Fore.CYAN}╔═══════════════════ AUTOQUEST CLAIMER ════════════════════╗{Style.RESET_ALL}")
        print(f"\n           {status(enabled)} AutoQuestClaimer {'enabled' if enabled else 'disabled'}")
        print(f"\n           {Fore.YELLOW}Every N minutes (min 120m / 2h), the bot pauses the main{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}loop for a short break, sends ;q to refresh the quest slot,{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}then runs AutoQuestRenewer logic to reroll unwanted quests.{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}Keyword categories are shared with AutoQuestRenewer.{Style.RESET_ALL}")

        print(f"\n           {Fore.YELLOW}═══ Settings ═══{Style.RESET_ALL}")
        print(f"           [1] {status(enabled)} AutoQuestClaimer on/off")
        print(f"           [2] Interval:        {Fore.GREEN}{interval_min}m{Style.RESET_ALL}  (min 120m)")
        print(f"           [3] Pause duration:  {Fore.GREEN}{pause_sec}s{Style.RESET_ALL}  (min 20s)")

        print(f"\n           {Fore.YELLOW}═══ Renewal Keywords ═══{Style.RESET_ALL}")
        print(f"           Configured under AutoQuestRenewer sub-menu (shared).")

        print(f"\n           [0] Back")
        print(f"\n{Fore.CYAN}╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")

    def handle_quest_claim_config(self):
        """Handler for AutoQuestClaimer configuration."""
        while True:
            self.show_quest_claim_menu()
            choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}").strip()

            aqc = self.config.get('auto_quest_claim', {})

            if choice == '1':
                aqc['enabled'] = not aqc.get('enabled', False)
                self.config['auto_quest_claim'] = aqc
                # Reset timer anchor so toggling on does not cause an immediate run
                self._last_quest_claim_ts = None
                state = "enabled" if aqc['enabled'] else "disabled"
                print(f"           {Fore.GREEN}AutoQuestClaimer {state}!{Style.RESET_ALL}")
                time_module.sleep(1)

            elif choice == '2':
                current = max(120, int(aqc.get('interval_minutes', 130) or 130))
                print(f"\n           {Fore.CYAN}Interval in minutes (min 120 = 2h){Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {current}m{Style.RESET_ALL}")
                raw = input(f"           {Fore.CYAN}New interval [min]: {Style.RESET_ALL}").strip()
                if raw.isdigit():
                    val = int(raw)
                    if val < 120:
                        print(f"           {Fore.RED}Minimum is 120 minutes. Value clamped.{Style.RESET_ALL}")
                        val = 120
                    aqc['interval_minutes'] = val
                    self.config['auto_quest_claim'] = aqc
                    self._last_quest_claim_ts = None
                    print(f"           {Fore.GREEN}Interval set to {val}m.{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.RED}Not a number — keeping {current}m.{Style.RESET_ALL}")
                time_module.sleep(1.5)

            elif choice == '3':
                current = max(20, int(aqc.get('pause_seconds', 20) or 20))
                print(f"\n           {Fore.CYAN}Pause duration in seconds (min 20){Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {current}s{Style.RESET_ALL}")
                raw = input(f"           {Fore.CYAN}New pause [sec]: {Style.RESET_ALL}").strip()
                if raw.isdigit():
                    val = int(raw)
                    if val < 20:
                        print(f"           {Fore.RED}Minimum is 20 seconds. Value clamped.{Style.RESET_ALL}")
                        val = 20
                    aqc['pause_seconds'] = val
                    self.config['auto_quest_claim'] = aqc
                    print(f"           {Fore.GREEN}Pause set to {val}s.{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.RED}Not a number — keeping {current}s.{Style.RESET_ALL}")
                time_module.sleep(1.5)

            elif choice == '0':
                self.save_config()
                break

            self.save_config()

    def _get_quest_renew_keywords(self):
        """Returns a dict mapping quest numbers to keywords based on config."""
        aqr = self.config.get('auto_quest_renewer', {})
        keywords = []
        if aqr.get('battle_quests', True):
            keywords.extend(['defeat', 'battle', 'battles'])
        if aqr.get('fish_quests', True):
            keywords.extend(['pokemon from fishing', 'fish'])
        if aqr.get('receive_quests', True):
            keywords.extend(['from another player', 'receive'])
        if aqr.get('catch_quests', True):
            keywords.extend(['encounter', 'catch'])
        return keywords
    
    def _parse_quests_from_embed(self, embed_text):
        """Parse quest embed text and return list of (quest_number, quest_text) tuples.
        Only parses actual quest headers like 'Quest #1:', 'Quest #2:' from PokeMeow embeds."""
        quests = []
        lines = embed_text.split('\n')
        
        # Primary: Match explicit "Quest #N:" headers (PokeMeow format)
        # Handles plain "Quest #1:", bold "**Quest #1**:", and other markdown variants
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            # Strip all markdown formatting (**, __, *, _) before matching
            clean_line = re.sub(r'[*_~`]', '', line_stripped)
            quest_header = re.match(r'quest\s*#?(\d+)\s*[:\.]', clean_line, re.IGNORECASE)
            if quest_header:
                quest_num = int(quest_header.group(1))
                quest_desc = line_stripped
                if i + 1 < len(lines) and lines[i + 1].strip():
                    quest_desc += " " + lines[i + 1].strip()
                quests.append((quest_num, quest_desc))
        
        # Fallback: Look for "1.", "2.", "#1", "#2" at start of line
        if not quests:
            found_nums = set()
            for line in lines:
                line_stripped = line.strip()
                for num in [1, 2, 3]:
                    if num in found_nums:
                        continue
                    patterns = [f"{num}.", f"{num})", f"#{num}"]
                    for pat in patterns:
                        if line_stripped.lower().startswith(pat):
                            quests.append((num, line_stripped))
                            found_nums.add(num)
                            break
        
        # Last resort: parse quest-like content but skip reward/progress lines
        if not quests:
            quest_num = 0
            for line in lines:
                line_stripped = line.strip()
                if not line_stripped:
                    continue
                skip_indicators = ['reward', 'progress', 'out of', 'next quest', 'support',
                                   'patreon', 'extra quest', 'shorter quest', 'timer']
                if any(skip in line_stripped.lower() for skip in skip_indicators):
                    continue
                quest_indicators = ['defeat', 'catch', 'battle', 'fish', 'encounter',
                                   'pokemon from', 'from another', 'earn', 'hatch',
                                   'evolve', 'trade', 'complete', 'win', 'use']
                if any(ind in line_stripped.lower() for ind in quest_indicators):
                    quest_num += 1
                    if quest_num <= 3:
                        quests.append((quest_num, line_stripped))
        
        return quests
    
    async def _autoquestclaim_tick(self, channel):
        """One tick for AutoQuestClaim. If enabled and the configured interval
        has elapsed since the last run (or since bot main-loop start), performs:
          1) pause for configured seconds (blocks auto-catching)
          2) send ;q (PokeMeow gives a new quest slot every ~2h)
          3) run the existing renewer logic (force=True) to reroll unwanted quests

        Callers must ensure the bot is currently idle before invoking this."""
        aqc = self.config.get('auto_quest_claim', {})
        if not aqc.get('enabled', False):
            return

        # Enforce minimums: interval >= 120 min, pause >= 20 s
        interval_min = max(120, int(aqc.get('interval_minutes', 130) or 130))
        pause_sec = max(20, int(aqc.get('pause_seconds', 20) or 20))
        interval_sec = interval_min * 60

        now = asyncio.get_event_loop().time()

        # First time: anchor the timer to now (no immediate run on bot start)
        if self._last_quest_claim_ts is None:
            self._last_quest_claim_ts = now
            next_in = interval_min
            self.log(f"[AutoQuestClaim] Timer started. Next run in {next_in}m.")
            return

        if now - self._last_quest_claim_ts < interval_sec:
            return

        # Interval elapsed -- run now. doing_dailys blocks auto-catching
        # (on_message guard at the top of check_and_catch_pokemon).
        self.doing_dailys = True
        try:
            print(f"\n{Fore.CYAN}[AutoQuestClaim] Interval reached ({interval_min}m). "
                  f"Pausing main loop for {pause_sec}s...{Style.RESET_ALL}")
            self.log(f"[AutoQuestClaim] Interval elapsed; pausing {pause_sec}s before ;q")

            # Block-sleep the pause
            slept = 0.0
            while slept < pause_sec and self.running:
                await asyncio.sleep(min(1.0, pause_sec - slept))
                slept += 1.0

            if not self.running:
                return

            print(f"{Fore.CYAN}[AutoQuestClaim] Sending ;q to refresh quests...{Style.RESET_ALL}")
            self.log("[AutoQuestClaim] Sending ;q")
            await self.send_command(channel, ';q')

            # Reuse the existing renewer (force=True -> runs even if AQR toggle off).
            # Renewer uses the keyword categories under auto_quest_renewer to decide
            # which quests to reroll; if all categories are disabled nothing is rerolled.
            await self.process_quest_renew(channel, force=True)

            self._last_quest_claim_ts = asyncio.get_event_loop().time()
            print(f"{Fore.GREEN}[AutoQuestClaim] Cycle complete. Next run in {interval_min}m.{Style.RESET_ALL}")
            self.log(f"[AutoQuestClaim] Cycle complete; next in {interval_min}m")
        except Exception as e:
            self.log(f"[AutoQuestClaim] Error: {str(e)}")
            print(f"{Fore.RED}[AutoQuestClaim] Error: {str(e)}{Style.RESET_ALL}")
        finally:
            self.doing_dailys = False

    async def process_quest_renew(self, channel, force=False):
        """Process quest renewal after ;q has been sent.
        Scans the response embed for keywords and renews matching quests.

        force=True bypasses the aqr.enabled gate (used by AutoQuestClaim so it
        can reuse the renewal logic without requiring the AutoQuestRenewer
        toggle to be on)."""
        aqr = self.config.get('auto_quest_renewer', {})
        if not force and not aqr.get('enabled', False):
            return
        
        keywords = self._get_quest_renew_keywords()
        if not keywords:
            self.log("AutoQuestRenewer: No keyword categories enabled, skipping.")
            return
        
        print(f"\n{Fore.CYAN}[AutoQuestRenewer] Scanning quests...{Style.RESET_ALL}")
        self.log("AutoQuestRenewer: Scanning quests...")
        
        # First scan uses the ;q already sent by daily tasks
        self._quest_renew_event = asyncio.Event()
        self._quest_renew_embed_text = ""
        self._quest_renew_raw_text = ""
        
        # Wait up to 8 seconds for the quest embed
        try:
            await asyncio.wait_for(self._quest_renew_event.wait(), timeout=8)
        except asyncio.TimeoutError:
            self.log("AutoQuestRenewer: No quest embed received within 8s, skipping.")
            print(f"{Fore.YELLOW}[AutoQuestRenewer] No quest response received, skipping.{Style.RESET_ALL}")
            self._quest_renew_event = None
            self._quest_renew_scrolls = None
            return
        
        embed_text = self._quest_renew_embed_text
        self._quest_renew_event = None
        
        if not embed_text:
            self.log("AutoQuestRenewer: Empty quest embed, skipping.")
            self._quest_renew_scrolls = None
            return
        
        # Main loop: parse quests, renew matches, keep rerolling same quest until desired
        # Track which quest slots have been successfully renewed to a good quest
        renewed_slots = set()
        stop_renewing = False
        
        while True:
            # Parse quests from current embed text
            quests = self._parse_quests_from_embed(embed_text)
            
            if not quests:
                self.log("AutoQuestRenewer: Could not parse any quests from embed.")
                print(f"{Fore.YELLOW}[AutoQuestRenewer] No quests found in response.{Style.RESET_ALL}")
                break
            
            self.log(f"AutoQuestRenewer: Found {len(quests)} quests: {quests}")
            
            # Check which quests match the keywords (excluding already renewed slots)
            quests_to_renew = []
            for quest_num, quest_text in quests:
                if quest_num in renewed_slots:
                    continue  # Skip already successfully renewed quests
                quest_lower = quest_text.lower()
                for keyword in keywords:
                    if keyword in quest_lower:
                        quests_to_renew.append((quest_num, quest_text, keyword))
                        break
            
            if not quests_to_renew:
                self.log("AutoQuestRenewer: No quests match renewal keywords.")
                print(f"{Fore.GREEN}[AutoQuestRenewer] All quests look good, no renewal needed!{Style.RESET_ALL}")
                break
            
            self.log(f"AutoQuestRenewer: {len(quests_to_renew)} quests to renew: {[(q[0], q[2]) for q in quests_to_renew]}")
            
            # Process ONE quest at a time, then re-check if it still needs renewal
            quest_num, quest_text, matched_keyword = quests_to_renew[0]
            
            if self._quest_renew_scrolls is not None and self._quest_renew_scrolls <= 0:
                self.log("AutoQuestRenewer: 0 scrolls left, stopping renewal.")
                print(f"{Fore.RED}[AutoQuestRenewer] No scrolls left! Stopping renewal.{Style.RESET_ALL}")
                stop_renewing = True
                break
            
            if not self.running or self.paused or self.captcha_active or self.temp_banned:
                self.log("AutoQuestRenewer: Bot paused/stopped, aborting renewal.")
                stop_renewing = True
                break
            
            print(f"{Fore.YELLOW}[AutoQuestRenewer] Renewing quest {quest_num} (matched: '{matched_keyword}'){Style.RESET_ALL}")
            self.log(f"AutoQuestRenewer: Renewing quest {quest_num} (keyword: '{matched_keyword}')")
            
            # Set up event to catch the renewal response (includes new quest embed)
            self._quest_renew_event = asyncio.Event()
            self._quest_renew_embed_text = ""
            self._quest_renew_raw_text = ""
            
            await asyncio.sleep(3)
            await self.send_command(channel, f";q r {quest_num}")
            
            try:
                await asyncio.wait_for(self._quest_renew_event.wait(), timeout=8)
            except asyncio.TimeoutError:
                self.log(f"AutoQuestRenewer: No response for ;q r {quest_num}, continuing...")
            
            renew_response = self._quest_renew_raw_text.lower()
            self._quest_renew_event = None
            
            # Check if no scrolls
            if "don't have any quest reset scroll" in renew_response:
                self._quest_renew_scrolls = 0
                self.log("AutoQuestRenewer: No quest reset scrolls available! Stopping.")
                print(f"{Fore.RED}[AutoQuestRenewer] No quest reset scrolls! Stopping renewal.{Style.RESET_ALL}")
                stop_renewing = True
                break
            
            scroll_match = re.search(r'you now have (\d+) scrolls? left', renew_response)
            if scroll_match:
                scrolls_left = int(scroll_match.group(1))
                self._quest_renew_scrolls = scrolls_left
                self.log(f"AutoQuestRenewer: {scrolls_left} scrolls remaining.")
                print(f"{Fore.CYAN}[AutoQuestRenewer] Scrolls remaining: {scrolls_left}{Style.RESET_ALL}")
                
                if scrolls_left <= 0:
                    self.log("AutoQuestRenewer: 0 scrolls left, stopping.")
                    print(f"{Fore.RED}[AutoQuestRenewer] No more scrolls! Stopping renewal.{Style.RESET_ALL}")
                    stop_renewing = True
                    break
            
            # Use the embed from the ;q r response to check the NEW quest
            embed_text = self._quest_renew_embed_text
            
            # Check if the new quest for this slot still matches unwanted keywords
            new_quests = self._parse_quests_from_embed(embed_text)
            new_quest_text = ""
            for nq_num, nq_text in new_quests:
                if nq_num == quest_num:
                    new_quest_text = nq_text.lower()
                    break
            
            still_unwanted = False
            for keyword in keywords:
                if keyword in new_quest_text:
                    still_unwanted = True
                    print(f"{Fore.YELLOW}[AutoQuestRenewer] Quest {quest_num} still unwanted ('{keyword}'), rerolling again...{Style.RESET_ALL}")
                    self.log(f"AutoQuestRenewer: Quest {quest_num} still matches '{keyword}', will reroll again")
                    break
            
            if not still_unwanted:
                # Quest is now good! Mark this slot as done
                renewed_slots.add(quest_num)
                print(f"{Fore.GREEN}[AutoQuestRenewer] Quest {quest_num} is now a desired quest!{Style.RESET_ALL}")
                self.log(f"AutoQuestRenewer: Quest {quest_num} successfully renewed to desired quest")
            
            # Cooldown between renew commands
            print(f"{Fore.CYAN}[AutoQuestRenewer] Cooldown 6s...{Style.RESET_ALL}")
            await asyncio.sleep(6)
            
            # Loop continues to re-check all quests (will skip renewed_slots)
        
        self._quest_renew_scrolls = None
        print(f"{Fore.GREEN}[AutoQuestRenewer] Quest renewal complete!{Style.RESET_ALL}")
        self.log("AutoQuestRenewer: Renewal process finished.")
    
    async def _handle_quest_response(self, message):
        """Called from on_message to capture quest/renew responses for AutoQuestRenewer."""
        if self._quest_renew_event is None or self._quest_renew_event.is_set():
            return
        
        # Collect all text from embeds and content
        all_text = ""
        embed_text = ""
        
        if message.embeds:
            for embed in message.embeds:
                embed_dict = embed.to_dict()
                if 'title' in embed_dict:
                    embed_text += str(embed_dict['title']) + "\n"
                if 'description' in embed_dict:
                    embed_text += str(embed_dict['description']) + "\n"
                if 'fields' in embed_dict:
                    for field in embed_dict['fields']:
                        if 'name' in field:
                            embed_text += str(field['name']) + "\n"
                        if 'value' in field:
                            embed_text += str(field['value']) + "\n"
                if 'footer' in embed_dict and 'text' in embed_dict['footer']:
                    embed_text += str(embed_dict['footer']['text']) + "\n"
        
        if message.content:
            all_text = message.content + "\n" + embed_text
        else:
            all_text = embed_text
        
        # Check if this looks like a quest-related response
        quest_indicators = ['quest', 'daily', 'task', 'defeat', 'catch', 'battle',
                           'fish', 'encounter', 'scroll', 'renew', 'pokemon from',
                           'from another', 'earn', 'hatch', 'evolve',
                           "don't have any quest reset scroll"]
        all_lower = all_text.lower()
        
        if any(ind in all_lower for ind in quest_indicators):
            self._quest_renew_embed_text = embed_text
            self._quest_renew_raw_text = all_text
            self._quest_renew_event.set()
    
