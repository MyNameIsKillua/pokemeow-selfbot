"""Remote control feature: Discord command handler, whitelist, activity messages."""
import os
import sys
import re
import json
import asyncio
import random
import threading
import time as time_module
from datetime import datetime, timedelta
from urllib.parse import urlparse

import discord
from colorama import Fore, Style

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from utils.platform import HAS_AIOHTTP_SOCKS


class RemoteControlMixin:
    async def handle_remote_command(self, message):
        """Handle remote control commands from control channel"""
        rc = self.config.get('remote_control', {})
        prefix = rc.get('prefix', '!')
        raw_content = message.content.strip()
        content = raw_content.lower()
        
        if not content.startswith(prefix):
            return
        
        cmd = content[len(prefix):].split()[0] if content[len(prefix):] else ''
        
        # Console logging for remote commands
        print(f"{Fore.CYAN}  [REMOTE] Command received: {cmd}{Style.RESET_ALL}")
        self.log(f"[REMOTE] Command received: {cmd}")
        
        response = ""
        
        if cmd == 'stop' or cmd == 'pause':
            if not self.paused:
                self.paused = True
                response = "**Bot PAUSED**\n```Use !start to resume.```"
                print(f"\n{Fore.YELLOW}  [REMOTE] Bot PAUSED via remote command{Style.RESET_ALL}")
            else:
                response = "```Bot is already paused.```"
        
        elif cmd == 'start' or cmd == 'resume':
            if self.paused:
                self.paused = False
                response = "**Bot RESUMED**\n```Catching enabled.```"
                print(f"\n{Fore.GREEN}  [REMOTE] Bot RESUMED via remote command{Style.RESET_ALL}")
            else:
                response = "```Bot is already running.```"
        
        elif cmd == 'status' or cmd == 'info':
            account = "Unknown"
            if self.client and self.client.user:
                account = str(self.client.user)
            
            captcha_service = self.config.get('captcha_service', 'none')
            if self.config.get('auto_solve_captcha', False):
                captcha_mode = "CatchBot AI"
            elif captcha_service == 'anticaptcha':
                captcha_mode = "AntiCaptcha"
            elif captcha_service == '2captcha':
                captcha_mode = "2Captcha"
            else:
                captcha_mode = "Manual"
            
            captcha_active = getattr(self, 'captcha_active', False)
            temp_ban = getattr(self, 'temp_banned', False)
            fish_on = self.config.get('fish_enabled', False)
            
            status_lines = [
                f"Account:     {account}",
                f"Status:      {'PAUSED' if self.paused else 'RUNNING'}",
                f"Fishing:     {'ON' if fish_on else 'OFF'}",
                f"Captcha:     {captcha_mode}",
                f"Temp Ban:    {'YES!' if temp_ban else 'No'}",
            ]
            response = "**Bot Status**\n```\n" + "\n".join(status_lines) + "\n```"
        
        elif cmd == 'stats':
            ss = getattr(self, 'session_stats', {})
            caught = ss.get('total_caught', 0)
            fled = ss.get('total_fled', 0)
            fished = ss.get('total_fished', 0)
            encounters = ss.get('total_encounters', 0)
            best = ss.get('best_catches', [])
            session_shinies = sum(1 for c in best if 'shiny' in c.lower()) if best else 0
            session_legends = sum(1 for c in best if any(x in c.lower() for x in ['legendary', 'mythical'])) if best else 0
            eggs = ss.get('eggs_hatched', 0)
            rate = (caught / encounters * 100) if encounters > 0 else 0
            captcha_attempts = ss.get('captcha_attempts', {})
            total_captchas = sum(captcha_attempts.values()) if captcha_attempts else 0
            
            stats_lines = [
                f"Encounters:  {encounters}",
                f"Caught:      {caught} ({rate:.1f}%)",
                f"Fled:        {fled}",
                f"Fished:      {fished}",
                f"Shinies:     {session_shinies}",
                f"Legendaries: {session_legends}",
                f"Eggs:        {eggs}",
                f"Captchas:    {total_captchas} solved",
            ]
            response = "**Session Stats**\n```\n" + "\n".join(stats_lines) + "\n```"
        
        elif cmd == 'lifetime':
            ps = getattr(self, 'persistent_stats', {})
            total_caught = ps.get('total_caught_alltime', 0)
            total_fled = ps.get('total_fled_alltime', 0)
            total_encounters = total_caught + total_fled
            catch_rate = (total_caught / total_encounters * 100) if total_encounters > 0 else 0
            sessions = ps.get('total_sessions', 0)
            shinies = ps.get('shinys_caught', 0)
            legends = ps.get('legendarys_caught', 0)
            fished = ps.get('total_fished_alltime', 0)
            eggs = len(ps.get('egg_pokemon_list', []))
            captchas = ps.get('total_captchas_solved', 0)
            
            stats_lines = [
                f"Sessions:      {sessions}",
                f"Caught:        {total_caught}",
                f"Fled:          {total_fled}",
                f"Catch-Rate:    {catch_rate:.1f}%",
                f"Shinies:       {shinies}",
                f"Legendaries:   {legends}",
                f"Fished:        {fished}",
                f"Eggs Hatched:  {eggs}",
                f"Captchas:      {captchas}",
            ]
            response = "**Lifetime Stats**\n```\n" + "\n".join(stats_lines) + "\n```"
        
        elif cmd == 'fish':
            if self.config.get('fish_enabled', False):
                self.config['fish_enabled'] = False
                response = "```Fishing DISABLED```"
                print(f"\n{Fore.YELLOW}  [REMOTE] Fishing DISABLED via remote command{Style.RESET_ALL}")
            else:
                self.config['fish_enabled'] = True
                response = "```Fishing ENABLED```"
                print(f"\n{Fore.GREEN}  [REMOTE] Fishing ENABLED via remote command{Style.RESET_ALL}")
            self.save_config()
        
        elif cmd == 'ping':
            response = "```Pong! Bot is alive.```"
        
        elif cmd == 'uptime':
            session_start = self.session_stats.get('session_start')
            if session_start:
                delta = datetime.now() - session_start
                hours, remainder = divmod(int(delta.total_seconds()), 3600)
                minutes, seconds = divmod(remainder, 60)
                uptime_str = f"{hours}h {minutes}m {seconds}s"
                response = f"**Uptime**\n```Bot running for: {uptime_str}```"
            else:
                response = "```Uptime not available.```"
        
        elif cmd == 'daily':
            channel_id = self.config.get('channel_id', '')
            if channel_id:
                try:
                    ch = self.client.get_channel(int(channel_id))
                    if ch:
                        self.doing_dailys = True
                        self.paused = True
                        self.catching = False
                        
                        response = "```BOT STOPPED. Daily tasks in 6s...```"
                        print(f"\n{Fore.RED}  ======================================{Style.RESET_ALL}")
                        print(f"{Fore.RED}  [REMOTE] BOT STOPPED FOR DAILY TASKS{Style.RESET_ALL}")
                        print(f"{Fore.RED}  ======================================{Style.RESET_ALL}")
                        
                        async def run_daily_delayed():
                            try:
                                for i in range(6, 0, -1):
                                    print(f"{Fore.YELLOW}  [REMOTE] Starting daily tasks in {i}s...{Style.RESET_ALL}")
                                    await asyncio.sleep(1)
                                
                                # Keep paused=True during daily tasks, doing_dailys keeps main loop stopped
                                print(f"\n{Fore.CYAN}  [REMOTE] Running daily tasks now...{Style.RESET_ALL}")
                                await self.run_daily_tasks(ch)
                            except Exception as e:
                                print(f"{Fore.RED}  [REMOTE] Daily tasks error: {e}{Style.RESET_ALL}")
                            finally:
                                self.doing_dailys = False
                                self.paused = False
                                print(f"\n{Fore.GREEN}  ======================================{Style.RESET_ALL}")
                                print(f"{Fore.GREEN}  [REMOTE] DAILY DONE - BOT RESUMED{Style.RESET_ALL}")
                                print(f"{Fore.GREEN}  ======================================{Style.RESET_ALL}\n")
                        
                        asyncio.create_task(run_daily_delayed())
                    else:
                        response = "```Channel not found.```"
                except Exception as e:
                    response = f"```Error: {str(e)[:30]}```"
            else:
                response = "```No channel configured.```"
        
        elif cmd == 'channel':
            channel_id = self.config.get('channel_id', '')
            channel_name = "Unknown"
            if channel_id:
                try:
                    ch = self.client.get_channel(int(channel_id))
                    if ch:
                        channel_name = f"#{ch.name}" if hasattr(ch, 'name') else str(channel_id)
                except:
                    pass
            response = f"**Hunting Channel**\n```{channel_name}\nID: {channel_id}```"
        
        elif cmd == 'sleep':
            parts = content.split()
            mins = 30
            if len(parts) > 1:
                try:
                    mins = int(parts[1])
                except:
                    pass
            mins = max(1, min(mins, 480))
            self.sleep_until = datetime.now() + timedelta(minutes=mins)
            self.paused = True
            response = f"**Bot Sleeping**\n```Sleeping for {mins} minutes.\nUse !wake to wake early.```"
            print(f"\n{Fore.YELLOW}  [REMOTE] Bot sleeping for {mins} minutes{Style.RESET_ALL}")
        
        elif cmd == 'wake':
            if hasattr(self, 'sleep_until') and self.sleep_until:
                self.sleep_until = None
                self.paused = False
                response = "**Bot Awake**\n```Bot woke up and resumed.```"
                print(f"\n{Fore.GREEN}  [REMOTE] Bot woke up via remote command{Style.RESET_ALL}")
            else:
                self.paused = False
                response = "```Bot was not sleeping, but resumed anyway.```"
        
        elif cmd == 'screenshot' or cmd == 'ss':
            try:
                import mss
                import io
                import discord
                
                parts = content.split()
                monitor_num = 1
                if len(parts) > 1:
                    try:
                        monitor_num = int(parts[1])
                    except:
                        pass
                
                with mss.mss() as sct:
                    num_monitors = len(sct.monitors) - 1
                    
                    if monitor_num < 1 or monitor_num > num_monitors:
                        response = f"```Invalid monitor. Available: 1-{num_monitors}\nUsage: !ss [1-{num_monitors}]```"
                    else:
                        monitor = sct.monitors[monitor_num]
                        screenshot = sct.grab(monitor)
                        
                        from PIL import Image
                        img = Image.frombytes('RGB', screenshot.size, screenshot.bgra, 'raw', 'BGRX')
                        
                        img_bytes = io.BytesIO()
                        img.save(img_bytes, format='PNG')
                        img_bytes.seek(0)
                        
                        await message.channel.send(
                            f"**Screenshot (Monitor {monitor_num}/{num_monitors})**",
                            file=discord.File(img_bytes, filename=f"screenshot_m{monitor_num}_{datetime.now().strftime('%H%M%S')}.png")
                        )
                        response = ""
                        print(f"\n{Fore.CYAN}  [REMOTE] Screenshot sent (Monitor {monitor_num}){Style.RESET_ALL}")
            except ImportError:
                response = "```Screenshot requires: pip install mss pillow```"
            except Exception as e:
                response = f"```Screenshot failed: {str(e)[:40]}```"
        
        elif cmd == 'captcha':
            ss = getattr(self, 'session_stats', {})
            ps = getattr(self, 'persistent_stats', {})
            
            session_attempts = ss.get('captcha_attempts', {})
            lifetime_attempts = ps.get('captcha_attempts', {})
            lifetime_total = ps.get('total_captchas_solved', 0)
            
            lines = []
            lines.append("SESSION:")
            if session_attempts:
                for attempts, count in sorted(session_attempts.items()):
                    lines.append(f"  {attempts} Attempt{'s' if int(attempts) > 1 else ''}:  {count}x")
                session_total = sum(session_attempts.values())
                lines.append(f"  Total:      {session_total}x")
            else:
                lines.append("  No captchas yet")
            
            lines.append("")
            lines.append("LIFETIME:")
            if lifetime_attempts:
                for attempts, count in sorted(lifetime_attempts.items(), key=lambda x: int(x[0])):
                    lines.append(f"  {attempts} Attempt{'s' if int(attempts) > 1 else ''}:  {count}x")
                lines.append(f"  Total:      {lifetime_total}x")
            else:
                lines.append("  No captchas yet")
            
            response = "**Captcha Stats**\n```\n" + "\n".join(lines) + "\n```"
        
        elif cmd == 'inv':
            channel_id = self.config.get('channel_id', '')
            if channel_id:
                try:
                    ch = self.client.get_channel(int(channel_id))
                    if ch:
                        was_paused = self.paused
                        self.paused = True
                        response = "```Checking inventory...```"
                        print(f"\n{Fore.CYAN}  [REMOTE] Inventory check requested{Style.RESET_ALL}")
                        
                        async def run_inv_check():
                            try:
                                await asyncio.sleep(3)
                                
                                # Send ;inv and wait for response
                                inv_future = asyncio.ensure_future(
                                    self.wait_for_message_return(ch, 'item inventory', timeout=15)
                                )
                                await asyncio.sleep(0.3)
                                await self.send_command(ch, ';inv')
                                self.log("[REMOTE] ;inv sent")
                                
                                inv_response = await inv_future
                                
                                inv_lootboxes = 0
                                inv_grazz = 0
                                ball_counts = {}
                                inv_honey = 0
                                inv_incense = 0
                                inv_repels = 0
                                
                                if inv_response and inv_response.embeds:
                                    inv_text = ''
                                    for embed in inv_response.embeds:
                                        embed_dict = embed.to_dict()
                                        if 'description' in embed_dict:
                                            inv_text += str(embed_dict['description']) + '\n'
                                        for field in embed_dict.get('fields', []):
                                            inv_text += str(field.get('name', '')) + ' ' + str(field.get('value', '')) + '\n'
                                        author = embed_dict.get('author', {})
                                        if 'name' in author:
                                            inv_text += str(author['name']) + '\n'
                                    
                                    inv_text_clean = inv_text.replace('**', '')
                                    inv_text_lower = inv_text_clean.lower()
                                    
                                    # Parse PokeCoins
                                    inv_coins = 0
                                    coins_match = re.search(r'([\d,]+)x\s*pokecoins', inv_text_lower)
                                    if coins_match:
                                        inv_coins = int(coins_match.group(1).replace(',', ''))
                                    
                                    # Parse lootbox count
                                    lootbox_match = re.search(r'([\d,]+)x\s*lootbox', inv_text_lower)
                                    if lootbox_match:
                                        inv_lootboxes = int(lootbox_match.group(1).replace(',', ''))
                                    
                                    # Parse grazz count
                                    grazz_match = re.search(r'([\d,]+)x\s*grazz\s*berr', inv_text_lower)
                                    if grazz_match:
                                        inv_grazz = int(grazz_match.group(1).replace(',', ''))
                                    
                                    # Parse ball counts
                                    ball_names_map = {
                                        'pb': ('poke ball', 'Pokeballs'),
                                        'gb': ('great ball', 'Greatballs'),
                                        'ub': ('ultra ball', 'Ultraballs'),
                                        'mb': ('master ball', 'Masterballs'),
                                        'premier': ('premier ball', 'Premierballs'),
                                    }
                                    for ball_key, (ball_pattern, ball_display) in ball_names_map.items():
                                        ball_match = re.search(r'([\d,]+)x\s*' + ball_pattern, inv_text_lower)
                                        if ball_match:
                                            ball_counts[ball_key] = int(ball_match.group(1).replace(',', ''))
                                    
                                    # Parse other items
                                    honey_match = re.search(r'([\d,]+)x\s*honey', inv_text_lower)
                                    inv_honey = int(honey_match.group(1).replace(',', '')) if honey_match else 0
                                    incense_match = re.search(r'([\d,]+)x\s*incense', inv_text_lower)
                                    inv_incense = int(incense_match.group(1).replace(',', '')) if incense_match else 0
                                    repel_match = re.search(r'([\d,]+)x\s*repel', inv_text_lower)
                                    inv_repels = int(repel_match.group(1).replace(',', '')) if repel_match else 0
                                    
                                    # Print to console
                                    ts = datetime.now().strftime('%H:%M:%S')
                                    print(f"{Fore.CYAN}  [REMOTE] === Inventory ==={Style.RESET_ALL}")
                                    print(f"{Fore.CYAN}  [REMOTE]   PokeCoins: {inv_coins:,}{Style.RESET_ALL}")
                                    print(f"{Fore.CYAN}  [REMOTE]   PB: {ball_counts.get('pb',0)} | GB: {ball_counts.get('gb',0)} | UB: {ball_counts.get('ub',0)} | MB: {ball_counts.get('mb',0)} | Premier: {ball_counts.get('premier',0)}{Style.RESET_ALL}")
                                    print(f"{Fore.CYAN}  [REMOTE]   LB: {inv_lootboxes} | GRazz: {inv_grazz} | Honey: {inv_honey} | Incense: {inv_incense} | Repels: {inv_repels}{Style.RESET_ALL}")
                                    
                                    # Send inventory summary to remote channel
                                    inv_lines = [
                                        f"PokeCoins:    {inv_coins:,}",
                                        "",
                                        "Pokeballs:    " + str(ball_counts.get('pb', 0)),
                                        "Greatballs:   " + str(ball_counts.get('gb', 0)),
                                        "Ultraballs:   " + str(ball_counts.get('ub', 0)),
                                        "Masterballs:  " + str(ball_counts.get('mb', 0)),
                                        "Premierballs: " + str(ball_counts.get('premier', 0)),
                                        "",
                                        "Lootboxes:    " + str(inv_lootboxes),
                                        "GRazz:        " + str(inv_grazz),
                                        "Honey:        " + str(inv_honey),
                                        "Incense:      " + str(inv_incense),
                                        "Repels:       " + str(inv_repels),
                                    ]
                                    inv_summary = "**Inventory**\n```\n" + "\n".join(inv_lines) + "\n```"
                                    await message.channel.send(inv_summary)
                                    
                                    # Open lootboxes if any
                                    if inv_lootboxes > 0:
                                        await asyncio.sleep(3)
                                        await self.send_command(ch, ';lb all')
                                        self.log(f"[REMOTE] ;lb all sent ({inv_lootboxes} lootboxes)")
                                        print(f"{Fore.MAGENTA}  [REMOTE] Opening {inv_lootboxes} Lootboxes...{Style.RESET_ALL}")
                                        await message.channel.send(f"```Opening {inv_lootboxes} Lootboxes...```")
                                        await asyncio.sleep(3)
                                    
                                    # Use grazz berries if any
                                    if inv_grazz > 0:
                                        await asyncio.sleep(3)
                                        await self.send_command(ch, ';grazz all')
                                        self.log(f"[REMOTE] ;grazz all sent ({inv_grazz} grazz berries)")
                                        print(f"{Fore.MAGENTA}  [REMOTE] Using {inv_grazz} GRazz Berries...{Style.RESET_ALL}")
                                        await message.channel.send(f"```Using {inv_grazz} GRazz Berries...```")
                                        await asyncio.sleep(3)
                                    
                                    if inv_lootboxes == 0 and inv_grazz == 0:
                                        await message.channel.send("```No Lootboxes or GRazz to use.```")
                                    
                                    await message.channel.send("```Inventory check done. Bot resumed.```")
                                else:
                                    await message.channel.send("```No inventory response from PokeMeow.```")
                                    print(f"{Fore.RED}  [REMOTE] No inventory response received{Style.RESET_ALL}")
                            
                            except Exception as e:
                                print(f"{Fore.RED}  [REMOTE] Inventory check error: {e}{Style.RESET_ALL}")
                                try:
                                    await message.channel.send(f"```Inventory check error: {str(e)[:40]}```")
                                except:
                                    pass
                            finally:
                                if not was_paused:
                                    self.paused = False
                                    print(f"{Fore.GREEN}  [REMOTE] Bot resumed after inventory check{Style.RESET_ALL}")
                        
                        asyncio.create_task(run_inv_check())
                    else:
                        response = "```Catch channel not found.```"
                except Exception as e:
                    response = f"```Error: {str(e)[:30]}```"
            else:
                response = "```No catch channel configured.```"
        
        elif cmd == 'text':
            # Extract the text after "!text " using original (non-lowered) content
            text_after_cmd = raw_content[len(prefix) + len('text'):].strip()
            if not text_after_cmd:
                response = f"```Usage: {prefix}text <message or command>\nExample: {prefix}text ;bal\nBot stays paused until {prefix}start```"
            else:
                channel_id = self.config.get('channel_id', '')
                if channel_id:
                    try:
                        ch = self.client.get_channel(int(channel_id))
                        if ch:
                            already_paused = self.paused
                            self.paused = True
                            if already_paused:
                                response = f"```Sending: {text_after_cmd}```"
                                print(f"{Fore.CYAN}  [REMOTE] Will send: {text_after_cmd}{Style.RESET_ALL}")
                            else:
                                response = f"**Bot PAUSED**\n```Sending in 5s: {text_after_cmd}\nBot stays paused until {prefix}start```"
                                print(f"\n{Fore.YELLOW}  [REMOTE] Bot PAUSED for !text command{Style.RESET_ALL}")
                                print(f"{Fore.CYAN}  [REMOTE] Will send: {text_after_cmd}{Style.RESET_ALL}")
                            
                            async def run_text_command():
                                try:
                                    if not already_paused:
                                        for i in range(5, 0, -1):
                                            print(f"{Fore.YELLOW}  [REMOTE] Sending text in {i}s...{Style.RESET_ALL}")
                                            await asyncio.sleep(1)
                                    
                                    # Listen for PokeMeow response BEFORE sending
                                    pokemeow_future = asyncio.ensure_future(
                                        self.wait_for_message_return(ch, '', timeout=15)
                                    )
                                    await asyncio.sleep(0.3)
                                    
                                    # Send the user's message
                                    await self.send_command(ch, text_after_cmd)
                                    self.log(f"[REMOTE] Text sent: {text_after_cmd}")
                                    
                                    # Wait for response from PokeMeow
                                    pm_response = await pokemeow_future
                                    
                                    if pm_response:
                                        # Helper: clean Discord markup for readable output
                                        def clean_discord_text(text):
                                            """Strip Discord emoji codes, custom emojis, markdown bold, etc."""
                                            t = str(text)
                                            # Convert Discord timestamps <t:1743656400:F> to readable time
                                            def _convert_timestamp(m):
                                                try:
                                                    ts = int(m.group(1))
                                                    dt = datetime.fromtimestamp(ts)
                                                    return dt.strftime('%d.%m.%Y %H:%M')
                                                except:
                                                    return m.group(0)
                                            t = re.sub(r'<t:(\d+)(?::[a-zA-Z])?>', _convert_timestamp, t)
                                            # Replace known emoji codes with Unicode BEFORE stripping all
                                            emoji_map = {
                                                ':white_check_mark:': '✅',
                                                ':x:': '❌',
                                                ':warning:': '⚠️',
                                                ':star:': '⭐',
                                                ':star2:': '🌟',
                                                ':sparkles:': '✨',
                                                ':heavy_check_mark:': '✔️',
                                                ':no_entry_sign:': '🚫',
                                                ':new:': '🆕',
                                                ':moneybag:': '💰',
                                                ':notepad_spiral:': '📝',
                                                ':timer:': '⏱️',
                                                ':timer_clock:': '⏲️',
                                                ':crossed_swords:': '⚔️',
                                            }
                                            for code, emoji in emoji_map.items():
                                                t = t.replace(code, emoji)
                                            # Replace known PokeMeow custom emojis <:name:id> with readable text
                                            pokemeow_emoji_map = {
                                                # Currencies & tokens
                                                'pokecoin': 'PokeCoins', 'PokeCoin': 'PokeCoins',
                                                'fishingtoken': 'Fishing Token', 'patreon_token': 'Patreon Token',
                                                'votecoin': 'Vote Coin', 'battle_points': 'Battle Points',
                                                'research_point': 'Research Point',
                                                'tickets': 'Swap Tickets', 'swapticket': 'Swap Ticket',
                                                'safari_ticket': 'Safari Ticket',
                                                'eonticket': 'Event Ticket', 'event_voucher': 'Event Voucher',
                                                # Balls
                                                'pokeball': 'Pokeball', 'greatball': 'Greatball',
                                                'ultraball': 'Ultraball', 'masterball': 'Masterball',
                                                'premierball': 'Premierball', 'diveball': 'Diveball',
                                                'beastball': 'Beastball', 'luxuryball': 'Luxuryball',
                                                'netball': 'Netball', 'lureball': 'Lureball',
                                                'duskball': 'Duskball', 'moonball': 'Moonball',
                                                'friendball': 'Friendball', 'loveball': 'Loveball',
                                                'fastball': 'Fastball', 'heavyball': 'Heavyball',
                                                'quickball': 'Quickball',
                                                # Berries & consumables
                                                'goldenrazzberry': 'GRazz Berry', 'goldenrazz': 'GRazz Berry',
                                                'rarecandy': 'Rare Candy',
                                                'honey': 'Honey', 'incense': 'Incense',
                                                'repel': 'Repel', 'super_repel': 'Super Repel',
                                                'superrepel': 'Super Repel', 'max_repel': 'Max Repel',
                                                'maxrepel': 'Max Repel',
                                                'lootbox': 'Lootbox', 'lootboxes': 'Lootbox',
                                                # Fishing
                                                'pokelure': 'Pokelure', 'mistys_lure': "Misty's Lure",
                                                'seaflute': 'Seaflute',
                                                'oldrod': '🎣', 'goodrod': '🎣', 'superrod': '🎣',
                                                # Eggs & incubators
                                                'poke_egg': '🥚',
                                                'i': 'Incubator', 'si': 'Super Incubator',
                                                # Catching
                                                'pokeradar': 'Pokeradar',
                                                'dexcaught': '🏀', 'dex': 'Dex',
                                                # Evolution items & held items
                                                'fire_stone': 'Fire Stone', 'water_stone': 'Water Stone',
                                                'thunder_stone': 'Thunder Stone', 'leaf_stone': 'Leaf Stone',
                                                'sun_stone': 'Sun Stone', 'moon_stone': 'Moon Stone',
                                                'shiny_stone': 'Shiny Stone', 'dusk_stone': 'Dusk Stone',
                                                'dawn_stone': 'Dawn Stone', 'ice_stone': 'Ice Stone',
                                                'oval_stone': 'Oval Stone',
                                                'sachet': 'Sachet', 'reaper_cloth': 'Reaper Cloth',
                                                'dubious_disc': 'Dubious Disc', 'upgrade': 'Upgrade',
                                                'protector': 'Protector', 'whipped_dream': 'Whipped Dream',
                                                'malicious_armor': 'Malicious Armor',
                                                'galarica_wreath': 'Galarica Wreath',
                                                'galarica_cuff': 'Galarica Cuff',
                                                # Held items & battle items
                                                'c': 'Charcoal', 'mystic_water': 'Mystic Water',
                                                'li': 'Luck Incense', 'fs': 'Focus Sash',
                                                'sb': 'Sitrus Berry', 'ms': 'Miracle Seed',
                                                # Trainer avatars (remove silently)
                                                'trainer_brendan': '', 'trainer_may': '',
                                            }
                                            def _replace_custom_emoji(m):
                                                name = m.group(1)
                                                # Check exact match first, then lowercase
                                                replacement = pokemeow_emoji_map.get(name) or pokemeow_emoji_map.get(name.lower())
                                                if replacement is not None:
                                                    return replacement
                                                return ''  # Unknown custom emoji: remove
                                            t = re.sub(r'<a?:(\w+):\d+>', _replace_custom_emoji, t)
                                            # Remove incomplete custom emoji at end of text: <:name:id (no closing >)
                                            t = re.sub(r'<:?\w+:\d+$', '', t)
                                            # Remove remaining standard emoji codes that have known text replacements
                                            # (these are the :name: format without < > brackets)
                                            for ename, erepl in pokemeow_emoji_map.items():
                                                t = t.replace(f':{ename}:', erepl if erepl else '')
                                            # Remove any remaining unknown standard emoji codes: :something:
                                            t = re.sub(r':[\w]+:', '', t)
                                            # Remove markdown bold **text** -> text
                                            t = t.replace('**', '')
                                            # Remove backtick formatting
                                            t = t.replace('`', '')
                                            # Clean up multiple spaces
                                            t = re.sub(r'  +', ' ', t)
                                            # Clean up lines that are now empty or just whitespace/dashes
                                            lines = []
                                            for line in t.split('\n'):
                                                stripped = line.strip()
                                                if stripped and stripped not in ('-', '- ', '•'):
                                                    # Clean leading "- " with nothing after emoji removal
                                                    stripped = re.sub(r'^-\s*$', '', stripped)
                                                    if stripped:
                                                        lines.append(stripped)
                                            return '\n'.join(lines)
                                        
                                        # Build response text from message content and embeds
                                        resp_parts = []
                                        if pm_response.content:
                                            cleaned = clean_discord_text(pm_response.content[:500])
                                            if cleaned:
                                                resp_parts.append(cleaned)
                                        if pm_response.embeds:
                                            for embed in pm_response.embeds:
                                                embed_dict = embed.to_dict()
                                                # Author name (often the title in PokeMeow)
                                                author = embed_dict.get('author', {})
                                                if 'name' in author:
                                                    cleaned = clean_discord_text(author['name'])
                                                    if cleaned:
                                                        resp_parts.append(f"--- {cleaned} ---")
                                                if 'title' in embed_dict:
                                                    cleaned = clean_discord_text(embed_dict['title'])
                                                    if cleaned:
                                                        resp_parts.append(cleaned)
                                                if 'description' in embed_dict:
                                                    cleaned = clean_discord_text(embed_dict['description'][:800])
                                                    if cleaned:
                                                        resp_parts.append(cleaned)
                                                for field in embed_dict.get('fields', []):
                                                    fname = clean_discord_text(field.get('name', ''))
                                                    fval = clean_discord_text(field.get('value', ''))
                                                    if fname or fval:
                                                        resp_parts.append(f"{fname}: {fval}" if fname and fval else fname or fval)
                                                footer = embed_dict.get('footer', {})
                                                if 'text' in footer:
                                                    cleaned = clean_discord_text(footer['text'])
                                                    if cleaned:
                                                        resp_parts.append(f"({cleaned})")
                                        
                                        resp_text = "\n".join(resp_parts) if resp_parts else "(empty response)"
                                        # Truncate if too long for Discord
                                        if len(resp_text) > 1800:
                                            resp_text = resp_text[:1800] + "\n..."
                                        
                                        forward_msg = f"**Response to:** `{text_after_cmd}`\n```\n{resp_text}\n```"
                                        await message.channel.send(forward_msg)
                                        print(f"{Fore.CYAN}  [REMOTE] PokeMeow response forwarded to control channel{Style.RESET_ALL}")
                                    else:
                                        await message.channel.send(f"```No response received for: {text_after_cmd}```")
                                        print(f"{Fore.YELLOW}  [REMOTE] No response received for text command{Style.RESET_ALL}")
                                    
                                    await message.channel.send(f"```Bot is PAUSED. Use {prefix}start to resume.```")
                                    print(f"{Fore.YELLOW}  [REMOTE] Bot stays PAUSED. Waiting for {prefix}start{Style.RESET_ALL}")
                                
                                except Exception as e:
                                    print(f"{Fore.RED}  [REMOTE] Text command error: {e}{Style.RESET_ALL}")
                                    try:
                                        await message.channel.send(f"```Text command error: {str(e)[:40]}\nBot is PAUSED. Use {prefix}start to resume.```")
                                    except:
                                        pass
                            
                            asyncio.create_task(run_text_command())
                        else:
                            response = "```Catch channel not found.```"
                    except Exception as e:
                        response = f"```Error: {str(e)[:30]}```"
                else:
                    response = "```No catch channel configured.```"
        
        elif cmd == 'help':
            help_lines = [
                f"{prefix}stop      - Pause the bot",
                f"{prefix}start     - Resume the bot",
                f"{prefix}sleep [m] - Sleep for m minutes",
                f"{prefix}wake      - Wake from sleep",
                f"{prefix}status    - Bot status & config",
                f"{prefix}stats     - Session stats",
                f"{prefix}captcha   - Captcha stats",
                f"{prefix}lifetime  - Lifetime stats",
                f"{prefix}uptime    - Bot running time",
                f"{prefix}channel   - Hunting channel",
                f"{prefix}fish      - Toggle fishing",
                f"{prefix}daily     - Run daily tasks",
                f"{prefix}inv       - Check inventory + lb/grazz",
                f"{prefix}text <msg>- Send custom message in catch channel",
                f"{prefix}ss [1-4]  - Screenshot monitor",
                f"{prefix}ping      - Check if alive",
            ]
            response = "**Remote Commands**\n```\n" + "\n".join(help_lines) + "\n```"
        
        else:
            response = f"```Unknown command. Use {prefix}help for list.```"
        
        if response:
            try:
                await message.channel.send(response)
                print(f"{Fore.CYAN}  [REMOTE] Response sent{Style.RESET_ALL}")
                self.log(f"[REMOTE] Response: {response[:50]}...")
            except Exception as e:
                print(f"{Fore.RED}  [REMOTE] Failed to send response: {e}{Style.RESET_ALL}")
                self.log(f"[REMOTE] Failed to send response: {e}")
    
    # ═════════════════════════════════════════════════════════════════
    #  CAPTCHA SYSTEM
    # ═════════════════════════════════════════════════════════════════
    
    def handle_remote_control_config(self):
        """Handler for Remote Control configuration"""
        while True:
            self.clear_screen()
            rc = self.config.get('remote_control', {
                'enabled': False,
                'control_channel_id': '',
                'prefix': '!',
                'whitelist_user_ids': []
            })
            
            print(f"\n{Fore.CYAN}+=============================================+{Style.RESET_ALL}")
            print(f"{Fore.CYAN}|        Remote Control Settings              |{Style.RESET_ALL}")
            print(f"{Fore.CYAN}+=============================================+{Style.RESET_ALL}\n")
            
            st = f"{Fore.GREEN}ON{Style.RESET_ALL}" if rc.get('enabled', False) else f"{Fore.RED}OFF{Style.RESET_ALL}"
            channel_id = rc.get('control_channel_id', '')
            prefix = rc.get('prefix', '!')
            whitelist = rc.get('whitelist_user_ids', [])
            
            print(f"           [1] Toggle Remote Control: {st}")
            print(f"           [2] Control Channel ID: {Fore.YELLOW}{channel_id if channel_id else 'Not set'}{Style.RESET_ALL}")
            print(f"           [3] Command Prefix: {Fore.YELLOW}{prefix}{Style.RESET_ALL}")
            print(f"           [4] Whitelist User IDs: {Fore.YELLOW}{len(whitelist)} users{Style.RESET_ALL}")
            print(f"\n           [0] Back")
            
            print(f"\n           {Fore.YELLOW}Info: Control the bot from a private Discord channel.{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}Commands: {prefix}stop, {prefix}start, {prefix}stats, {prefix}daily, {prefix}ss, etc.{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}Use {prefix}help in control channel to see all commands.{Style.RESET_ALL}")
            
            choice = input(f"\n           {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            if choice == '1':
                rc['enabled'] = not rc.get('enabled', False)
                self.config['remote_control'] = rc
                self.save_config()
                status_str = "enabled" if rc['enabled'] else "disabled"
                print(f"           {Fore.GREEN}Remote Control {status_str}!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '2':
                print(f"\n           {Fore.CYAN}Enter Control Channel ID:{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}This is a PRIVATE channel where you send commands.{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Right-click channel > Copy Channel ID{Style.RESET_ALL}")
                if channel_id:
                    print(f"           {Fore.GREEN}Current: {channel_id}{Style.RESET_ALL}")
                new_id = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                if new_id:
                    rc['control_channel_id'] = new_id
                    self.config['remote_control'] = rc
                    self.save_config()
                    print(f"           {Fore.GREEN}Control Channel ID saved!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '3':
                print(f"\n           {Fore.CYAN}Enter Command Prefix (default: !){Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {prefix}{Style.RESET_ALL}")
                new_prefix = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                if new_prefix:
                    rc['prefix'] = new_prefix
                    self.config['remote_control'] = rc
                    self.save_config()
                    print(f"           {Fore.GREEN}Prefix set to: {new_prefix}{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '4':
                self.handle_whitelist_config(rc)
            elif choice == '0':
                break
    
    def handle_whitelist_config(self, rc):
        """Handler for Whitelist management sub-menu"""
        while True:
            self.clear_screen()
            whitelist = rc.get('whitelist_user_ids', [])
            
            print(f"\n{Fore.CYAN}+=============================================+{Style.RESET_ALL}")
            print(f"{Fore.CYAN}|       Whitelist Management                  |{Style.RESET_ALL}")
            print(f"{Fore.CYAN}+=============================================+{Style.RESET_ALL}\n")
            
            print(f"           {Fore.YELLOW}Whitelisted users can use remote commands.{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}Your own account always works (no need to add).{Style.RESET_ALL}\n")
            
            if whitelist:
                print(f"           {Fore.GREEN}Whitelisted User IDs:{Style.RESET_ALL}")
                for i, user_id in enumerate(whitelist, 1):
                    print(f"             {i}. {Fore.CYAN}{user_id}{Style.RESET_ALL}")
            else:
                print(f"           {Fore.YELLOW}No users whitelisted yet.{Style.RESET_ALL}")
            
            print(f"\n           [1] Add User ID")
            print(f"           [2] Remove User ID")
            print(f"           [3] Clear All")
            print(f"\n           [0] Back")
            
            choice = input(f"\n           {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            if choice == '1':
                print(f"\n           {Fore.CYAN}Enter Discord User ID to whitelist:{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}(Right-click user > Copy User ID){Style.RESET_ALL}")
                user_id = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                if user_id:
                    if user_id not in whitelist:
                        whitelist.append(user_id)
                        rc['whitelist_user_ids'] = whitelist
                        self.config['remote_control'] = rc
                        self.save_config()
                        print(f"           {Fore.GREEN}User {user_id} added to whitelist!{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.YELLOW}User already in whitelist.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '2':
                if whitelist:
                    print(f"\n           {Fore.CYAN}Enter User ID to remove (or number from list):{Style.RESET_ALL}")
                    remove_input = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                    try:
                        # Check if it's a number (index)
                        idx = int(remove_input) - 1
                        if 0 <= idx < len(whitelist):
                            removed = whitelist.pop(idx)
                            rc['whitelist_user_ids'] = whitelist
                            self.config['remote_control'] = rc
                            self.save_config()
                            print(f"           {Fore.GREEN}User {removed} removed from whitelist!{Style.RESET_ALL}")
                        else:
                            print(f"           {Fore.RED}Invalid number.{Style.RESET_ALL}")
                    except ValueError:
                        # It's a user ID string
                        if remove_input in whitelist:
                            whitelist.remove(remove_input)
                            rc['whitelist_user_ids'] = whitelist
                            self.config['remote_control'] = rc
                            self.save_config()
                            print(f"           {Fore.GREEN}User {remove_input} removed!{Style.RESET_ALL}")
                        else:
                            print(f"           {Fore.RED}User not found in whitelist.{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.YELLOW}Whitelist is empty.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '3':
                if whitelist:
                    confirm = input(f"           {Fore.RED}Clear all whitelisted users? (y/n): {Style.RESET_ALL}").lower()
                    if confirm == 'y':
                        rc['whitelist_user_ids'] = []
                        self.config['remote_control'] = rc
                        self.save_config()
                        print(f"           {Fore.GREEN}Whitelist cleared!{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.YELLOW}Whitelist is already empty.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '0':
                break
    
    async def maybe_send_activity_message(self, channel):
        """Maybe send a random activity message based on chance. Call after catching."""
        ab = self.config.get('anti_ban', {})
        if not ab.get('activity_messages_enabled', False):
            return
        
        chance = ab.get('activity_messages_chance', 5)
        if random.randint(1, 100) > chance:
            return
        
        # Get message pool
        custom_messages = ab.get('activity_messages_list', [])
        default_messages = [
            "good luck please i'm dying here",
            "come onn just one shiny today",
            "pls arceus i'm begging",
            "send shiny luck i'm on my knees",
            "please please please hit me with something good",
            "manifesting shiny rn come onnn",
            "my luck is so bad today",
            "pls just one good catch",
            "hoping for something decent",
            "come onnn just one shiny",
        ]
        
        message_pool = custom_messages if custom_messages else default_messages
        msg = random.choice(message_pool)
        
        # Wait a bit before sending (looks more natural)
        await asyncio.sleep(random.uniform(1.5, 4.0))
        
        self.log(f"Activity Message: Sending '{msg}'")
        print(f"{Fore.MAGENTA}  [Activity] Sending: {msg}{Style.RESET_ALL}")
        
        # Send the message
        await self.send_command(channel, msg)
    
    def handle_activity_messages_list(self):
        """Manage the list of activity messages"""
        while True:
            self.clear_screen()
            ab = self.config.get('anti_ban', {})
            messages = ab.get('activity_messages_list', [])
            
            print(f"\n{Fore.CYAN}+=============================================+{Style.RESET_ALL}")
            print(f"{Fore.CYAN}|    Manage Activity Messages                 |{Style.RESET_ALL}")
            print(f"{Fore.CYAN}+=============================================+{Style.RESET_ALL}\n")
            
            if not messages:
                print(f"           {Fore.YELLOW}No custom messages. Using defaults.{Style.RESET_ALL}\n")
                print(f"           {Fore.YELLOW}Default messages:{Style.RESET_ALL}")
                defaults = [
                    "good luck please i'm dying here",
                    "come onn just one shiny today",
                    "pls arceus i'm begging",
                    "send shiny luck i'm on my knees",
                    "please please please hit me with something good",
                ]
                for i, msg in enumerate(defaults[:5], 1):
                    print(f"           {i}. {msg}")
                print()
            else:
                print(f"           {Fore.YELLOW}Custom Messages ({len(messages)}):{Style.RESET_ALL}")
                for i, msg in enumerate(messages, 1):
                    msg_preview = msg[:40] + "..." if len(msg) > 40 else msg
                    print(f"           [{i}] {msg_preview}")
                print()
            
            print(f"           [A] Add Message")
            print(f"           [D] Delete Message")
            print(f"           [C] Clear All Custom Messages")
            print(f"\n           [0] Back")
            
            choice = input(f"\n           {Fore.CYAN}Choose an option: {Style.RESET_ALL}").strip().lower()
            
            if choice == 'a':
                print(f"\n           {Fore.CYAN}Enter activity message:{Style.RESET_ALL}")
                msg = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                if msg:
                    if messages is None:
                        messages = []
                    messages.append(msg)
                    ab['activity_messages_list'] = messages
                    self.config['anti_ban'] = ab
                    self.save_config()
                    print(f"           {Fore.GREEN}Message added!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == 'd':
                if messages:
                    print(f"\n           {Fore.CYAN}Enter message number to delete (1-{len(messages)}):{Style.RESET_ALL}")
                    try:
                        idx = int(input(f"           {Fore.CYAN}> {Style.RESET_ALL}")) - 1
                        if 0 <= idx < len(messages):
                            removed = messages.pop(idx)
                            ab['activity_messages_list'] = messages
                            self.config['anti_ban'] = ab
                            self.save_config()
                            print(f"           {Fore.GREEN}Message deleted!{Style.RESET_ALL}")
                        else:
                            print(f"           {Fore.RED}Invalid number.{Style.RESET_ALL}")
                    except ValueError:
                        print(f"           {Fore.RED}Invalid input.{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.YELLOW}No messages to delete.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == 'c':
                if messages:
                    confirm = input(f"           {Fore.RED}Clear all custom messages? (y/n): {Style.RESET_ALL}").lower()
                    if confirm == 'y':
                        ab['activity_messages_list'] = []
                        self.config['anti_ban'] = ab
                        self.save_config()
                        print(f"           {Fore.GREEN}All messages cleared!{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.YELLOW}No custom messages to clear.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '0':
                break
    
    def handle_custom_message_config(self):
        """Handler for Custom Message configuration"""
        while True:
            self.clear_screen()
            cm = self.config.get('custom_message', {'enabled': False, 'message': '', 'chance': 50, 'command': 'p_only', 'p_chance': 50})
            
            print(f"\n{Fore.CYAN}+=============================================+{Style.RESET_ALL}")
            print(f"{Fore.CYAN}|          Custom Message Settings            |{Style.RESET_ALL}")
            print(f"{Fore.CYAN}+=============================================+{Style.RESET_ALL}\n")
            
            st = f"{Fore.GREEN}ON{Style.RESET_ALL}" if cm.get('enabled', False) else f"{Fore.RED}OFF{Style.RESET_ALL}"
            cm_mode = cm.get('command', 'p_only')
            cm_p_chance = cm.get('p_chance', 50)
            if cm_mode == 'p_only':
                cm_mode_label = f'{Fore.CYAN};p only{Style.RESET_ALL}'
            elif cm_mode == 'find_only':
                cm_mode_label = f'{Fore.CYAN};find only{Style.RESET_ALL}'
            else:
                cm_mode_label = f"{Fore.CYAN}Both random ({cm_p_chance}% ;p / {100 - cm_p_chance}% ;find){Style.RESET_ALL}"
            cm_msg_display = cm.get('message', '') or '(not set)'
            
            print(f"           [1] Toggle Custom Message: {st}")
            print(f"           [2] Set Message:  {Fore.CYAN}{cm_msg_display}{Style.RESET_ALL}")
            print(f"           [3] Set Chance:   {Fore.YELLOW}{cm.get('chance', 50)}%{Style.RESET_ALL} (chance to use custom message)")
            print(f"           [4] Set Command:  {cm_mode_label}")
            print(f"\n           [0] Back")
            
            preview_cmd = ';p' if cm_mode == 'p_only' else (';find' if cm_mode == 'find_only' else ';p or ;find')
            print(f"\n           {Fore.YELLOW}Info: {cm.get('chance', 50)}% chance to send '{preview_cmd} {cm.get('message', 'msg')}'{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}Command choice is independent from the normal spawn command.{Style.RESET_ALL}")
            
            choice = input(f"\n           {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            if choice == '1':
                cm['enabled'] = not cm.get('enabled', False)
                self.config['custom_message'] = cm
                self.save_config()
                status_str = "enabled" if cm['enabled'] else "disabled"
                print(f"           {Fore.GREEN}Custom Message {status_str}!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '2':
                print(f"\n           {Fore.CYAN}Enter your custom message:{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}(Appended after ;p or ;find, e.g. ';p hello'){Style.RESET_ALL}")
                msg = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                cm['message'] = msg
                self.config['custom_message'] = cm
                self.save_config()
                print(f"           {Fore.GREEN}Message saved!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '3':
                print(f"\n           {Fore.CYAN}Enter chance percentage (1-100):{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {cm.get('chance', 50)}%{Style.RESET_ALL}")
                try:
                    chance = int(input(f"           {Fore.CYAN}> {Style.RESET_ALL}"))
                    if 1 <= chance <= 100:
                        cm['chance'] = chance
                        self.config['custom_message'] = cm
                        self.save_config()
                        print(f"           {Fore.GREEN}Chance set to {chance}%!{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.RED}Invalid! Must be 1-100.{Style.RESET_ALL}")
                except ValueError:
                    print(f"           {Fore.RED}Invalid input! Enter a number.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '4':
                print(f"\n           {Fore.CYAN}Which command to use for custom messages?{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}(Independent from normal spawn command setting){Style.RESET_ALL}")
                print(f"\n           [1] ;p only")
                print(f"           [2] ;find only")
                print(f"           [3] Both random (set % for ;p vs ;find)")
                sc = input(f"\n           {Fore.CYAN}Choose: {Style.RESET_ALL}").strip()
                if sc == '1':
                    cm['command'] = 'p_only'
                    self.config['custom_message'] = cm
                    self.save_config()
                    print(f"           {Fore.GREEN}Custom message command set to ;p only!{Style.RESET_ALL}")
                elif sc == '2':
                    cm['command'] = 'find_only'
                    self.config['custom_message'] = cm
                    self.save_config()
                    print(f"           {Fore.GREEN}Custom message command set to ;find only!{Style.RESET_ALL}")
                elif sc == '3':
                    try:
                        v = int(input(f"           {Fore.CYAN}Chance for ;p in % (1-99): {Style.RESET_ALL}"))
                        if 1 <= v <= 99:
                            cm['command'] = 'both_random'
                            cm['p_chance'] = v
                            self.config['custom_message'] = cm
                            self.save_config()
                            print(f"           {Fore.GREEN}Set to Both random ({v}% ;p / {100-v}% ;find)!{Style.RESET_ALL}")
                        else:
                            print(f"           {Fore.RED}Invalid! Must be 1-99.{Style.RESET_ALL}")
                    except ValueError:
                        print(f"           {Fore.RED}Invalid input! Enter a number.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '0':
                break
    
    def handle_custom_message_fish_config(self):
        """Handler for Custom Message (Fish) configuration"""
        while True:
            self.clear_screen()
            cmf = self.config.get('custom_message_fish', {'enabled': False, 'message': '', 'chance': 50})
            
            print(f"\n{Fore.CYAN}+=============================================+{Style.RESET_ALL}")
            print(f"{Fore.CYAN}|       Custom Message (;fish) Settings       |{Style.RESET_ALL}")
            print(f"{Fore.CYAN}+=============================================+{Style.RESET_ALL}\n")
            
            st = f"{Fore.GREEN}ON{Style.RESET_ALL}" if cmf.get('enabled', False) else f"{Fore.RED}OFF{Style.RESET_ALL}"
            cmf_msg_display = cmf.get('message', '') or '(not set)'
            
            print(f"           [1] Toggle Custom Fish Message: {st}")
            print(f"           [2] Set Message:  {Fore.CYAN}{cmf_msg_display}{Style.RESET_ALL}")
            print(f"           [3] Set Chance:   {Fore.YELLOW}{cmf.get('chance', 50)}%{Style.RESET_ALL} (chance to use custom message)")
            print(f"\n           [0] Back")
            
            print(f"\n           {Fore.YELLOW}Info: {cmf.get('chance', 50)}% chance to send ';f {cmf.get('message', 'msg')}'{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}Separate from ;p custom message settings.{Style.RESET_ALL}")
            
            choice = input(f"\n           {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            if choice == '1':
                cmf['enabled'] = not cmf.get('enabled', False)
                self.config['custom_message_fish'] = cmf
                self.save_config()
                status_str = "enabled" if cmf['enabled'] else "disabled"
                print(f"           {Fore.GREEN}Custom Fish Message {status_str}!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '2':
                print(f"\n           {Fore.CYAN}Enter your custom fish message:{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}(Appended after ;f, e.g. ';f hello'){Style.RESET_ALL}")
                msg = input(f"           {Fore.CYAN}> {Style.RESET_ALL}").strip()
                cmf['message'] = msg
                self.config['custom_message_fish'] = cmf
                self.save_config()
                print(f"           {Fore.GREEN}Fish message saved!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '3':
                print(f"\n           {Fore.CYAN}Enter chance percentage (1-100):{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {cmf.get('chance', 50)}%{Style.RESET_ALL}")
                try:
                    chance = int(input(f"           {Fore.CYAN}> {Style.RESET_ALL}"))
                    if 1 <= chance <= 100:
                        cmf['chance'] = chance
                        self.config['custom_message_fish'] = cmf
                        self.save_config()
                        print(f"           {Fore.GREEN}Chance set to {chance}%!{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.RED}Invalid! Must be 1-100.{Style.RESET_ALL}")
                except ValueError:
                    print(f"           {Fore.RED}Invalid input! Enter a number.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice == '0':
                break
    
