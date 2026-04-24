"""Rate-limit protection feature: monitoring Pokemeow response latency and pausing."""
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


class RateLimitMixin:
    def on_pokemeow_response(self):
        """Call this when PokeMeow responds to reset the no-response counter"""
        self._no_response_counter = 0
        self._last_pokemeow_response = datetime.now()
        if self._rate_limit_sleeping:
            self._rate_limit_sleeping = False
            self.log("⚡ Rate Limit: PokeMeow responded! Resuming normal operation.")
    
    def increment_no_response(self):
        """Call this when a command is sent. Increments the no-response counter."""
        self._no_response_counter += 1
        self.log(f"⚡ Rate Limit: No response counter = {self._no_response_counter}")
    
    async def check_rate_limit_protection(self):
        """Check if rate limit protection should trigger a sleep.
        Returns True if we should sleep (and handles the sleep), False otherwise."""
        rl_cfg = self.config.get('rate_limit_protection', {})
        if not rl_cfg.get('enabled', True):
            return False
        
        max_no_response = rl_cfg.get('max_no_response', 3)
        
        if self._no_response_counter >= max_no_response:
            sleep_min = rl_cfg.get('sleep_min', 30)
            sleep_max = rl_cfg.get('sleep_max', 90)
            sleep_time = random.randint(sleep_min, sleep_max)
            
            self._rate_limit_sleeping = True
            self.log(f"⚡ Rate Limit Protection: No response after {self._no_response_counter} commands!")
            self.log(f"⚡ Rate Limit Protection: Sleeping for {sleep_time}s to avoid spam detection...")
            print(f"\n{Fore.YELLOW}  ⚡  Rate Limit Protection: PokeMeow not responding!{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}  ⚡  Sleeping for {sleep_time}s to avoid spam detection...{Style.RESET_ALL}\n")
            
            # Sleep in small increments so we can still respond to stop commands
            slept = 0
            while slept < sleep_time and self.running:
                await asyncio.sleep(min(5, sleep_time - slept))
                slept += 5
                # Check if PokeMeow responded during sleep (e.g., delayed response)
                if not self._rate_limit_sleeping:
                    self.log("⚡ Rate Limit: PokeMeow responded during sleep, resuming early!")
                    print(f"{Fore.GREEN}  ⚡  PokeMeow responded! Resuming early...{Style.RESET_ALL}")
                    break
            
            self._rate_limit_sleeping = False
            self._no_response_counter = 0  # Reset counter after sleep
            self.log(f"⚡ Rate Limit Protection: Sleep ended, resuming...")
            print(f"{Fore.GREEN}  ⚡  Rate Limit sleep ended! Resuming...{Style.RESET_ALL}\n")
            return True
        
        return False
    
    def handle_rate_limit_config(self):
        """Handler for Rate Limit Protection configuration"""
        while True:
            self.clear_screen()
            rl = self.config.get('rate_limit_protection', {'enabled': True, 'max_no_response': 3, 'sleep_min': 30, 'sleep_max': 90})
            
            print(f"\n{Fore.CYAN}+=============================================+{Style.RESET_ALL}")
            print(f"{Fore.CYAN}|      Rate Limit Protection Settings         |{Style.RESET_ALL}")
            print(f"{Fore.CYAN}+=============================================+{Style.RESET_ALL}\n")
            
            st = f"{Fore.GREEN}ON{Style.RESET_ALL}" if rl.get('enabled', True) else f"{Fore.RED}OFF{Style.RESET_ALL}"
            
            print(f"           [1] Toggle Rate Limit Protection: {st}")
            print(f"           [2] Max Commands Without Response: {Fore.YELLOW}{rl.get('max_no_response', 3)}{Style.RESET_ALL}")
            print(f"           [3] Sleep Duration: {Fore.YELLOW}{rl.get('sleep_min', 30)}-{rl.get('sleep_max', 90)}s{Style.RESET_ALL}")
            print(f"\n           [0] Back")
            
            print(f"\n           {Fore.YELLOW}Info: If PokeMeow doesn't respond after {rl.get('max_no_response', 3)} commands,{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}the bot will sleep for {rl.get('sleep_min', 30)}-{rl.get('sleep_max', 90)}s to avoid spam detection.{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}This helps on public servers with rate limits.{Style.RESET_ALL}")
            
            choice = input(f"\n           {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            if choice == '1':
                rl['enabled'] = not rl.get('enabled', True)
                self.config['rate_limit_protection'] = rl
                self.save_config()
                status_str = "enabled" if rl['enabled'] else "disabled"
                print(f"           {Fore.GREEN}Rate Limit Protection {status_str}!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '2':
                print(f"\n           {Fore.CYAN}Max commands without response before sleeping:{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {rl.get('max_no_response', 3)} commands{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Range: 2-10 (lower = more cautious){Style.RESET_ALL}")
                try:
                    val = int(input(f"           {Fore.CYAN}> {Style.RESET_ALL}"))
                    if 2 <= val <= 10:
                        rl['max_no_response'] = val
                        self.config['rate_limit_protection'] = rl
                        self.save_config()
                        print(f"           {Fore.GREEN}Set to {val} commands!{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.RED}Invalid! Must be 2-10.{Style.RESET_ALL}")
                except ValueError:
                    print(f"           {Fore.RED}Invalid input! Enter a number.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '3':
                print(f"\n           {Fore.CYAN}Sleep duration range (seconds):{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {rl.get('sleep_min', 30)}-{rl.get('sleep_max', 90)}s{Style.RESET_ALL}")
                try:
                    sleep_min = int(input(f"           {Fore.CYAN}Min sleep (10-300): {Style.RESET_ALL}"))
                    if 10 <= sleep_min <= 300:
                        sleep_max = int(input(f"           {Fore.CYAN}Max sleep ({sleep_min}-600): {Style.RESET_ALL}"))
                        if sleep_min <= sleep_max <= 600:
                            rl['sleep_min'] = sleep_min
                            rl['sleep_max'] = sleep_max
                            self.config['rate_limit_protection'] = rl
                            self.save_config()
                            print(f"           {Fore.GREEN}Sleep duration set to {sleep_min}-{sleep_max}s!{Style.RESET_ALL}")
                        else:
                            print(f"           {Fore.RED}Invalid! Max must be {sleep_min}-600.{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.RED}Invalid! Min must be 10-300.{Style.RESET_ALL}")
                except ValueError:
                    print(f"           {Fore.RED}Invalid input! Enter a number.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '0':
                break
    
