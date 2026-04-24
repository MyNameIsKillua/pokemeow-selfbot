"""Autobuyer feature: ball stock checking and autobuyer config menus."""
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


class AutoBuyerMixin:
    async def check_ball_stock(self, message):
        """Prüft Ball-Bestände nach einem Catch und kauft nach wenn nötig.
        Wird nur aktiv wenn 'you caught' oder 'broke out of the' im Text steht."""
        if self.buying_balls:
            return
        
        autobuyer = self.config.get('autobuyer', {})
        if not autobuyer.get('enabled', False):
            return
        
        # Sammle ALLEN Text aus der Nachricht (Embeds + Content)
        all_text = ""
        if message.embeds:
            for embed in message.embeds:
                embed_dict = embed.to_dict()
                for key in ['title', 'description', 'footer']:
                    if key in embed_dict:
                        val = embed_dict[key]
                        if isinstance(val, dict):
                            all_text += str(val.get('text', '')) + " "
                        else:
                            all_text += str(val) + " "
                if 'fields' in embed_dict:
                    for field in embed_dict['fields']:
                        all_text += str(field.get('name', '')) + " "
                        all_text += str(field.get('value', '')) + " "
        if message.content:
            all_text += message.content
        
        # Normalisierung: lowercase + Markdown/Sonderzeichen entfernen
        all_text = all_text.lower()
        all_text = all_text.replace('*', '').replace('_', '').replace('═', '').replace('—', '').replace('─', '')
        
        # NUR scannen wenn es eine Catch-Bestätigung ist
        is_catch_result = 'you caught' in all_text or 'broke out of the' in all_text
        if not is_catch_result:
            return
        
        self.log(f"[AUTOBUYER] Checking inventory after catch result...")
        
        # Ball-Bestände parsen (supports comma-separated numbers like "2,045")
        ball_stock = {}
        patterns = {
            'pb': r'pokeballs[:\s]+([\d,]+)',
            'gb': r'greatballs[:\s]+([\d,]+)',
            'ub': r'ultraballs[:\s]+([\d,]+)',
            'mb': r'masterballs[:\s]+([\d,]+)'
        }
        
        for ball_type, pattern in patterns.items():
            match = re.search(pattern, all_text)
            if match:
                # Remove commas from number string before converting to int
                ball_stock[ball_type] = int(match.group(1).replace(',', ''))
        
        if not ball_stock:
            return
        
        # Prüfe ob etwas gekauft werden muss
        ball_names = {'pb': 'Pokeball', 'gb': 'Greatball', 'ub': 'Ultraball', 'mb': 'Masterball'}
        buy_queue = []
        
        for ball_type in ['pb', 'gb', 'ub', 'mb']:
            if ball_type not in ball_stock:
                continue
            
            settings = autobuyer.get(ball_type, {})
            threshold = settings.get('threshold', 10)
            amount = settings.get('amount', 0)
            
            if amount <= 0:
                continue
            
            current = ball_stock[ball_type]
            if current <= threshold:
                buy_queue.append((ball_type, current, threshold, amount))
        
        if not buy_queue:
            return
        
        # Kaufen!
        self.buying_balls = True
        try:
            channel = message.channel
            
            for ball_type, current, threshold, amount in buy_queue:
                ball_name = ball_names.get(ball_type, ball_type)
                self.log(f"AutoBuyer: {ball_name} at {current} (Threshold: <={threshold}) -> Buying {amount}x")
                print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] AutoBuyer: {ball_name} only {current}x left! Buying {amount}x...{Style.RESET_ALL}")
                
                await asyncio.sleep(3)
                
                if not self.running or self.paused or self.captcha_active or self.temp_banned:
                    self.log("AutoBuyer: Cancelled (Bot paused/stopped)")
                    break
                
                command = f";shop buy {ball_type} {amount}"
                await self.send_command(channel, command)
                self.log(f"AutoBuyer: {command} sent")
                print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] AutoBuyer: {ball_name} x{amount} purchased!{Style.RESET_ALL}")
                
                await asyncio.sleep(3)
            
            # Nach dem Kauf 5 Sekunden warten bevor wieder ;p gesendet wird
            self.log("AutoBuyer: Waiting 5s before resuming ;p...")
            print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] AutoBuyer: Waiting 5s before continuing to catch...{Style.RESET_ALL}")
            await asyncio.sleep(5)
            
        except Exception as e:
            self.log(f"AutoBuyer Error: {str(e)}")
            print(f"{Fore.RED}AutoBuyer Error: {str(e)}{Style.RESET_ALL}")
        finally:
            self.buying_balls = False
    
    # ═════════════════════════════════════════════════════════════════
    #  AUTO-RELEASE SYSTEM
    # ═════════════════════════════════════════════════════════════════
    
    def show_autobuyer_menu(self):
        """Zeigt das AutoBuyer Konfigurations-Menü (eigenes Fenster)"""
        self.print_header()
        
        autobuyer = self.config.get('autobuyer', {})
        enabled = autobuyer.get('enabled', False)
        
        def status(on):
            return f"{Fore.GREEN}✓{Style.RESET_ALL}" if on else f"{Fore.RED}✗{Style.RESET_ALL}"
        
        print(f"\n{Fore.CYAN}╔═══════════════════ AUTOBUYER ═════════════════════════╗{Style.RESET_ALL}")
        print(f"\n           {status(enabled)} AutoBuyer {'enabled' if enabled else 'disabled'}")
        print(f"\n           {Fore.YELLOW}The AutoBuyer monitors your ball inventory after{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}every catch and buys automatically.{Style.RESET_ALL}")
        
        print(f"\n           {Fore.YELLOW}═══ Settings ═══{Style.RESET_ALL}")
        print(f"           [1] {status(enabled)} AutoBuyer on/off")
        
        pb = autobuyer.get('pb', {'threshold': 10, 'amount': 200})
        gb = autobuyer.get('gb', {'threshold': 10, 'amount': 100})
        ub = autobuyer.get('ub', {'threshold': 10, 'amount': 25})
        mb = autobuyer.get('mb', {'threshold': 1, 'amount': 1})
        
        print(f"\n           {Fore.YELLOW}═══ Ball Thresholds ═══{Style.RESET_ALL}")
        print(f"           {Fore.YELLOW}{'Ball':<14} {'Buy when ≤':<16} {'Amount':<12}{Style.RESET_ALL}")
        print(f"           {'─' * 42}")
        print(f"           [2] Pokeball     ≤ {pb.get('threshold', 10):<14} → {pb.get('amount', 200)}x buy")
        print(f"           [3] Greatball    ≤ {gb.get('threshold', 10):<14} → {gb.get('amount', 100)}x buy")
        print(f"           [4] Ultraball    ≤ {ub.get('threshold', 10):<14} → {ub.get('amount', 25)}x buy")
        print(f"           [5] Masterball   ≤ {mb.get('threshold', 1):<14} → {mb.get('amount', 1)}x buy")
        
        print(f"\n           [6] Restore Default Values")
        print(f"           [0] Back")
        
        print(f"\n{Fore.CYAN}╚════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
    
    def handle_autobuyer_config(self):
        """Handler für AutoBuyer Konfiguration (eigenes Fenster)"""
        ball_types = {'2': 'pb', '3': 'gb', '4': 'ub', '5': 'mb'}
        ball_names = {'pb': 'Pokeball', 'gb': 'Greatball', 'ub': 'Ultraball', 'mb': 'Masterball'}
        
        while True:
            self.show_autobuyer_menu()
            choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            autobuyer = self.config.get('autobuyer', {})
            
            if choice == '1':
                autobuyer['enabled'] = not autobuyer.get('enabled', False)
                self.config['autobuyer'] = autobuyer
                state = "enabled" if autobuyer['enabled'] else "disabled"
                print(f"           {Fore.GREEN}AutoBuyer {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice in ball_types:
                ball_type = ball_types[choice]
                ball_name = ball_names[ball_type]
                settings = autobuyer.get(ball_type, {})
                
                print(f"\n           {Fore.CYAN}═══ {ball_name} Settings ═══{Style.RESET_ALL}")
                print(f"           Current: Buy when ≤ {settings.get('threshold', 10)}, Amount: {settings.get('amount', 0)}")
                
                # Threshold
                threshold_input = input(f"           {Fore.CYAN}Buy when ≤ (number, Enter=keep): {Style.RESET_ALL}").strip()
                if threshold_input:
                    try:
                        threshold = int(threshold_input)
                        if threshold >= 0:
                            settings['threshold'] = threshold
                            print(f"           {Fore.GREEN}Threshold: ≤{threshold}{Style.RESET_ALL}")
                        else:
                            print(f"           {Fore.RED}Must be ≥ 0!{Style.RESET_ALL}")
                    except ValueError:
                        print(f"           {Fore.RED}Invalid number!{Style.RESET_ALL}")
                
                # Buy amount
                amount_input = input(f"           {Fore.CYAN}Buy amount (number, Enter=keep): {Style.RESET_ALL}").strip()
                if amount_input:
                    try:
                        amount = int(amount_input)
                        if amount >= 0:
                            settings['amount'] = amount
                            print(f"           {Fore.GREEN}Buy amount: {amount}x{Style.RESET_ALL}")
                        else:
                            print(f"           {Fore.RED}Must be ≥ 0!{Style.RESET_ALL}")
                    except ValueError:
                        print(f"           {Fore.RED}Invalid number!{Style.RESET_ALL}")
                
                autobuyer[ball_type] = settings
                self.config['autobuyer'] = autobuyer
                print(f"           {Fore.GREEN}{ball_name} saved!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice == '6':
                self.config['autobuyer'] = {
                    'enabled': autobuyer.get('enabled', False),
                    'pb': {'threshold': 10, 'amount': 200},
                    'gb': {'threshold': 10, 'amount': 100},
                    'ub': {'threshold': 10, 'amount': 25},
                    'mb': {'threshold': 1, 'amount': 1}
                }
                print(f"           {Fore.GREEN}Default values restored!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice == '0':
                self.save_config()
                break
            
            self.save_config()
    
