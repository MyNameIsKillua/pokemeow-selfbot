"""Auto-release feature: automatic release of caught Pokemon based on rules."""
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


class AutoReleaseMixin:
    async def check_auto_release(self, message):
        """Prüft ob Auto-Release ausgeführt werden soll nach einem Catch.
        Nutzt den PokéMeow Command ';release duplicates' der alle doppelten
        Common-Pokemon released (behält Legendary & Shiny automatisch)."""
        if self.releasing:
            return
        
        auto_release = self.config.get('auto_release', {})
        if not auto_release.get('enabled', False):
            return
        
        # Nur nach einem erfolgreichen Catch zählen
        all_text = ""
        if message.embeds:
            for embed in message.embeds:
                embed_dict = embed.to_dict()
                if 'description' in embed_dict:
                    all_text += str(embed_dict['description']).lower() + " "
                if 'title' in embed_dict:
                    all_text += str(embed_dict['title']).lower() + " "
        if message.content:
            all_text += message.content.lower()
        
        if 'you caught' not in all_text:
            return
        
        # Catch-Counter erhöhen
        self.release_counter += 1
        interval = auto_release.get('interval', 50)
        
        if self.release_counter < interval:
            return
        
        # Release ausführen!
        self.releasing = True
        self.release_counter = 0
        
        try:
            channel = message.channel
            
            self.log(f"♻️ Auto-Release: {interval} catches reached, starting ;release duplicates")
            print(f"\n{Fore.MAGENTA}[{datetime.now().strftime('%H:%M:%S')}] ♻️ Auto-Release: Starting duplicate release...{Style.RESET_ALL}")
            
            # Kurz warten damit es nicht mit anderen Commands kollidiert
            await asyncio.sleep(4)
            
            if not self.running or self.paused or self.captcha_active or self.temp_banned:
                self.log("♻️ Auto-Release: Cancelled (Bot paused/stopped)")
                return
            
            # ;release duplicates entfernt alle doppelten Pokemon
            # Behält automatisch Legendary und Shiny!
            await self.send_command(channel, ';release duplicates')
            self.log("♻️ Auto-Release: ;release duplicates sent")
            
            # Warte auf Bestätigung von PokéMeow
            released = await self.wait_for_message(channel, 'released', timeout=15)
            
            if released:
                self.log("♻️ Auto-Release: Duplicates successfully released!")
                print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ♻️ Duplicates released! (Legendary & Shiny kept){Style.RESET_ALL}")
            else:
                # Auch wenn keine Bestätigung kam, ist es ok (evtl. keine Duplikate vorhanden)
                self.log("♻️ Auto-Release: No confirmation received (possibly no duplicates)")
                print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ♻️ Release sent (no duplicates found?){Style.RESET_ALL}")
            
            # Cooldown nach Release bevor weiter gecatcht wird
            await asyncio.sleep(5)
            
        except Exception as e:
            self.log(f"♻️ Auto-Release Error: {str(e)}")
            print(f"{Fore.RED}Auto-Release Error: {str(e)}{Style.RESET_ALL}")
        finally:
            self.releasing = False
    
    # ═════════════════════════════════════════════════════════════════
    #  CONFIG / LOGGING
    # ═════════════════════════════════════════════════════════════════
    
