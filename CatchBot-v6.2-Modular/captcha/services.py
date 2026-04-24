"""CaptchaServicesMixin: 2Captcha + AntiCaptcha + CatchBot AI solvers."""
import os
import sys
import time as time_module
import base64
from datetime import datetime
from colorama import Fore, Style

from utils.platform import HAS_REQUESTS

try:
    import requests
except ImportError:
    pass


class CaptchaServicesMixin:
    def get_captcha_service_name(self):
        """Gibt den Anzeigenamen des aktiven Captcha-Services zurück"""
        service = self.config.get('captcha_service', 'manual')
        names = {'2captcha': '2Captcha', 'anticaptcha': 'Anti-Captcha', 'catchbot_ai': 'CatchBot AI', 'manual': 'Manual'}
        return names.get(service, service)
    
    def get_active_captcha_api_key(self):
        """Gibt den API Key des aktiven Captcha-Services zurück"""
        service = self.config.get('captcha_service', 'manual')
        if service == '2captcha':
            return self.config.get('twocaptcha_api_key', '')
        elif service == 'anticaptcha':
            return self.config.get('anticaptcha_api_key', '')
        elif service == 'catchbot_ai':
            # CatchBot AI uses a local model, no API key needed
            # Return a non-empty string so has_api_key checks pass
            return 'local_model'
        return ''
    
    # ═════════════════════════════════════════════════════════════════
    #  CATCHBOT AI SOLVER (Local TrOCR Model)
    # ═════════════════════════════════════════════════════════════════
    
    _ai_solver = None  # Class-level: shared across all instances, loaded once
    
    @classmethod
    def _load_ai_solver(cls):
        """Lazy-load the CatchBot AI solver (only once, on first use)."""
        if cls._ai_solver is not None:
            return cls._ai_solver
        
        try:
            # Import the bundled solver module from the captcha package.
            script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
            
            # Check for encrypted model first (preferred), then unencrypted
            encrypted_path = os.path.join(script_dir, 'catchbot_model_onnx_encrypted')
            unencrypted_path = os.path.join(script_dir, 'catchbot_model_onnx')
            
            if os.path.exists(encrypted_path):
                # Use encrypted model - pass base path, solver.py adds "_encrypted"
                model_path = unencrypted_path
            elif os.path.exists(unencrypted_path):
                # Use unencrypted model
                model_path = unencrypted_path
            else:
                print(f"{Fore.RED}  CatchBot AI model not found!{Style.RESET_ALL}")
                print(f"{Fore.RED}  Looked in: {unencrypted_path}{Style.RESET_ALL}")
                print(f"{Fore.RED}  Looked in: {encrypted_path}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}  Run export_to_onnx.py then encrypt_model.py!{Style.RESET_ALL}")
                return None
            
            # Add script dir to path so package imports resolve when launched from a console.
            if script_dir not in sys.path:
                sys.path.insert(0, script_dir)
            
            from captcha.solver import CaptchaAISolver
            cls._ai_solver = CaptchaAISolver(model_path)
            return cls._ai_solver
        
        except Exception as e:
            print(f"{Fore.RED}  Failed to load CatchBot AI: {str(e)}{Style.RESET_ALL}")
            return None
    
    def solve_captcha_with_ai(self, image_base64):
        """
        Solve captcha using the local CatchBot AI (TrOCR) model.
        Returns (solution, task_id) - task_id is None since it's local.
        """
        try:
            solver = self._load_ai_solver()
            if solver is None:
                return None, None
            
            use_tta = self.config.get('catchbot_ai_tta', False)
            solution = solver.solve_from_base64(image_base64, use_tta=use_tta)
            
            if solution:
                print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] CatchBot AI prediction: '{solution}' (TTA={'ON' if use_tta else 'OFF'}){Style.RESET_ALL}")
                return solution, None
            else:
                print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] CatchBot AI returned empty prediction{Style.RESET_ALL}")
                return None, None
        
        except Exception as e:
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] CatchBot AI Error: {str(e)}{Style.RESET_ALL}")
            return None, None
    
    # ═════════════════════════════════════════════════════════════════
    #  CAPTCHA BALANCE CHECK
    # ═════════════════════════════════════════════════════════════════
    
    def check_2captcha_balance(self):
        """Fragt das 2Captcha Guthaben ab und gibt es zurück"""
        if not HAS_REQUESTS:
            return None, "'requests' Modul nicht installiert!"
        
        api_key = self.config.get('twocaptcha_api_key', '')
        if not api_key:
            return None, "No 2Captcha API Key set!"
        
        try:
            payload = {"clientKey": api_key}
            response = requests.post(
                "https://api.2captcha.com/getBalance",
                json=payload,
                timeout=10
            )
            result = response.json()
            
            if result.get('errorId', 1) != 0:
                error_desc = result.get('errorDescription', 'Unknown error')
                return None, f"API Error: {error_desc}"
            
            balance = result.get('balance', 0)
            return balance, None
            
        except requests.exceptions.RequestException as e:
            return None, f"Network Error: {str(e)}"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def check_anticaptcha_balance(self):
        """Fragt das Anti-Captcha Guthaben ab und gibt es zurueck"""
        if not HAS_REQUESTS:
            return None, "'requests' Modul nicht installiert!"
        
        api_key = self.config.get('anticaptcha_api_key', '')
        if not api_key:
            return None, "No Anti-Captcha API Key set!"
        
        try:
            payload = {"clientKey": api_key}
            response = requests.post(
                "https://api.anti-captcha.com/getBalance",
                json=payload,
                timeout=10
            )
            result = response.json()
            
            if result.get('errorId', 1) != 0:
                error_desc = result.get('errorDescription', 'Unknown error')
                return None, f"API Error: {error_desc}"
            
            balance = result.get('balance', 0)
            return balance, None
            
        except requests.exceptions.RequestException as e:
            return None, f"Network Error: {str(e)}"
        except Exception as e:
            return None, f"Error: {str(e)}"
    
    def show_captcha_balance(self):
        """Zeigt das Guthaben des aktiven Captcha-Services an"""
        service = self.config.get('captcha_service', 'manual')
        
        print(f"\n           {Fore.CYAN}═══ Check Captcha Balance ═══{Style.RESET_ALL}")
        
        # 2Captcha Balance
        api_key_2c = self.config.get('twocaptcha_api_key', '')
        if api_key_2c:
            print(f"           {Fore.YELLOW}Checking 2Captcha balance...{Style.RESET_ALL}", end="", flush=True)
            balance, error = self.check_2captcha_balance()
            if error:
                print(f"\r           {Fore.RED}2Captcha: {error}{Style.RESET_ALL}                    ")
            else:
                color = Fore.GREEN if balance > 1.0 else (Fore.YELLOW if balance > 0.2 else Fore.RED)
                print(f"\r           {color}2Captcha Balance: ${balance:.4f}{Style.RESET_ALL}                    ")
                if balance < 0.2:
                    print(f"           {Fore.RED}⚠ Balance low! Please recharge!{Style.RESET_ALL}")
        else:
            print(f"           {Fore.YELLOW}2Captcha: No API Key set{Style.RESET_ALL}")
        
        # Anti-Captcha Balance
        api_key_ac = self.config.get('anticaptcha_api_key', '')
        if api_key_ac:
            print(f"           {Fore.YELLOW}Checking Anti-Captcha balance...{Style.RESET_ALL}", end="", flush=True)
            balance, error = self.check_anticaptcha_balance()
            if error:
                print(f"\r           {Fore.RED}Anti-Captcha: {error}{Style.RESET_ALL}                    ")
            else:
                color = Fore.GREEN if balance > 1.0 else (Fore.YELLOW if balance > 0.2 else Fore.RED)
                print(f"\r           {color}Anti-Captcha Balance: ${balance:.4f}{Style.RESET_ALL}                    ")
                if balance < 0.2:
                    print(f"           {Fore.RED}⚠ Balance low! Please recharge!{Style.RESET_ALL}")
        else:
            print(f"           {Fore.YELLOW}Anti-Captcha: No API Key set{Style.RESET_ALL}")
        
        if not api_key_2c and not api_key_ac:
            print(f"           {Fore.RED}No captcha service configured!{Style.RESET_ALL}")
            print(f"           {Fore.YELLOW}Set an API key first under [C] (2Captcha) or [K] (Anti-Captcha).{Style.RESET_ALL}")
        
        print()
        time_module.sleep(3)
    
    def report_2captcha(self, task_id, correct):
        """Meldet ein Captcha-Ergebnis an 2Captcha zurueck (reportCorrect / reportIncorrect)"""
        if not HAS_REQUESTS or not task_id:
            return
        api_key = self.config.get('twocaptcha_api_key', '')
        if not api_key:
            return
        endpoint = "https://api.2captcha.com/reportCorrect" if correct else "https://api.2captcha.com/reportIncorrect"
        action = "correct" if correct else "incorrect"
        try:
            payload = {"clientKey": api_key, "taskId": task_id}
            resp = requests.post(endpoint, json=payload, timeout=10)
            result = resp.json()
            if result.get('errorId', 1) == 0:
                self.log(f"2Captcha: Report {action} sent for Task #{task_id}.")
            else:
                self.log(f"2Captcha: Report {action} Error: {result.get('errorDescription', '?')}")
        except Exception as e:
            self.log(f"2Captcha: Report {action} Error: {str(e)}")
    
    def solve_captcha_with_2captcha(self, image_base64):
        """Sendet das Captcha-Bild an 2Captcha API und gibt (solution, task_id) zurueck"""
        if not HAS_REQUESTS:
            self.log("❌ 2Captcha: 'requests' module not installed! Install with: py -m pip install requests")
            return None, None
        
        api_key = self.config.get('twocaptcha_api_key', '')
        if not api_key:
            self.log("❌ 2Captcha: No API Key set! Set it in the config.")
            return None, None
        
        try:
            # Step 1: Create task (createTask)
            self.log("🔄 2Captcha: Sending captcha for solving...")
            print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] 🔄 2Captcha: Sending captcha for solving...{Style.RESET_ALL}")
            
            create_payload = {
                "clientKey": api_key,
                "task": {
                    "type": "ImageToTextTask",
                    "body": image_base64,
                    "case": True,
                    "numeric": 1,
                    "minLength": 3,
                    "maxLength": 6,
                    "comment": "enter the numbers you see on the image (digits 0-9 only, 3-6 digits)"
                },
                "languagePool": "en"
            }
            
            response = requests.post(
                "https://api.2captcha.com/createTask",
                json=create_payload,
                timeout=30
            )
            result = response.json()
            
            if result.get('errorId', 1) != 0:
                error_desc = result.get('errorDescription', 'Unknown error')
                error_code = result.get('errorCode', 'UNKNOWN')
                self.log(f"❌ 2Captcha createTask Error: {error_code} - {error_desc}")
                print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ 2Captcha Error: {error_code} - {error_desc}{Style.RESET_ALL}")
                return None, None
            
            task_id = result.get('taskId')
            if not task_id:
                self.log("❌ 2Captcha: No Task ID received!")
                return None, None
            
            self.log(f"🔄 2Captcha: Task created (ID: {task_id}), waiting for solution...")
            print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] 🔄 2Captcha: Task #{task_id} created, waiting for solution...{Style.RESET_ALL}")
            
            # Schritt 2: Auf Ergebnis warten (getTaskResult) - max 120 Sekunden
            for attempt in range(24):  # 24 * 5s = 120s max
                time_module.sleep(5)
                
                result_payload = {
                    "clientKey": api_key,
                    "taskId": task_id
                }
                
                response = requests.post(
                    "https://api.2captcha.com/getTaskResult",
                    json=result_payload,
                    timeout=30
                )
                result = response.json()
                
                if result.get('errorId', 1) != 0:
                    error_desc = result.get('errorDescription', 'Unknown error')
                    self.log(f"❌ 2Captcha getTaskResult Error: {error_desc}")
                    return None, task_id
                
                status = result.get('status', '')
                
                if status == 'ready':
                    solution = result.get('solution', {}).get('text', '')
                    cost = result.get('cost', '?')
                    self.log(f"✅ 2Captcha: Solution received: '{solution}' (Cost: ${cost})")
                    print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ✅ 2Captcha Solution: '{solution}' (Cost: ${cost}){Style.RESET_ALL}")
                    return solution, task_id
                elif status == 'processing':
                    if attempt % 2 == 0:
                        print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ⏳ 2Captcha: Still solving... ({(attempt+1)*5}s){Style.RESET_ALL}")
                else:
                    self.log(f"❌ 2Captcha: Unknown status: {status}")
                    return None, task_id
            
            self.log("❌ 2Captcha: Timeout - no solution after 120 seconds!")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ 2Captcha: Timeout after 120s!{Style.RESET_ALL}")
            return None, task_id
            
        except requests.exceptions.RequestException as e:
            self.log(f"2Captcha Network Error: {str(e)}")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ 2Captcha Network Error: {str(e)}{Style.RESET_ALL}")
            return None, None
        except Exception as e:
            self.log(f"❌ 2Captcha Error: {str(e)}")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ 2Captcha Error: {str(e)}{Style.RESET_ALL}")
            return None, None
    
    def report_anticaptcha(self, task_id, correct):
        """Meldet ein Captcha-Ergebnis an Anti-Captcha zurueck (reportIncorrectImageCaptcha)"""
        if not HAS_REQUESTS or not task_id:
            return
        api_key = self.config.get('anticaptcha_api_key', '')
        if not api_key:
            return
        # Anti-Captcha hat nur reportIncorrectImageCaptcha (kein reportCorrect fuer Bilder)
        if correct:
            self.log(f"Anti-Captcha: Solution was correct (Task #{task_id}).")
            return
        try:
            payload = {"clientKey": api_key, "taskId": task_id}
            resp = requests.post(
                "https://api.anti-captcha.com/reportIncorrectImageCaptcha",
                json=payload,
                timeout=10
            )
            result = resp.json()
            if result.get('errorId', 1) == 0:
                self.log(f"Anti-Captcha: Report incorrect sent for Task #{task_id} (refund possible).")
            else:
                self.log(f"Anti-Captcha: Report incorrect Error: {result.get('errorDescription', '?')}")
        except Exception as e:
            self.log(f"Anti-Captcha: Report incorrect Error: {str(e)}")
    
    def solve_captcha_with_anticaptcha(self, image_base64):
        """Sendet das Captcha-Bild an Anti-Captcha API und gibt (solution, task_id) zurueck"""
        if not HAS_REQUESTS:
            self.log("❌ Anti-Captcha: 'requests' module not installed! Install with: py -m pip install requests")
            return None, None
        
        api_key = self.config.get('anticaptcha_api_key', '')
        if not api_key:
            self.log("❌ Anti-Captcha: No API Key set! Set it in the config.")
            return None, None
        
        try:
            # Step 1: Create task (createTask)
            self.log("🔄 Anti-Captcha: Sending captcha for solving...")
            print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] 🔄 Anti-Captcha: Sending captcha for solving...{Style.RESET_ALL}")
            
            create_payload = {
                "clientKey": api_key,
                "task": {
                    "type": "ImageToTextTask",
                    "body": image_base64,
                    "case": True,
                    "numeric": 1,
                    "minLength": 3,
                    "maxLength": 6,
                    "comment": "enter the numbers you see (digits 0-9 only, 3-6 digits)"
                },
                "languagePool": "en"
            }
            
            response = requests.post(
                "https://api.anti-captcha.com/createTask",
                json=create_payload,
                timeout=30
            )
            result = response.json()
            
            if result.get('errorId', 1) != 0:
                error_desc = result.get('errorDescription', 'Unknown error')
                error_code = result.get('errorCode', 'UNKNOWN')
                self.log(f"❌ Anti-Captcha createTask Error: {error_code} - {error_desc}")
                print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ Anti-Captcha Error: {error_code} - {error_desc}{Style.RESET_ALL}")
                return None, None
            
            task_id = result.get('taskId')
            if not task_id:
                self.log("❌ Anti-Captcha: No Task ID received!")
                return None, None
            
            self.log(f"🔄 Anti-Captcha: Task created (ID: {task_id}), waiting for solution...")
            print(f"{Fore.CYAN}[{datetime.now().strftime('%H:%M:%S')}] 🔄 Anti-Captcha: Task #{task_id} created, waiting for solution...{Style.RESET_ALL}")
            
            # Schritt 2: Auf Ergebnis warten (getTaskResult) - max 120 Sekunden
            for attempt in range(40):  # 40 * 3s = 120s max
                time_module.sleep(3)
                
                result_payload = {
                    "clientKey": api_key,
                    "taskId": task_id
                }
                
                response = requests.post(
                    "https://api.anti-captcha.com/getTaskResult",
                    json=result_payload,
                    timeout=30
                )
                result = response.json()
                
                if result.get('errorId', 1) != 0:
                    error_desc = result.get('errorDescription', 'Unknown error')
                    self.log(f"❌ Anti-Captcha getTaskResult Error: {error_desc}")
                    return None, task_id
                
                status = result.get('status', '')
                
                if status == 'ready':
                    solution = result.get('solution', {}).get('text', '')
                    cost = result.get('cost', '?')
                    self.log(f"✅ Anti-Captcha: Solution received: '{solution}' (Cost: ${cost})")
                    print(f"{Fore.GREEN}[{datetime.now().strftime('%H:%M:%S')}] ✅ Anti-Captcha Solution: '{solution}' (Cost: ${cost}){Style.RESET_ALL}")
                    return solution, task_id
                elif status == 'processing':
                    if attempt % 3 == 0:
                        print(f"{Fore.YELLOW}[{datetime.now().strftime('%H:%M:%S')}] ⏳ Anti-Captcha: Still solving... ({(attempt+1)*3}s){Style.RESET_ALL}")
                else:
                    self.log(f"❌ Anti-Captcha: Unknown status: {status}")
                    return None, task_id
            
            self.log("❌ Anti-Captcha: Timeout - no solution after 120 seconds!")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ Anti-Captcha: Timeout after 120s!{Style.RESET_ALL}")
            return None, task_id
            
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Anti-Captcha Network Error: {str(e)}")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ Anti-Captcha Network Error: {str(e)}{Style.RESET_ALL}")
            return None, None
        except Exception as e:
            self.log(f"❌ Anti-Captcha Error: {str(e)}")
            print(f"{Fore.RED}[{datetime.now().strftime('%H:%M:%S')}] ❌ Anti-Captcha Error: {str(e)}{Style.RESET_ALL}")
            return None, None
    
