"""CaptchaDetectionMixin: captcha detection + alert sounds + auto-solve orchestration."""
import os
import sys
import re
import asyncio
import random
import threading
import base64
import time as time_module
from datetime import datetime, timedelta
from io import BytesIO
from colorama import Fore, Style

import discord

from utils.platform import (
    CATCHBOT_VERSION,
    HAS_TOAST,
    HAS_PLYER,
    WINDOWS,
    _show_windows_toast,
    _generate_alarm_wav,
)

try:
    import requests
except ImportError:
    pass

try:
    import winsound
except ImportError:
    winsound = None


class CaptchaDetectionMixin:
    async def check_captcha(self, message):
        """Checks if a captcha message is present or has been solved"""
        all_text = ""
        
        # Text aus Embeds (inkl. fields, footer)
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
        
        # Text aus Nachricht
        if message.content:
            all_text += message.content.lower()
        
        # Captcha solved? (Check first, because on Edit the old message gets modified)
        if self.captcha_active:
            # Check for temp ban FIRST (even while captcha is active)
            # PokeMeow may send the ban message while captcha_active is True
            if 'you have been temporarily banned' in all_text or 'temporarily banned for' in all_text:
                self.temp_banned = True
                self.captcha_active = False
                self.captcha_solve_attempts = 0
                self.captcha_last_message = None
                self.log(f"🚫 TEMPORARILY BANNED! Captcha could not be solved!")
                print(f"\n{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
                print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██████████████████████████████████████████████████████████████{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██   TEMPORARILY BANNED!                                  ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██   Captcha could not be solved.                         ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██   Bot is COMPLETELY paused.                            ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██   Wait until the ban has expired,                      ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██   then press [P] to continue.                          ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
                print(f"{Fore.RED}  ██████████████████████████████████████████████████████████████{Style.RESET_ALL}")
                print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
                print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}\n")
                
                # Desktop-Notification
                if self.config.get('notification_enabled', True):
                    try:
                        _show_windows_toast(
                            '🚫 CatchBot - TEMPORARILY BANNED!',
                            'Captcha could not be solved! Bot is paused.',
                            timeout=60
                        )
                    except Exception:
                        pass
                
                # Alarm-Sound (5x soft beeps)
                if WINDOWS and self.config.get('sound_enabled', True):
                    def ban_alert():
                        try:
                            volume = self.config.get('alarm_volume', 33)
                            for _ in range(5):
                                wav_data = _generate_alarm_wav(volume=volume, frequency=900, duration_ms=250)
                                winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                                time_module.sleep(0.1)
                            wav_data = _generate_alarm_wav(volume=volume, frequency=500, duration_ms=700)
                            winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                        except Exception:
                            pass
                    threading.Thread(target=ban_alert, daemon=True).start()
                return
            
            # Check if message is from PokeMeow (ID: 664508672713424926) to avoid false positives
            # Also check for bot flag in case user ID changes (it's an App)
            is_from_pokemeow = message.author.id == 664508672713424926 or (message.author.bot and 'pokemeow' in message.author.name.lower())
            # Exact message from PokeMeow: "Thank you, you may continue playing!"
            is_captcha_solved = 'thank you, you may continue playing' in all_text.lower()
            
            if is_from_pokemeow and is_captcha_solved:
                self.captcha_active = False
                attempts_used = self.captcha_solve_attempts
                self.captcha_solve_attempts = 0
                self.captcha_last_message = None
                service_name = self.get_captcha_service_name()
                
                # === REPORT CORRECT an den Captcha-Service ===
                task_id = getattr(self, '_last_captcha_task_id', None)
                svc = getattr(self, '_last_captcha_service', None)
                if task_id and svc:
                    if svc == '2captcha':
                        threading.Thread(target=self.report_2captcha, args=(task_id, True), daemon=True).start()
                    elif svc == 'anticaptcha':
                        threading.Thread(target=self.report_anticaptcha, args=(task_id, True), daemon=True).start()
                    self._last_captcha_task_id = None
                    self._last_captcha_service = None
                # Track captcha attempts in session_stats AND persistent_stats
                if attempts_used > 0:
                    # Session stats
                    if 'captcha_attempts' not in self.session_stats:
                        self.session_stats['captcha_attempts'] = {}
                    attempt_key = attempts_used
                    self.session_stats['captcha_attempts'][attempt_key] = self.session_stats['captcha_attempts'].get(attempt_key, 0) + 1
                    
                    # Lifetime/persistent stats
                    if 'captcha_attempts' not in self.persistent_stats:
                        self.persistent_stats['captcha_attempts'] = {}
                    self.persistent_stats['captcha_attempts'][str(attempt_key)] = self.persistent_stats['captcha_attempts'].get(str(attempt_key), 0) + 1
                    self.persistent_stats['total_captchas_solved'] = self.persistent_stats.get('total_captchas_solved', 0) + 1
                    self.save_persistent_stats()
                    
                    self.log(f"✅ CAPTCHA SOLVED by {service_name}! (Attempt {attempts_used}) Bot continues.")
                else:
                    self.log(f"✅ CAPTCHA SOLVED! Bot continues.")
                print(f"\n{Fore.GREEN}{'═' * 66}{Style.RESET_ALL}")
                print(f"{Fore.GREEN}  ✅  Captcha solved! Bot continues!{Style.RESET_ALL}")
                if attempts_used > 0:
                    print(f"{Fore.GREEN}  🤖  Solved by {service_name} (Attempt {attempts_used}){Style.RESET_ALL}")
                print(f"{Fore.GREEN}{'═' * 66}{Style.RESET_ALL}\n")
                
                # Short confirmation sound (soft)
                if WINDOWS and self.config.get('sound_enabled', True):
                    def _solved_beep():
                        try:
                            volume = self.config.get('alarm_volume', 33)
                            wav_data = _generate_alarm_wav(volume=volume, frequency=600, duration_ms=250)
                            winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                        except Exception:
                            pass
                    threading.Thread(target=_solved_beep, daemon=True).start()
                
                return
            
            # Wrong answer detected? -> Reset collector + Retry if Auto-Solve active
            if ('incorrect' in all_text or 'wrong' in all_text or 'try again' in all_text):
                
                if self.captcha_solve_attempts > 0:
                    # === REPORT INCORRECT an den Captcha-Service ===
                    task_id = getattr(self, '_last_captcha_task_id', None)
                    svc = getattr(self, '_last_captcha_service', None)
                    if task_id and svc:
                        if svc == '2captcha':
                            threading.Thread(target=self.report_2captcha, args=(task_id, False), daemon=True).start()
                        elif svc == 'anticaptcha':
                            threading.Thread(target=self.report_anticaptcha, args=(task_id, False), daemon=True).start()
                        self._last_captcha_task_id = None
                        self._last_captcha_service = None
                    max_retries = self.config.get('captcha_max_retries', 5)
                    service_name = self.get_captcha_service_name()
                    
                    if self.captcha_solve_attempts < max_retries:
                        self.log(f"❌ Captcha answer wrong! Retry {self.captcha_solve_attempts}/{max_retries}...")
                        print(f"\n{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ❌ Wrong answer! Retrying ({self.captcha_solve_attempts}/{max_retries})...{Style.RESET_ALL}")
                        
                        # PokeMeow edits the same message with a NEW captcha image.
                        # We must use the CURRENT edited message (not the old cached one)
                        # and wait a moment for PokeMeow to fully update the embed.
                        self.captcha_last_message = message
                        
                        async def retry_with_fresh_message():
                            await asyncio.sleep(3)  # Wait for PokeMeow to update embed with new image
                            try:
                                # Re-fetch the message from Discord to get the absolute latest version
                                fresh_msg = await message.channel.fetch_message(message.id)
                                self.captcha_last_message = fresh_msg
                                self.log(f"🔄 Re-fetched message for retry (embeds: {len(fresh_msg.embeds)})")
                            except Exception as e:
                                self.log(f"⚠️ Could not re-fetch message: {e}, using current version")
                                fresh_msg = message
                            asyncio.create_task(self.auto_solve_captcha(fresh_msg))
                        
                        asyncio.create_task(retry_with_fresh_message())
                        return
                    else:
                        self.captcha_solve_attempts = 0
                        self.captcha_last_message = None
                        self.log(f"❌ All {max_retries} attempts failed! Solve manually!")
                        print(f"\n{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
                        print(f"{Fore.RED}  ❌  All {max_retries} auto-solve attempts failed!{Style.RESET_ALL}")
                        print(f"{Fore.RED}  ➜  Solve the captcha MANUALLY in Discord!{Style.RESET_ALL}")
                        print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}\n")
                        
                        # Play alarm again to get attention
                        threading.Thread(target=self.play_captcha_alert, daemon=True).start()
                        return
                return
        
        # Temporarily banned? (Captcha not solved in time / too many wrong answers)
        if 'you have been temporarily banned' in all_text or 'temporarily banned for' in all_text:
            self.temp_banned = True
            self.captcha_active = False
            self.captcha_solve_attempts = 0
            self.captcha_last_message = None
            self.log(f"🚫 TEMPORARILY BANNED! Captcha could not be solved!")
            print(f"\n{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
            print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
            print(f"{Fore.RED}  ████████████████████████████████████████████████████████████{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   TEMPORARILY BANNED!                                  ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   Captcha could not be solved.                         ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   Bot is COMPLETELY paused.                            ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   Wait until the ban has expired,                      ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██   then press [P] to continue.                          ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ██                                                        ██{Style.RESET_ALL}")
            print(f"{Fore.RED}  ████████████████████████████████████████████████████████████{Style.RESET_ALL}")
            print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
            print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}\n")
            
            # Desktop-Notification (native toast - works in .exe)
            if self.config.get('notification_enabled', True):
                try:
                    _show_windows_toast(
                        '⚠️ CatchBot - TEMPORARILY BANNED!',
                        'Captcha could not be solved! Bot is paused.',
                        timeout=60
                    )
                except Exception:
                    pass
            
            # Alarm-Sound (5x soft beeps)
            if WINDOWS and self.config.get('sound_enabled', True):
                def ban_alert():
                    try:
                        volume = self.config.get('alarm_volume', 33)
                        for _ in range(5):
                            wav_data = _generate_alarm_wav(volume=volume, frequency=900, duration_ms=250)
                            winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                            time_module.sleep(0.1)
                        wav_data = _generate_alarm_wav(volume=volume, frequency=500, duration_ms=700)
                        winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                    except Exception:
                        pass
                threading.Thread(target=ban_alert, daemon=True).start()
            return
        
        # Captcha detected? (Only if not already active)
        if not self.captcha_active and 'a wild captcha appeared' in all_text:
            self.captcha_active = True
            self.captcha_solve_attempts = 0
            self.captcha_last_message = message
            self.captcha_detected_at = datetime.now()
            self.captcha_timeout_triggered = False
            
            # Start 70-second timeout timer (alarm + stop auto-solve if still unsolved)
            asyncio.create_task(self.captcha_timeout_watchdog())
            
            # Check if Auto-Solve is enabled
            max_retries = self.config.get('captcha_max_retries', 5)
            service = self.config.get('captcha_service', 'manual')
            service_name = self.get_captcha_service_name()
            has_api_key = self.get_active_captcha_api_key() != ''
            
            if self.config.get('auto_solve_captcha', False) and service != 'manual' and has_api_key:
                self.log(f"⚠️ CAPTCHA DETECTED! Auto-Solve with {service_name} starting (max {max_retries} attempts)...")
                print(f"\n{Fore.YELLOW}{'!' * 66}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}  ⚠️  CAPTCHA DETECTED! Auto-Solve active...{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}  🤖  {service_name} solving automatically (max {max_retries}x){Style.RESET_ALL}")
                print(f"{Fore.YELLOW}{'!' * 66}{Style.RESET_ALL}\n")
                
                # Auto-Solve starten (async)
                asyncio.create_task(self.auto_solve_captcha(message))
            else:
                self.log(f"⚠️ CAPTCHA DETECTED! Bot paused. Solve the captcha manually!")
                print(f"\n{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
                print(f"{Fore.RED}  ⚠️  CAPTCHA DETECTED! Bot is paused!{Style.RESET_ALL}")
                print(f"{Fore.RED}  ➜  Solve the captcha manually in Discord!{Style.RESET_ALL}")
                print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}\n")
            
            # Sound + Notification (in Thread damit es nicht blockiert)
            threading.Thread(target=self.play_captcha_alert, daemon=True).start()
    
    def play_captcha_alert(self):
        """Plays a captcha alarm sound and shows native desktop notification (works in .exe).
        Sound repeats configurable via alarm_repeat (default 1)."""
        # Desktop notification (native Windows toast - works in Nuitka .exe)
        if self.config.get('notification_enabled', True):
            try:
                _show_windows_toast(
                    '⚠ CatchBot - CAPTCHA!',
                    'A captcha has appeared! Solve it manually in Discord.',
                    timeout=30
                )
            except Exception as e:
                self.log(f"Notification Error: {str(e)}")
        
        # Captcha alarm: urgent ascending tone pattern, repeated alarm_repeat times
        if WINDOWS and self.config.get('sound_enabled', True):
            try:
                volume = self.config.get('alarm_volume', 33)
                repeats = self.config.get('alarm_repeat', 1)
                for _ in range(repeats):
                    # Ascending urgent beep pattern: 600 -> 800 -> 1000 Hz
                    for freq in [600, 800, 1000]:
                        wav_data = _generate_alarm_wav(volume=volume, frequency=freq, duration_ms=300)
                        winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                        time_module.sleep(0.1)
                    time_module.sleep(0.3)
            except Exception:
                pass
    
    # ═════════════════════════════════════════════════════════════════
    #  DAILY CATCH LIMIT ERKENNUNG
    # ═════════════════════════════════════════════════════════════════
    
    async def captcha_timeout_watchdog(self):
        """Waits 70 seconds after captcha detection. If still unsolved, triggers alarm + notification
        and stops auto-solve so the user can solve it manually."""
        await asyncio.sleep(70)  # 1 minute 10 seconds
        
        if not self.captcha_active:
            return  # Captcha was already solved, nothing to do
        
        self.captcha_timeout_triggered = True
        self.log("CAPTCHA TIMEOUT! 70 seconds passed, captcha still unsolved!")
        
        print(f"\n{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
        print(f"{Fore.RED}  CAPTCHA TIMEOUT! Auto-Solve taking too long!{Style.RESET_ALL}")
        print(f"{Fore.RED}  Auto-Solve stopped. Solve the captcha MANUALLY in Discord!{Style.RESET_ALL}")
        print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}\n")
        
        # Reset auto-solve attempts so it stops retrying
        self.captcha_solve_attempts = self.config.get('captcha_max_retries', 3) + 999
        
        # Cancel/report the pending captcha task so we don't get charged for a late result
        task_id = getattr(self, '_last_captcha_task_id', None)
        service = getattr(self, '_last_captcha_service', None)
        if task_id:
            self.log(f"Cancelling pending captcha task {task_id} on {service}...")
            if service == '2captcha':
                threading.Thread(target=self.report_2captcha, args=(task_id, False), daemon=True).start()
            elif service == 'anticaptcha':
                threading.Thread(target=self.report_anticaptcha, args=(task_id, False), daemon=True).start()
            self._last_captcha_task_id = None
            print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] Pending captcha task reported as incorrect (cancel){Style.RESET_ALL}")
        
        # Fire alarm + desktop notification with timeout-specific message
        threading.Thread(target=self.play_captcha_timeout_alert, daemon=True).start()
    
    def play_captcha_timeout_alert(self):
        """Plays alarm and shows timeout-specific desktop notification."""
        if self.config.get('notification_enabled', True):
            try:
                _show_windows_toast(
                    'CatchBot - CAPTCHA TIMEOUT!',
                    'Solve Captcha manually, Auto-Solver takes too long!',
                    timeout=60
                )
            except Exception as e:
                self.log(f"Notification Error: {str(e)}")
        
        if WINDOWS and self.config.get('sound_enabled', True):
            try:
                volume = self.config.get('alarm_volume', 33)
                repeats = self.config.get('alarm_repeat', 1) + 1
                for _ in range(repeats):
                    for freq in [600, 800, 1000]:
                        wav_data = _generate_alarm_wav(volume=volume, frequency=freq, duration_ms=300)
                        winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                        time_module.sleep(0.1)
                    time_module.sleep(0.3)
            except Exception:
                pass
    
    # ═════════════════════════════════════════════════════════════════
    async def download_captcha_image_from_message(self, message):
        """Downloads captcha image from a message (embed or attachment). Returns raw bytes or None."""
        # Try embeds first
        if message.embeds:
            for embed in message.embeds:
                image_url = None
                if embed.image and embed.image.url:
                    image_url = embed.image.url
                elif embed.thumbnail and embed.thumbnail.url:
                    image_url = embed.thumbnail.url
                if not image_url:
                    embed_dict = embed.to_dict()
                    if 'image' in embed_dict and 'url' in embed_dict['image']:
                        image_url = embed_dict['image']['url']
                    elif 'thumbnail' in embed_dict and 'url' in embed_dict['thumbnail']:
                        image_url = embed_dict['thumbnail']['url']
                
                if image_url:
                    try:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            headers_auth = {'Authorization': self.config.get('token', '')}
                            async with session.get(image_url, headers=headers_auth, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                                if resp.status == 200:
                                    data = await resp.read()
                                    if len(data) > 100:
                                        return data
                    except Exception:
                        pass
                    try:
                        import aiohttp
                        async with aiohttp.ClientSession() as session:
                            async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                                if resp.status == 200:
                                    data = await resp.read()
                                    if len(data) > 100:
                                        return data
                    except Exception:
                        pass
        
        # Try attachments
        if message.attachments:
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                    try:
                        data = await attachment.read()
                        if len(data) > 100:
                            return data
                    except Exception:
                        pass
        return None
    
    async def auto_solve_captcha(self, message):
        """Versucht das Captcha automatisch über den konfigurierten Service zu lösen (mit Retry)"""
        if not self.config.get('auto_solve_captcha', False):
            return
        
        # === DEDUP +: prevent duplicate concurrent solve attempts ===
        # Can happen when on_message + on_message_edit both fire for the same
        # "incorrect response" event (Discord cache timing issue).
        if self._solving_captcha:
            self.log("auto_solve_captcha: already solving, ignoring duplicate trigger.")
            return
        self._solving_captcha = True
        
        service = self.config.get('captcha_service', 'manual')
        service_name = self.get_captcha_service_name()
        api_key = self.get_active_captcha_api_key()
        
        if service == 'manual' or not api_key:
            self.log(f"⚠️ Auto-Solve: No captcha service configured or no API key set!")
            print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ⚠️ No API key for {service_name}! Set it in the config.{Style.RESET_ALL}")
            return
        
        if service != 'catchbot_ai' and not HAS_REQUESTS:
            self.log("⚠⚠⚠ Auto-Solve: 'requests' not installed!")
            print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ⚠️ 'requests' not installed! py -m pip install requests{Style.RESET_ALL}")
            return
        
        # Abort if timeout watchdog already fired
        if self.captcha_timeout_triggered:
            self.log("Auto-Solve aborted: captcha timeout was triggered, solve manually!")
            return
        
        # Increase attempt counter
        self.captcha_solve_attempts += 1
        max_retries = self.config.get('captcha_max_retries', 5)
        attempt = self.captcha_solve_attempts
        self.captcha_last_message = message
        
        self.log(f"🔄 Auto-Solve Attempt {attempt}/{max_retries}")
        
        # Captcha-Bild aus der Nachricht extrahieren
        image_base64 = None
        
        # Methode 1: Bild aus Embed (thumbnail oder image)
        if message.embeds:
            for embed in message.embeds:
                # discord.py Embed hat .image und .thumbnail als Objekte
                image_url = None
                
                if embed.image and embed.image.url:
                    image_url = embed.image.url
                elif embed.thumbnail and embed.thumbnail.url:
                    image_url = embed.thumbnail.url
                
                if not image_url:
                    # Fallback: to_dict() fuer aeltere discord.py Versionen
                    embed_dict = embed.to_dict()
                    if 'image' in embed_dict and 'url' in embed_dict['image']:
                        image_url = embed_dict['image']['url']
                    elif 'thumbnail' in embed_dict and 'url' in embed_dict['thumbnail']:
                        image_url = embed_dict['thumbnail']['url']
                
                if image_url:
                    self.log(f"🖼️ Captcha image URL found: {image_url}")
                    print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] 🖼️ Captcha image found, downloading...{Style.RESET_ALL}")
                    
                    try:
                        # Versuche verschiedene Download-Methoden
                        img_data = None
                        
                        # Methode A: aiohttp mit Bot-Token (wie discord.py intern)
                        try:
                            import aiohttp
                            async with aiohttp.ClientSession() as session:
                                headers_auth = {'Authorization': self.config.get('token', '')}
                                async with session.get(image_url, headers=headers_auth, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                                    if resp.status == 200:
                                        img_data = await resp.read()
                                        self.log(f"🖼️ Downloaded via aiohttp+auth ({len(img_data)} Bytes)")
                        except Exception as e:
                            self.log(f"aiohttp+auth failed: {str(e)}")
                        
                        # Methode B: aiohttp ohne Auth
                        if not img_data or len(img_data) < 100:
                            try:
                                import aiohttp
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                                        if resp.status == 200:
                                            img_data = await resp.read()
                                            self.log(f"🖼️ Downloaded via aiohttp ({len(img_data)} Bytes)")
                            except Exception as e:
                                self.log(f"aiohttp failed: {str(e)}")
                        
                        # Methode C: requests als Fallback
                        if not img_data or len(img_data) < 100:
                            try:
                                img_response = requests.get(image_url, timeout=15)
                                if img_response.status_code == 200:
                                    img_data = img_response.content
                                    self.log(f"🖼️ Downloaded via requests ({len(img_data)} Bytes)")
                            except Exception as e:
                                self.log(f"requests failed: {str(e)}")
                        
                        if img_data and len(img_data) > 100:
                            # Sauberes base64 ohne Zeilenumbrueche oder Prefix
                            raw_b64 = base64.b64encode(img_data).decode('utf-8')
                            image_base64 = raw_b64.replace('\n', '').replace('\r', '')
                            # No data:image prefix - raw base64 string only
                            if image_base64.startswith('data:'):
                                image_base64 = image_base64.split(',', 1)[-1]
                            self.log(f"🖼️ Image ready ({len(img_data)} Bytes, base64: {len(image_base64)} chars)")
                            print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] 🖼️ Image downloaded ({len(img_data)} Bytes){Style.RESET_ALL}")
                        else:
                            size = len(img_data) if img_data else 0
                            self.log(f"❌ All download methods failed or image too small ({size} Bytes)")
                            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ Image download failed ({size} Bytes){Style.RESET_ALL}")
                    except Exception as e:
                        self.log(f"❌ Image download Error: {str(e)}")
                    break
        
        # Methode 2: Bild aus Attachments
        if not image_base64 and message.attachments:
            for attachment in message.attachments:
                if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                    self.log(f"🖼️ Captcha attachment found: {attachment.filename}")
                    print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] 🖼️ Captcha attachment found: {attachment.filename}{Style.RESET_ALL}")
                    
                    try:
                        # discord.py read() nutzt den Token automatisch
                        img_bytes = await attachment.read()
                        if len(img_bytes) > 100:
                            raw_b64 = base64.b64encode(img_bytes).decode('utf-8')
                            image_base64 = raw_b64.replace('\n', '').replace('\r', '')
                            self.log(f"🖼️ Attachment downloaded ({len(img_bytes)} Bytes)")
                            print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] 🖼️ Attachment downloaded ({len(img_bytes)} Bytes){Style.RESET_ALL}")
                        else:
                            self.log(f"❌ Attachment too small: {len(img_bytes)} Bytes")
                    except Exception as e:
                        self.log(f"❌ Attachment read Error: {str(e)}")
                        # Fallback: requests
                        try:
                            img_response = requests.get(attachment.url, timeout=15)
                            if img_response.status_code == 200 and len(img_response.content) > 100:
                                raw_b64 = base64.b64encode(img_response.content).decode('utf-8')
                                image_base64 = raw_b64.replace('\n', '').replace('\r', '')
                                self.log(f"🖼️ Attachment fallback downloaded ({len(img_response.content)} Bytes)")
                        except Exception as e2:
                            self.log(f"❌ Attachment fallback Error: {str(e2)}")
                    break
        
        # === RETRY DOWNLOAD if first attempt failed ===
        if not image_base64:
            max_download_retries = 3
            for dl_retry in range(1, max_download_retries + 1):
                self.log(f"🔄 Image download retry {dl_retry}/{max_download_retries}...")
                print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] 🔄 Image download retry {dl_retry}/{max_download_retries}...{Style.RESET_ALL}")
                await asyncio.sleep(2)  # Wait 2 seconds before retry
                
                # Re-try downloading from embeds
                if message.embeds:
                    for embed in message.embeds:
                        image_url = None
                        if embed.image and embed.image.url:
                            image_url = embed.image.url
                        elif embed.thumbnail and embed.thumbnail.url:
                            image_url = embed.thumbnail.url
                        if not image_url:
                            embed_dict = embed.to_dict()
                            if 'image' in embed_dict and 'url' in embed_dict['image']:
                                image_url = embed_dict['image']['url']
                            elif 'thumbnail' in embed_dict and 'url' in embed_dict['thumbnail']:
                                image_url = embed_dict['thumbnail']['url']
                        if image_url:
                            try:
                                import aiohttp
                                async with aiohttp.ClientSession() as session:
                                    async with session.get(image_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                                        if resp.status == 200:
                                            img_data = await resp.read()
                                            if img_data and len(img_data) > 100:
                                                raw_b64 = base64.b64encode(img_data).decode('utf-8')
                                                image_base64 = raw_b64.replace('\n', '').replace('\r', '')
                                                if image_base64.startswith('data:'):
                                                    image_base64 = image_base64.split(',', 1)[-1]
                                                self.log(f"🖼️ Retry {dl_retry} success! ({len(img_data)} Bytes)")
                                                print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] 🖼️ Retry {dl_retry} success! ({len(img_data)} Bytes){Style.RESET_ALL}")
                            except Exception as e:
                                self.log(f"Retry {dl_retry} failed: {str(e)}")
                            break
                
                # Re-try from attachments
                if not image_base64 and message.attachments:
                    for attachment in message.attachments:
                        if any(attachment.filename.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.gif']):
                            try:
                                img_bytes = await attachment.read()
                                if len(img_bytes) > 100:
                                    raw_b64 = base64.b64encode(img_bytes).decode('utf-8')
                                    image_base64 = raw_b64.replace('\n', '').replace('\r', '')
                                    self.log(f"🖼️ Retry {dl_retry} attachment success! ({len(img_bytes)} Bytes)")
                                    print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] 🖼️ Retry {dl_retry} attachment success! ({len(img_bytes)} Bytes){Style.RESET_ALL}")
                            except Exception:
                                pass
                            break
                
                if image_base64:
                    break  # Download succeeded on retry
        
        # === ALL DOWNLOAD ATTEMPTS FAILED → ALARM ===
        if not image_base64:
            self.log("❌ Auto-Solve: All image download attempts failed! Playing alarm...")
            print(f"\n{Fore.RED}{'!' * 66}{Style.RESET_ALL}")
            print(f"{Fore.RED}  ⚠️  CAPTCHA IMAGE DOWNLOAD FAILED!{Style.RESET_ALL}")
            print(f"{Fore.RED}  ⚠️  Could not download captcha image after {max_download_retries} retries.{Style.RESET_ALL}")
            print(f"{Fore.RED}  ⚠️  Solve the captcha MANUALLY in Discord!{Style.RESET_ALL}")
            print(f"{Fore.RED}{'!' * 66}{Style.RESET_ALL}\n")
            # Play alarm + notification so user notices
            self.play_captcha_alert()
            return
        
        # Captcha lösen (in Thread um Event-Loop nicht zu blockieren)
        service_name = self.get_captcha_service_name()
        print(f"\n{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}  🤖  {service_name} Auto-Solve Attempt {attempt}/{max_retries}...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'═' * 66}{Style.RESET_ALL}\n")
        
        loop = asyncio.get_running_loop()
        
        # Je nach Service den richtigen Solver aufrufen
        # Alle Solver geben (solution, task_id) zurueck
        if service == 'catchbot_ai':
            # CatchBot AI: solve + delay in parallel (solve during wait time)
            delay_min = self.config.get('catchbot_ai_delay_min', 7)
            delay_max = self.config.get('catchbot_ai_delay_max', 15)
            delay = random.uniform(delay_min, delay_max)
            print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] CatchBot AI: Solving + waiting {delay:.1f}s in parallel...{Style.RESET_ALL}")
            # Run both concurrently: solve in background thread + delay timer
            solve_task = loop.run_in_executor(None, self.solve_captcha_with_ai, image_base64)
            delay_task = asyncio.sleep(delay)
            (solution, task_id), _ = await asyncio.gather(solve_task, delay_task)
            # Check if captcha was already solved during the delay (manual solve)
            if not self.captcha_active:
                self.log("CatchBot AI: Captcha already solved during delay, skipping.")
                self._solving_captcha = False  # Reset the lock to allow future attempts
                return
        elif service == 'anticaptcha':
            solution, task_id = await loop.run_in_executor(None, self.solve_captcha_with_anticaptcha, image_base64)
        else:
            solution, task_id = await loop.run_in_executor(None, self.solve_captcha_with_2captcha, image_base64)
        
        # Task-ID merken fuer reportCorrect/reportIncorrect
        self._last_captcha_task_id = task_id
        self._last_captcha_service = service
        
        if solution:
            # Lösung in den Channel senden
            self.log(f"📝 Sending captcha solution (Attempt {attempt}/{max_retries}): '{solution}'")
            print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] 📝 Sending solution (Attempt {attempt}/{max_retries}): '{solution}'{Style.RESET_ALL}")
            
            try:
                channel = message.channel
                await channel.send(solution)
                self._solving_captcha = False  # Reset so check_captcha retry logic can re-trigger if needed
                self.log(f"✅ Captcha solution '{solution}' sent! Waiting for confirmation...")
                print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ✅ Solution sent! Waiting for confirmation...{Style.RESET_ALL}")
            except Exception as e:
                self.log(f"❌ Error sending solution: {str(e)}")
                print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ Error sending: {str(e)}{Style.RESET_ALL}")
        else:
            # Service konnte nicht lösen (API-Fehler/Timeout)
            if attempt < max_retries:
                self.log(f"❌ {service_name} Attempt {attempt} failed, retrying...")
                print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ❌ Attempt {attempt} failed, starting retry...{Style.RESET_ALL}")
                # Direkt erneut versuchen bei API-Fehler
                await asyncio.sleep(2)
                self._solving_captcha = False  # Reset so retry task can proceed
                asyncio.create_task(self.auto_solve_captcha(message))
            else:
                self.captcha_solve_attempts = 0
                self.captcha_last_message = None
                self._solving_captcha = False
                self.log(f"❌ All {max_retries} attempts failed! Solve manually!")
                print(f"\n{Fore.RED}{'═' * 66}{Style.RESET_ALL}")
                print(f"{Fore.RED}  ❌  All {max_retries} auto-solve attempts failed!{Style.RESET_ALL}")
                print(f"{Fore.RED}  ➜  Solve the captcha MANUALLY in Discord!{Style.RESET_ALL}")
                print(f"{Fore.RED}{'═' * 66}{Style.RESET_ALL}\n")
                
                threading.Thread(target=self.play_captcha_alert, daemon=True).start()
    
    # ═════════════════════════════════════════════════════════════════
    #  EGG SYSTEM
    # ═════════════════════════════════════════════════════════════════
    
