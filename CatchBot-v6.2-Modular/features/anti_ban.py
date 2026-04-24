"""Anti-ban feature: typing delays, pauses, night mode, idle detection."""
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


class AntiBanMixin:
    def show_anti_ban_menu(self):
        """Shows the Anti-Ban Options sub-menu"""
        self.print_header()
        
        def status(on):
            return f"{Fore.GREEN}[ON]{Style.RESET_ALL}" if on else f"{Fore.RED}[OFF]{Style.RESET_ALL}"
        
        ab = self.config.get('anti_ban', {})
        
        def fmt_time(minutes):
            if minutes >= 60:
                h = minutes // 60
                m = minutes % 60
                return f"{h}h {m}m" if m else f"{h}h"
            return f"{minutes}m"
        
        print(f"\n{Fore.CYAN}{'=' * 22} ANTI-BAN OPTIONS {'=' * 22}{Style.RESET_ALL}")
        print(f"\n           {Fore.YELLOW}Make the bot behave more like a human player.{Style.RESET_ALL}")
        
        # --- Random Pauses ---
        int_min = ab.get('pause_interval_min', 60)
        int_max = ab.get('pause_interval_max', 180)
        dur_min = ab.get('pause_duration_min', 10)
        dur_max = ab.get('pause_duration_max', 30)
        print(f"\n           {Fore.YELLOW}--- Random Pauses ---{Style.RESET_ALL}")
        print(f"           [1] {status(ab.get('enabled', False))} Enable Random Pauses")
        print(f"           [2] Pause Interval: {fmt_time(int_min)} - {fmt_time(int_max)}")
        print(f"           [3] Pause Duration: {fmt_time(dur_min)} - {fmt_time(dur_max)}")
        
        # --- Catch Reaction Delay ---
        cr_min = ab.get('catch_reaction_min', 1)
        cr_max = ab.get('catch_reaction_max', 3)
        print(f"\n           {Fore.YELLOW}--- Catch Reaction Delay (always active) ---{Style.RESET_ALL}")
        print(f"           [4] Reaction Delay: {cr_min}s - {cr_max}s (before clicking ball)")
        
        # --- Pokemon Spawn Delay ---
        sd_min = ab.get('spawn_delay_min', 11)
        sd_max = ab.get('spawn_delay_max', 15)
        print(f"\n           {Fore.YELLOW}--- Pokemon Spawn Delay ---{Style.RESET_ALL}")
        print(f"           [S] Spawn Delay Range: {sd_min}s - {sd_max}s (time between ;p)")
        
        # --- Spawn Command ---
        sc_mode = ab.get('spawn_command', 'p_only')
        sc_p_chance = ab.get('spawn_p_chance', 50)
        if sc_mode == 'p_only':
            sc_label = ';p only'
        elif sc_mode == 'find_only':
            sc_label = ';find only'
        else:
            sc_label = f"Both random ({sc_p_chance}% ;p / {100 - sc_p_chance}% ;find)"
        print(f"\n           {Fore.YELLOW}--- Spawn Command ---{Style.RESET_ALL}")
        print(f"           [W] Spawn Command: {Fore.CYAN}{sc_label}{Style.RESET_ALL}")
        
        # --- Skip Spawn ---
        print(f"\n           {Fore.YELLOW}--- Random Spawn Skip ---{Style.RESET_ALL}")
        print(f"           [5] {status(ab.get('skip_spawn_enabled', False))} Random Spawn Skip")
        print(f"           [6] Skip Chance: {ab.get('skip_spawn_chance', 3)}%")
        
        # --- Idle Moments ---
        idle_dmin = ab.get('idle_duration_min', 30)
        idle_dmax = ab.get('idle_duration_max', 60)
        print(f"\n           {Fore.YELLOW}--- Random Idle Moments ---{Style.RESET_ALL}")
        print(f"           [7] {status(ab.get('idle_moments_enabled', False))} Random Idle Moments")
        print(f"           [8] Idle Chance: {ab.get('idle_chance', 5)}% (per catch cycle)")
        print(f"           [9] Idle Duration: {idle_dmin}s - {idle_dmax}s")
        
        # --- Typing Simulation ---
        td_min = ab.get('typing_delay_min', 300)
        td_max = ab.get('typing_delay_max', 800)
        print(f"\n           {Fore.YELLOW}--- Typing Simulation ---{Style.RESET_ALL}")
        print(f"           [T] {status(ab.get('typing_simulation_enabled', False))} Typing Simulation")
        print(f"           [D] Typing Delay: {td_min}ms - {td_max}ms (per character)")
        
        # --- Night Mode ---
        nm_start = ab.get('night_mode_start', 23)
        nm_end = ab.get('night_mode_end', 7)
        print(f"\n           {Fore.YELLOW}--- Night Mode ---{Style.RESET_ALL}")
        print(f"           [N] {status(ab.get('night_mode_enabled', False))} Night Mode (Auto-Sleep)")
        print(f"           [H] Sleep Hours: {nm_start:02d}:00 - {nm_end:02d}:00 (bot pauses)")
        
        print(f"\n           [R] Reset ALL Anti-Ban to Defaults")
        print(f"           [0] Back")
        print(f"\n{Fore.CYAN}{'=' * 62}{Style.RESET_ALL}\n")
    
    def _ab_input_int(self, prompt, current, min_val, max_val):
        """Helper for anti-ban integer input with validation"""
        val = input(f"           {Fore.CYAN}{prompt}: {Style.RESET_ALL}").strip()
        try:
            v = int(val)
            if min_val <= v <= max_val:
                return v
            else:
                print(f"           {Fore.RED}Invalid! Must be between {min_val} and {max_val}.{Style.RESET_ALL}")
                return None
        except ValueError:
            print(f"           {Fore.RED}Invalid input! Enter a number.{Style.RESET_ALL}")
            return None
    
    def handle_anti_ban_config(self):
        """Handler for Anti-Ban configuration sub-menu"""
        while True:
            self.show_anti_ban_menu()
            choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            ab = self.config.get('anti_ban', {})
            
            # --- [1] Toggle Random Pauses ---
            if choice == '1':
                ab['enabled'] = not ab.get('enabled', False)
                self.config['anti_ban'] = ab
                state = "enabled" if ab['enabled'] else "disabled"
                print(f"           {Fore.GREEN}Random Pauses {state}!{Style.RESET_ALL}")
                if ab['enabled']:
                    self.schedule_next_anti_ban_pause()
                    print(f"           {Fore.YELLOW}Next pause will be scheduled when bot starts.{Style.RESET_ALL}")
                else:
                    self.anti_ban_paused = False
                    self.anti_ban_next_pause = None
                time_module.sleep(1)
            
            # --- [2] Pause Interval (min & max) ---
            elif choice == '2':
                print(f"\n           {Fore.CYAN}Pause Interval — time between random pauses{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('pause_interval_min', 60)} - {ab.get('pause_interval_max', 180)} min{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Range: 30 - 600 min (10h){Style.RESET_ALL}")
                v_min = self._ab_input_int(f"Min Interval in minutes (30-600)", ab.get('pause_interval_min', 60), 30, 600)
                if v_min is not None:
                    v_max_input = self._ab_input_int(f"Max Interval in minutes ({v_min}-600)", ab.get('pause_interval_max', 180), v_min, 600)
                    if v_max_input is not None:
                        ab['pause_interval_min'] = v_min
                        ab['pause_interval_max'] = v_max_input
                        self.config['anti_ban'] = ab
                        print(f"           {Fore.GREEN}Pause Interval set to {v_min} - {v_max_input} min!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [3] Pause Duration (min & max) ---
            elif choice == '3':
                print(f"\n           {Fore.CYAN}Pause Duration — how long each pause lasts{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('pause_duration_min', 10)} - {ab.get('pause_duration_max', 30)} min{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Range: 5 - 1200 min (20h){Style.RESET_ALL}")
                v_min = self._ab_input_int(f"Min Duration in minutes (5-1200)", ab.get('pause_duration_min', 10), 5, 1200)
                if v_min is not None:
                    v_max_input = self._ab_input_int(f"Max Duration in minutes ({v_min}-1200)", ab.get('pause_duration_max', 30), v_min, 1200)
                    if v_max_input is not None:
                        ab['pause_duration_min'] = v_min
                        ab['pause_duration_max'] = v_max_input
                        self.config['anti_ban'] = ab
                        print(f"           {Fore.GREEN}Pause Duration set to {v_min} - {v_max_input} min!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [4] Catch Reaction Delay ---
            elif choice == '4':
                print(f"\n           {Fore.CYAN}Catch Reaction Delay — time before clicking the ball{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('catch_reaction_min', 1)}s - {ab.get('catch_reaction_max', 3)}s{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Range: 1 - 8 seconds (always active){Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Simulates a human looking at the spawn before clicking.{Style.RESET_ALL}")
                v_min = self._ab_input_int(f"Min Reaction in seconds (1-8)", ab.get('catch_reaction_min', 1), 1, 8)
                if v_min is not None:
                    v_max_input = self._ab_input_int(f"Max Reaction in seconds ({v_min}-8)", ab.get('catch_reaction_max', 3), v_min, 8)
                    if v_max_input is not None:
                        ab['catch_reaction_min'] = v_min
                        ab['catch_reaction_max'] = v_max_input
                        self.config['anti_ban'] = ab
                        print(f"           {Fore.GREEN}Catch Reaction set to {v_min}s - {v_max_input}s!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [S] Pokemon Spawn Delay ---
            elif choice.lower() == 's':
                print(f"\n           {Fore.CYAN}Pokemon Spawn Delay — seconds between each ;p command{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('spawn_delay_min', 11)}s - {ab.get('spawn_delay_max', 15)}s{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Range: 11 - 60 seconds{Style.RESET_ALL}")
                v_min = self._ab_input_int(f"Min Delay in seconds (11-60)", ab.get('spawn_delay_min', 11), 11, 60)
                if v_min is not None:
                    v_max_input = self._ab_input_int(f"Max Delay in seconds ({v_min}-60)", ab.get('spawn_delay_max', 15), v_min, 60)
                    if v_max_input is not None:
                        ab['spawn_delay_min'] = v_min
                        ab['spawn_delay_max'] = v_max_input
                        self.config['anti_ban'] = ab
                        print(f"           {Fore.GREEN}Pokemon Spawn Delay set to {v_min}s - {v_max_input}s!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [W] Spawn Command ---
            elif choice.lower() == 'w':
                print(f"\n           {Fore.CYAN}Spawn Command — which command to use for spawning{Style.RESET_ALL}")
                sc_mode = ab.get('spawn_command', 'p_only')
                print(f"           {Fore.YELLOW}Current: {sc_mode}{Style.RESET_ALL}")
                print(f"\n           [1] ;p only")
                print(f"           [2] ;find only")
                print(f"           [3] Both random (set % for ;p vs ;find)")
                sc_choice = input(f"\n           {Fore.CYAN}Choose: {Style.RESET_ALL}").strip()
                if sc_choice == '1':
                    ab['spawn_command'] = 'p_only'
                    self.config['anti_ban'] = ab
                    self.save_config()
                    print(f"           {Fore.GREEN}Spawn command set to ;p only!{Style.RESET_ALL}")
                elif sc_choice == '2':
                    ab['spawn_command'] = 'find_only'
                    self.config['anti_ban'] = ab
                    self.save_config()
                    print(f"           {Fore.GREEN}Spawn command set to ;find only!{Style.RESET_ALL}")
                elif sc_choice == '3':
                    v = self._ab_input_int(f"Chance for ;p in % (1-99, rest goes to ;find)", ab.get('spawn_p_chance', 50), 1, 99)
                    if v is not None:
                        ab['spawn_command'] = 'both_random'
                        ab['spawn_p_chance'] = v
                        self.config['anti_ban'] = ab
                        self.save_config()
                        print(f"           {Fore.GREEN}Spawn command set to Both random ({v}% ;p / {100-v}% ;find)!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [5] Toggle Skip Spawn ---
            elif choice == '5':
                ab['skip_spawn_enabled'] = not ab.get('skip_spawn_enabled', False)
                self.config['anti_ban'] = ab
                state = "enabled" if ab['skip_spawn_enabled'] else "disabled"
                print(f"           {Fore.GREEN}Random Spawn Skip {state}!{Style.RESET_ALL}")
                if ab['skip_spawn_enabled']:
                    print(f"           {Fore.YELLOW}Bot will randomly skip {ab.get('skip_spawn_chance', 3)}% of spawns.{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [6] Skip Chance ---
            elif choice == '6':
                print(f"\n           {Fore.CYAN}Skip Chance — % chance to ignore a spawn{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('skip_spawn_chance', 3)}%{Style.RESET_ALL}")
                v = self._ab_input_int(f"Skip Chance in % (1-25)", ab.get('skip_spawn_chance', 3), 1, 25)
                if v is not None:
                    ab['skip_spawn_chance'] = v
                    self.config['anti_ban'] = ab
                    print(f"           {Fore.GREEN}Skip Chance set to {v}%!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [7] Toggle Idle Moments ---
            elif choice == '7':
                ab['idle_moments_enabled'] = not ab.get('idle_moments_enabled', False)
                self.config['anti_ban'] = ab
                state = "enabled" if ab['idle_moments_enabled'] else "disabled"
                print(f"           {Fore.GREEN}Random Idle Moments {state}!{Style.RESET_ALL}")
                if ab['idle_moments_enabled']:
                    print(f"           {Fore.YELLOW}Bot will randomly idle for {ab.get('idle_duration_min', 30)}-{ab.get('idle_duration_max', 60)}s.{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [8] Idle Chance ---
            elif choice == '8':
                print(f"\n           {Fore.CYAN}Idle Chance — % chance per catch cycle to idle{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('idle_chance', 5)}%{Style.RESET_ALL}")
                v = self._ab_input_int(f"Idle Chance in % (1-30)", ab.get('idle_chance', 5), 1, 30)
                if v is not None:
                    ab['idle_chance'] = v
                    self.config['anti_ban'] = ab
                    print(f"           {Fore.GREEN}Idle Chance set to {v}%!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [9] Idle Duration ---
            elif choice == '9':
                print(f"\n           {Fore.CYAN}Idle Duration — how long each idle moment lasts{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('idle_duration_min', 30)}s - {ab.get('idle_duration_max', 60)}s{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Range: 10 - 300 seconds (5 min){Style.RESET_ALL}")
                v_min = self._ab_input_int(f"Min Idle in seconds (10-300)", ab.get('idle_duration_min', 30), 10, 300)
                if v_min is not None:
                    v_max_input = self._ab_input_int(f"Max Idle in seconds ({v_min}-300)", ab.get('idle_duration_max', 60), v_min, 300)
                    if v_max_input is not None:
                        ab['idle_duration_min'] = v_min
                        ab['idle_duration_max'] = v_max_input
                        self.config['anti_ban'] = ab
                        print(f"           {Fore.GREEN}Idle Duration set to {v_min}s - {v_max_input}s!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [T] Toggle Typing Simulation ---
            elif choice.lower() == 't':
                ab['typing_simulation_enabled'] = not ab.get('typing_simulation_enabled', False)
                self.config['anti_ban'] = ab
                state = "enabled" if ab['typing_simulation_enabled'] else "disabled"
                print(f"           {Fore.GREEN}Typing Simulation {state}!{Style.RESET_ALL}")
                if ab['typing_simulation_enabled']:
                    print(f"           {Fore.YELLOW}Bot will wait {ab.get('typing_delay_min', 300)}-{ab.get('typing_delay_max', 800)}ms per character before sending commands.{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [D] Typing Delay ---
            elif choice.lower() == 'd':
                print(f"\n           {Fore.CYAN}Typing Delay — ms per character before sending{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('typing_delay_min', 300)}ms - {ab.get('typing_delay_max', 800)}ms{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Range: 50 - 2000 ms{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Example: ';p' = 2 chars → {ab.get('typing_delay_min', 300)*2}-{ab.get('typing_delay_max', 800)*2}ms delay{Style.RESET_ALL}")
                v_min = self._ab_input_int(f"Min Delay in ms (50-2000)", ab.get('typing_delay_min', 300), 50, 2000)
                if v_min is not None:
                    v_max_input = self._ab_input_int(f"Max Delay in ms ({v_min}-2000)", ab.get('typing_delay_max', 800), v_min, 2000)
                    if v_max_input is not None:
                        ab['typing_delay_min'] = v_min
                        ab['typing_delay_max'] = v_max_input
                        self.config['anti_ban'] = ab
                        print(f"           {Fore.GREEN}Typing Delay set to {v_min}ms - {v_max_input}ms!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [N] Toggle Night Mode ---
            elif choice.lower() == 'n':
                ab['night_mode_enabled'] = not ab.get('night_mode_enabled', False)
                self.config['anti_ban'] = ab
                state = "enabled" if ab['night_mode_enabled'] else "disabled"
                print(f"           {Fore.GREEN}Night Mode {state}!{Style.RESET_ALL}")
                if ab['night_mode_enabled']:
                    print(f"           {Fore.YELLOW}Bot will sleep from {ab.get('night_mode_start', 23):02d}:00 to {ab.get('night_mode_end', 7):02d}:00.{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [H] Night Mode Hours ---
            elif choice.lower() == 'h':
                print(f"\n           {Fore.CYAN}Night Mode Hours — when bot sleeps{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {ab.get('night_mode_start', 23):02d}:00 - {ab.get('night_mode_end', 7):02d}:00{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Use 24h format (0-23){Style.RESET_ALL}")
                v_start = self._ab_input_int(f"Sleep START hour (0-23)", ab.get('night_mode_start', 23), 0, 23)
                if v_start is not None:
                    v_end = self._ab_input_int(f"Sleep END hour (0-23)", ab.get('night_mode_end', 7), 0, 23)
                    if v_end is not None:
                        if v_start == v_end:
                            print(f"           {Fore.RED}Start and End cannot be the same hour!{Style.RESET_ALL}")
                        else:
                            ab['night_mode_start'] = v_start
                            ab['night_mode_end'] = v_end
                            self.config['anti_ban'] = ab
                            print(f"           {Fore.GREEN}Night Mode: Sleep from {v_start:02d}:00 to {v_end:02d}:00!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            # --- [R] Reset All ---
            elif choice.lower() == 'r':
                self.config['anti_ban'] = {
                    'enabled': False,
                    'pause_interval_min': 60,
                    'pause_interval_max': 180,
                    'pause_duration_min': 10,
                    'pause_duration_max': 30,
                    'catch_reaction_min': 1,
                    'catch_reaction_max': 3,
                    'spawn_delay_min': 11,
                    'spawn_delay_max': 15,
                    'spawn_command': 'p_only',
                    'spawn_p_chance': 50,
                    'skip_spawn_enabled': False,
                    'skip_spawn_chance': 3,
                    'idle_moments_enabled': False,
                    'idle_chance': 5,
                    'idle_duration_min': 30,
                    'idle_duration_max': 60,
                    'typing_simulation_enabled': False,
                    'typing_delay_min': 300,
                    'typing_delay_max': 800,
                    'night_mode_enabled': False,
                    'night_mode_start': 23,
                    'night_mode_end': 7,
                }
                self.anti_ban_paused = False
                self.anti_ban_next_pause = None
                print(f"           {Fore.GREEN}All Anti-Ban settings reset to defaults!{Style.RESET_ALL}")
                time_module.sleep(1)
            
            elif choice == '0':
                self.save_config()
                break
            
            self.save_config()
    
    def schedule_next_anti_ban_pause(self):
        """Schedule the next anti-ban pause"""
        ab = self.config.get('anti_ban', {})
        if not ab.get('enabled', False):
            self.anti_ban_next_pause = None
            return
        interval_min = ab.get('pause_interval_min', 60)
        interval_max = ab.get('pause_interval_max', 180)
        minutes = random.randint(interval_min, interval_max)
        self.anti_ban_next_pause = datetime.now() + timedelta(minutes=minutes)
        self.log(f"🛡️ Anti-Ban: Next pause scheduled in {minutes} min (at {self.anti_ban_next_pause.strftime('%H:%M:%S')})")
    
    def is_night_mode_active(self):
        """Check if current time is within the night mode sleep window"""
        ab = self.config.get('anti_ban', {})
        if not ab.get('night_mode_enabled', False):
            return False
        now_hour = datetime.now().hour
        start = ab.get('night_mode_start', 23)
        end = ab.get('night_mode_end', 7)
        if start < end:
            return start <= now_hour < end
        else:  # wraps midnight, e.g. 23:00 - 07:00
            return now_hour >= start or now_hour < end
    
    async def get_typing_delay(self, command):
        """Calculate and apply typing simulation delay for a command"""
        ab = self.config.get('anti_ban', {})
        if not ab.get('typing_simulation_enabled', False):
            return
        char_count = len(command)
        delay_min_ms = ab.get('typing_delay_min', 300)
        delay_max_ms = ab.get('typing_delay_max', 800)
        total_ms = sum(random.randint(delay_min_ms, delay_max_ms) for _ in range(char_count))
        total_seconds = total_ms / 1000.0
        self.log(f"🛡️ Anti-Ban: Typing sim {total_ms}ms ({total_seconds:.1f}s) for '{command}'")
        await asyncio.sleep(total_seconds)
    
    async def anti_ban_pause_check(self):
        """Check if it's time for an anti-ban pause, and pause if so"""
        ab = self.config.get('anti_ban', {})
        if not ab.get('enabled', False) or self.anti_ban_next_pause is None:
            return
        
        if datetime.now() >= self.anti_ban_next_pause:
            dur_min = ab.get('pause_duration_min', 10)
            dur_max = ab.get('pause_duration_max', 30)
            pause_minutes = random.randint(dur_min, dur_max)
            
            self.anti_ban_paused = True
            resume_time = datetime.now() + timedelta(minutes=pause_minutes)
            
            self.log(f"🛡️ Anti-Ban: Pausing for {pause_minutes} min (resume at {resume_time.strftime('%H:%M:%S')})")
            print(f"\n{Fore.MAGENTA}  🛡️  Anti-Ban Pause: Sleeping for {pause_minutes} min (until {resume_time.strftime('%H:%M:%S')}){Style.RESET_ALL}\n")
            
            # Sleep in small increments so we can still respond to stop commands
            total_seconds = pause_minutes * 60
            slept = 0
            while slept < total_seconds and self.running:
                await asyncio.sleep(min(5, total_seconds - slept))
                slept += 5
            
            self.anti_ban_paused = False
            self.log(f"🛡️ Anti-Ban: Pause ended, resuming bot.")
            print(f"\n{Fore.GREEN}  🛡️  Anti-Ban Pause ended! Resuming...{Style.RESET_ALL}\n")
            
            # Schedule next pause
            self.schedule_next_anti_ban_pause()
    
    async def anti_ban_night_mode_check(self):
        """Check night mode and sleep until wake time if active"""
        if not self.is_night_mode_active():
            return False
        
        ab = self.config.get('anti_ban', {})
        end_hour = ab.get('night_mode_end', 7)
        
        now = datetime.now()
        wake_time = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
        if wake_time <= now:
            wake_time += timedelta(days=1)
        
        sleep_seconds = (wake_time - now).total_seconds()
        sleep_minutes = int(sleep_seconds / 60)
        
        self.anti_ban_paused = True
        self.log(f"🌙 Night Mode: Sleeping until {wake_time.strftime('%H:%M')} ({sleep_minutes} min)")
        print(f"\n{Fore.MAGENTA}  🌙  Night Mode: Sleeping until {wake_time.strftime('%H:%M')} ({sleep_minutes} min){Style.RESET_ALL}\n")
        
        slept = 0
        while slept < sleep_seconds and self.running:
            await asyncio.sleep(min(10, sleep_seconds - slept))
            slept += 10
        
        self.anti_ban_paused = False
        self.log(f"🌙 Night Mode: Waking up!")
        print(f"\n{Fore.GREEN}  🌙  Night Mode ended! Resuming...{Style.RESET_ALL}\n")
        return True
    
    async def anti_ban_idle_check(self):
        """Randomly idle for a short period (micro-pause)"""
        ab = self.config.get('anti_ban', {})
        if not ab.get('idle_moments_enabled', False):
            return False
        chance = ab.get('idle_chance', 5)
        if random.randint(1, 100) > chance:
            return False
        dur_min = ab.get('idle_duration_min', 30)
        dur_max = ab.get('idle_duration_max', 60)
        idle_secs = random.randint(dur_min, dur_max)
        self.log(f"🛡️ Anti-Ban: Random idle for {idle_secs}s")
        print(f"{Fore.MAGENTA}  🛡️  Idle moment: pausing {idle_secs}s...{Style.RESET_ALL}")
        await asyncio.sleep(idle_secs)
        return True
    
    def should_skip_spawn(self):
        """Check if this spawn should be randomly skipped"""
        ab = self.config.get('anti_ban', {})
        if not ab.get('skip_spawn_enabled', False):
            return False
        chance = ab.get('skip_spawn_chance', 3)
        if random.randint(1, 100) <= chance:
            self.log(f"🛡️ Anti-Ban: Randomly skipping this spawn ({chance}% chance)")
            print(f"{Fore.MAGENTA}  🛡️  Skipping this spawn (random){Style.RESET_ALL}")
            return True
        return False
    
    # ═════════════════════════════════════════════════════════════════
    #  RATE LIMIT PROTECTION
    # ═════════════════════════════════════════════════════════════════
    
