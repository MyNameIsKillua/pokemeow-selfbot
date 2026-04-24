"""LogsMixin: log, save_logs_on_stop, show_logs."""
import os
import sys
import time as time_module
from datetime import datetime, timedelta
from colorama import Fore, Style


class LogsMixin:
    def log(self, message):
        """Fügt einen Log-Eintrag hinzu und schreibt live in Datei"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}"
        self.logs.append(log_entry)
        if len(self.logs) > 200:
            self.logs.pop(0)
        
        # Sofort in Datei schreiben
        if self.start_time:
            try:
                log_filename = os.path.join(self.logs_dir, f'Logs {self.start_time}.txt')
                with open(log_filename, 'a', encoding='utf-8') as f:
                    f.write(log_entry + '\n')
            except Exception:
                pass
    
    def save_logs_on_stop(self):
        """Speichert finale Log-Zeile beim Beenden und zeigt Session-Stats"""
        # Session-Stats anzeigen wenn es Encounters gab
        if self.session_stats.get('total_encounters', 0) > 0:
            self.print_session_stats()
            
            # Stats auch in Log-Datei schreiben
            s = self.session_stats
            total = s['total_encounters']
            caught = s['total_caught']
            fled = s['total_fled']
            rate = (caught / total * 100) if total > 0 else 0
            duration = self.get_session_duration()
            
            self.log(f"=== SESSION STATS: {duration} | Encounters: {total} | Caught: {caught} | Fled: {fled} | Rate: {rate:.1f}% ===")
            
            for r in s['caught_by_rarity']:
                c = s['caught_by_rarity'].get(r, 0)
                f = s['fled_by_rarity'].get(r, 0)
                self.log(f"  {r}: {c}/{c+f} caught")
        
        # Persistent Stats speichern
        self.save_persistent_stats()
        
        if not self.start_time:
            return
        
        try:
            stop_time = datetime.now().strftime('%d.%m.%Y %H:%M:%S')
            log_filename = os.path.join(self.logs_dir, f'Logs {self.start_time}.txt')
            with open(log_filename, 'a', encoding='utf-8') as f:
                f.write(f'\n=== Bot stopped: {stop_time} ===\n')
            print(f"\n{Fore.GREEN}Logs saved: {log_filename}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error saving logs: {str(e)}{Style.RESET_ALL}")
    
    # ═════════════════════════════════════════════════════════════════
    #  POKEMON NAMEN SYSTEM
    # ═════════════════════════════════════════════════════════════════
    
    def show_logs(self):
        """Zeigt die letzten Logs"""
        self.print_header()
        print(f"\n{Fore.CYAN}+======================= LOGS ===========================+{Style.RESET_ALL}\n")
        
        if not self.logs:
            print(f"           {Fore.YELLOW}No logs available.{Style.RESET_ALL}")
        else:
            for log in self.logs[-20:]:
                print(f"           {log}")
        
        log_files = sorted(os.listdir(self.logs_dir)) if os.path.exists(self.logs_dir) else []
        if log_files:
            print(f"\n           {Fore.YELLOW}Saved Log Files:{Style.RESET_ALL}")
            for f in log_files[-5:]:
                filepath = os.path.join(self.logs_dir, f)
                size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
                print(f"           {self.logs_dir}/{f} ({size} Bytes)")
        
        print(f"\n{Fore.CYAN}╚═════════════════════════════════════════════════════════╝{Style.RESET_ALL}\n")
        input(f"           {Fore.YELLOW}Press Enter to continue...{Style.RESET_ALL}")
    
