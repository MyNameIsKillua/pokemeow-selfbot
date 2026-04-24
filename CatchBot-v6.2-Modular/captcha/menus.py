"""CaptchaMenuMixin: show_captcha_menu, handle_captcha_config."""
import os
import sys
import threading
import time as time_module
from colorama import Fore, Style

from utils.platform import WINDOWS, _generate_alarm_wav

try:
    import winsound
except ImportError:
    winsound = None


class CaptchaMenuMixin:
    def show_captcha_menu(self):
        """Shows the Captcha configuration menu (foldable sub-menu like AutoBuyer)"""
        self.print_header()
        
        def status(on):
            return f"{Fore.GREEN}[ON]{Style.RESET_ALL}" if on else f"{Fore.RED}[OFF]{Style.RESET_ALL}"
        
        service_name = self.get_captcha_service_name()
        auto_solve_on = self.config.get('auto_solve_captcha', False)
        
        print(f"\n{Fore.CYAN}{'=' * 20} CAPTCHA SETTINGS {'=' * 20}{Style.RESET_ALL}")
        
        print(f"\n           {Fore.YELLOW}--- Notifications ---{Style.RESET_ALL}")
        print(f"           [N] {status(self.config.get('notification_enabled', True))} Desktop-Notification")
        print(f"           [S] {status(self.config.get('sound_enabled', True))} Sound-Alarm")
        vol = self.config.get('alarm_volume', 33)
        print(f"           [L] Alarm Volume: {vol}%")
        rep = self.config.get('alarm_repeat', 1)
        print(f"           [J] Alarm Repeat: {rep}x")
        
        print(f"\n           {Fore.YELLOW}--- Auto-Solve ---{Style.RESET_ALL}")
        print(f"           [D] Captcha Service: {Fore.CYAN}{service_name}{Style.RESET_ALL}")
        print(f"           [A] {status(auto_solve_on)} Auto-Solve ({service_name})")
        print(f"           [C] Set 2Captcha API Key")
        print(f"           [K] Set Anti-Captcha API Key")
        print(f"           [R] Max Retries: {self.config.get('captcha_max_retries', 3)}x")
        print(f"           [G] Check Captcha Balance")
        
        # CatchBot AI specific settings (only show when CatchBot AI is selected)
        service = self.config.get('captcha_service', 'manual')
        if service == 'catchbot_ai':
            tta_on = self.config.get('catchbot_ai_tta', False)
            delay_min = self.config.get('catchbot_ai_delay_min', 7)
            delay_max = self.config.get('catchbot_ai_delay_max', 15)
            print(f"\n           {Fore.YELLOW}--- CatchBot AI Settings ---{Style.RESET_ALL}")
            print(f"           [T] {status(tta_on)} TTA (Test-Time Augmentation)")
            print(f"           [W] Answer Delay: {delay_min}-{delay_max}s")
            
            # Check if model exists (unencrypted or encrypted)
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            model_path = os.path.join(script_dir, 'catchbot_model_onnx')
            encrypted_path = os.path.join(script_dir, 'catchbot_model_onnx_encrypted')
            if os.path.exists(model_path):
                print(f"           {Fore.GREEN}Model: Found (unencrypted){Style.RESET_ALL}")
            elif os.path.exists(encrypted_path):
                print(f"           {Fore.GREEN}Model: Found (encrypted){Style.RESET_ALL}")
            else:
                print(f"           {Fore.RED}Model: NOT FOUND! Run train_captcha.py first!{Style.RESET_ALL}")
        
        print(f"\n           [0] Back")
        
        print(f"\n{Fore.CYAN}{'=' * 58}{Style.RESET_ALL}\n")
    
    def handle_captcha_config(self):
        """Handler for Captcha configuration (foldable sub-menu)"""
        while True:
            self.show_captcha_menu()
            choice = input(f"                    {Fore.CYAN}Choose an option: {Style.RESET_ALL}")
            
            if choice.lower() == 'n':
                self.config['notification_enabled'] = not self.config.get('notification_enabled', True)
                state = "enabled" if self.config['notification_enabled'] else "disabled"
                print(f"           {Fore.GREEN}Desktop Notification {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice.lower() == 's':
                self.config['sound_enabled'] = not self.config.get('sound_enabled', True)
                state = "enabled" if self.config['sound_enabled'] else "disabled"
                print(f"           {Fore.GREEN}Sound Alarm {state}!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice.lower() == 'l':
                print(f"\n           {Fore.CYAN}Alarm Volume (0-100){Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {self.config.get('alarm_volume', 33)}%{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}0 = muted, 50 = normal, 100 = loud{Style.RESET_ALL}")
                vol_input = input(f"           {Fore.CYAN}Volume (0-100): {Style.RESET_ALL}").strip()
                try:
                    vol = int(vol_input)
                    if 0 <= vol <= 100:
                        self.config['alarm_volume'] = vol
                        print(f"           {Fore.GREEN}Volume set to {vol}%!{Style.RESET_ALL}")
                        if WINDOWS and vol > 0:
                            def _test_tone():
                                try:
                                    wav_data = _generate_alarm_wav(volume=vol, frequency=700, duration_ms=400)
                                    winsound.PlaySound(wav_data, winsound.SND_MEMORY | winsound.SND_NOSTOP)
                                except Exception:
                                    pass
                            threading.Thread(target=_test_tone, daemon=True).start()
                            print(f"           {Fore.YELLOW}(Playing test tone...){Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.RED}Invalid! Must be between 0 and 100.{Style.RESET_ALL}")
                except ValueError:
                    print(f"           {Fore.RED}Invalid input! Enter a number (0-100).{Style.RESET_ALL}")
                time_module.sleep(2)
            elif choice.lower() == 'j':
                print(f"\n           {Fore.CYAN}Alarm Repeat (1-10){Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {self.config.get('alarm_repeat', 1)}x{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}How many times the alarm pattern repeats{Style.RESET_ALL}")
                rep_input = input(f"           {Fore.CYAN}Repeats (1-10): {Style.RESET_ALL}").strip()
                try:
                    rep = int(rep_input)
                    if 1 <= rep <= 10:
                        self.config['alarm_repeat'] = rep
                        print(f"           {Fore.GREEN}Alarm Repeat set to {rep}x!{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.RED}Invalid! Must be between 1 and 10.{Style.RESET_ALL}")
                except ValueError:
                    print(f"           {Fore.RED}Invalid input! Enter a number (1-10).{Style.RESET_ALL}")
                time_module.sleep(2)
            elif choice.lower() == 'd':
                print(f"\n           {Fore.CYAN}Select Captcha Service:{Style.RESET_ALL}")
                print(f"           [1] CatchBot AI (Local AI Model - FREE)")
                print(f"           [2] 2Captcha  (https://2captcha.com)")
                print(f"           [3] Anti-Captcha (https://anti-captcha.com)")
                print(f"           [4] Manual (no Auto-Solve)")
                service_choice = input(f"           {Fore.CYAN}Choose (1/2/3/4): {Style.RESET_ALL}").strip()
                if service_choice == '1':
                    # CatchBot AI - check if model exists (unencrypted or encrypted)
                    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                    model_path = os.path.join(script_dir, 'catchbot_model_onnx')
                    encrypted_path = os.path.join(script_dir, 'catchbot_model_onnx_encrypted')
                    if os.path.exists(model_path) or os.path.exists(encrypted_path):
                        self.config['captcha_service'] = 'catchbot_ai'
                        self.config['auto_solve_captcha'] = True
                        print(f"           {Fore.GREEN}Captcha Service: CatchBot AI selected!{Style.RESET_ALL}")
                        print(f"           {Fore.GREEN}Model found! Auto-Solve enabled.{Style.RESET_ALL}")
                        print(f"           {Fore.YELLOW}Configure TTA and delay under [T] and [W]{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.RED}CatchBot AI model not found!{Style.RESET_ALL}")
                        print(f"           {Fore.YELLOW}Train the model first: python train_captcha.py{Style.RESET_ALL}")
                        print(f"           {Fore.YELLOW}Service not changed.{Style.RESET_ALL}")
                elif service_choice == '2':
                    self.config['captcha_service'] = '2captcha'
                    print(f"           {Fore.GREEN}Captcha Service: 2Captcha selected!{Style.RESET_ALL}")
                    if not self.config.get('twocaptcha_api_key', ''):
                        print(f"           {Fore.YELLOW}Don't forget to set your API Key under [C]!{Style.RESET_ALL}")
                    if self.config.get('twocaptcha_api_key', ''):
                        self.config['auto_solve_captcha'] = True
                elif service_choice == '3':
                    self.config['captcha_service'] = 'anticaptcha'
                    print(f"           {Fore.GREEN}Captcha Service: Anti-Captcha selected!{Style.RESET_ALL}")
                    if not self.config.get('anticaptcha_api_key', ''):
                        print(f"           {Fore.YELLOW}Don't forget to set your API Key under [K]!{Style.RESET_ALL}")
                    if self.config.get('anticaptcha_api_key', ''):
                        self.config['auto_solve_captcha'] = True
                elif service_choice == '4':
                    self.config['captcha_service'] = 'manual'
                    self.config['auto_solve_captcha'] = False
                    print(f"           {Fore.GREEN}Captcha Service: Manual (Auto-Solve disabled){Style.RESET_ALL}")
                else:
                    print(f"           {Fore.RED}Invalid selection!{Style.RESET_ALL}")
                time_module.sleep(2)
            elif choice.lower() == 'a':
                service = self.config.get('captcha_service', 'manual')
                service_name = self.get_captcha_service_name()
                if service == 'manual':
                    print(f"           {Fore.RED}Choose a Captcha Service first under [D]!{Style.RESET_ALL}")
                    time_module.sleep(2)
                elif service == 'catchbot_ai':
                    # CatchBot AI: no API key needed, just toggle
                    script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
                    model_path = os.path.join(script_dir, 'catchbot_model_onnx')
                    encrypted_path = os.path.join(script_dir, 'catchbot_model_onnx_encrypted')
                    if not os.path.exists(model_path) and not os.path.exists(encrypted_path):
                        print(f"           {Fore.RED}CatchBot AI model not found! Train it first: python train_captcha.py{Style.RESET_ALL}")
                        time_module.sleep(2)
                    else:
                        self.config['auto_solve_captcha'] = not self.config.get('auto_solve_captcha', False)
                        state = "enabled" if self.config['auto_solve_captcha'] else "disabled"
                        print(f"           {Fore.GREEN}{service_name} Auto-Solve {state}!{Style.RESET_ALL}")
                        time_module.sleep(1)
                elif not self.get_active_captcha_api_key():
                    key_hint = '[C]' if service == '2captcha' else '[K]'
                    print(f"           {Fore.RED}Set a {service_name} API Key first under {key_hint}!{Style.RESET_ALL}")
                    time_module.sleep(2)
                else:
                    self.config['auto_solve_captcha'] = not self.config.get('auto_solve_captcha', False)
                    state = "enabled" if self.config['auto_solve_captcha'] else "disabled"
                    print(f"           {Fore.GREEN}{service_name} Auto-Solve {state}!{Style.RESET_ALL}")
                    time_module.sleep(1)
            elif choice.lower() == 'r':
                print(f"\n           {Fore.CYAN}Max Retries for Auto-Solve (1-5){Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}Current: {self.config.get('captcha_max_retries', 3)}x{Style.RESET_ALL}")
                retry_input = input(f"           {Fore.CYAN}Amount (1-5): {Style.RESET_ALL}").strip()
                try:
                    retries = int(retry_input)
                    if 1 <= retries <= 5:
                        self.config['captcha_max_retries'] = retries
                        print(f"           {Fore.GREEN}Max Retries set to {retries}!{Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.RED}Invalid! Must be between 1 and 5.{Style.RESET_ALL}")
                except ValueError:
                    print(f"           {Fore.RED}Invalid input! Enter a number (1-5).{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice.lower() == 'c':
                print(f"\n           {Fore.CYAN}Enter 2Captcha API Key{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}(Get your key at https://2captcha.com){Style.RESET_ALL}")
                api_key = input(f"           {Fore.CYAN}API Key: {Style.RESET_ALL}").strip()
                if api_key:
                    self.config['twocaptcha_api_key'] = api_key
                    print(f"           {Fore.GREEN}2Captcha API Key saved!{Style.RESET_ALL}")
                    if self.config.get('captcha_service', 'manual') == 'manual':
                        self.config['captcha_service'] = '2captcha'
                        print(f"           {Fore.GREEN}Captcha Service automatically set to 2Captcha!{Style.RESET_ALL}")
                    if not self.config.get('auto_solve_captcha', False) and self.config.get('captcha_service') == '2captcha':
                        self.config['auto_solve_captcha'] = True
                        print(f"           {Fore.GREEN}Auto-Solve automatically enabled!{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.RED}No key entered!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice.lower() == 'k':
                print(f"\n           {Fore.CYAN}Enter Anti-Captcha API Key{Style.RESET_ALL}")
                print(f"           {Fore.YELLOW}(Get your key at https://anti-captcha.com){Style.RESET_ALL}")
                api_key = input(f"           {Fore.CYAN}API Key: {Style.RESET_ALL}").strip()
                if api_key:
                    self.config['anticaptcha_api_key'] = api_key
                    print(f"           {Fore.GREEN}Anti-Captcha API Key saved!{Style.RESET_ALL}")
                    if self.config.get('captcha_service', 'manual') == 'manual':
                        self.config['captcha_service'] = 'anticaptcha'
                        print(f"           {Fore.GREEN}Captcha Service automatically set to Anti-Captcha!{Style.RESET_ALL}")
                    if not self.config.get('auto_solve_captcha', False) and self.config.get('captcha_service') == 'anticaptcha':
                        self.config['auto_solve_captcha'] = True
                        print(f"           {Fore.GREEN}Auto-Solve automatically enabled!{Style.RESET_ALL}")
                else:
                    print(f"           {Fore.RED}No key entered!{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice.lower() == 't':
                # Toggle TTA (only relevant for CatchBot AI)
                service = self.config.get('captcha_service', 'manual')
                if service != 'catchbot_ai':
                    print(f"           {Fore.YELLOW}TTA is only available with CatchBot AI service!{Style.RESET_ALL}")
                    print(f"           {Fore.YELLOW}Select CatchBot AI under [D] first.{Style.RESET_ALL}")
                else:
                    self.config['catchbot_ai_tta'] = not self.config.get('catchbot_ai_tta', False)
                    state = "enabled" if self.config['catchbot_ai_tta'] else "disabled"
                    if self.config['catchbot_ai_tta']:
                        print(f"           {Fore.GREEN}TTA {state}! (Higher accuracy, slightly slower){Style.RESET_ALL}")
                    else:
                        print(f"           {Fore.YELLOW}TTA {state}! (Faster but less accurate){Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice.lower() == 'w':
                # Configure answer delay (only relevant for CatchBot AI)
                service = self.config.get('captcha_service', 'manual')
                if service != 'catchbot_ai':
                    print(f"           {Fore.YELLOW}Answer delay is only for CatchBot AI service!{Style.RESET_ALL}")
                else:
                    delay_min = self.config.get('catchbot_ai_delay_min', 7)
                    delay_max = self.config.get('catchbot_ai_delay_max', 15)
                    print(f"\n           {Fore.CYAN}CatchBot AI Answer Delay{Style.RESET_ALL}")
                    print(f"           {Fore.YELLOW}Current: {delay_min}-{delay_max}s (random per attempt){Style.RESET_ALL}")
                    print(f"           {Fore.YELLOW}Simulates human solve time to avoid detection.{Style.RESET_ALL}")
                    min_input = input(f"           {Fore.CYAN}Min delay in seconds (7-25): {Style.RESET_ALL}").strip()
                    max_input = input(f"           {Fore.CYAN}Max delay in seconds (7-25): {Style.RESET_ALL}").strip()
                    try:
                        new_min = int(min_input)
                        new_max = int(max_input)
                        if 7 <= new_min <= 25 and 7 <= new_max <= 25 and new_min <= new_max:
                            self.config['catchbot_ai_delay_min'] = new_min
                            self.config['catchbot_ai_delay_max'] = new_max
                            print(f"           {Fore.GREEN}Delay set to {new_min}-{new_max}s!{Style.RESET_ALL}")
                        else:
                            print(f"           {Fore.RED}Invalid! Min must be <= Max, both between 7-25.{Style.RESET_ALL}")
                    except ValueError:
                        print(f"           {Fore.RED}Invalid input! Enter numbers.{Style.RESET_ALL}")
                time_module.sleep(1)
            elif choice.lower() == 'g':
                self.show_captcha_balance()
            elif choice == '0':
                self.save_config()
                break
    
