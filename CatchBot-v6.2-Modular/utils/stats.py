"""StatsMixin: session duration + print_session_stats."""
import os
from datetime import datetime, timedelta
from colorama import Fore, Style


class StatsMixin:
    def get_session_duration(self):
        """Gibt die Session-Dauer als formatierten String zurueck"""
        if not self.session_stats['session_start']:
            return "0m"
        delta = datetime.now() - self.session_stats['session_start']
        total_seconds = int(delta.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def print_session_stats(self):
        """Zeigt die Session-Statistiken huebsch formatiert an"""
        s = self.session_stats
        p = self.persistent_stats
        
        total = s['total_encounters']
        caught = s['total_caught']
        fled = s['total_fled']
        rate = (caught / total * 100) if total > 0 else 0
        duration = self.get_session_duration()
        
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}              SESSION STATISTICS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"  Duration:          {Fore.WHITE}{duration}{Style.RESET_ALL}")
        print(f"  Encounters:        {Fore.WHITE}{total}{Style.RESET_ALL}")
        print(f"  Caught:            {Fore.GREEN}{caught}{Style.RESET_ALL}")
        print(f"  Fled:              {Fore.RED}{fled}{Style.RESET_ALL}")
        print(f"  Catch-Rate:        {Fore.YELLOW}{rate:.1f}%{Style.RESET_ALL}")
        
        # Fish stats (session)
        fished = s.get('total_fished', 0)
        fished_fled = s.get('total_fished_fled', 0)
        if fished > 0 or fished_fled > 0:
            print(f"\n{Fore.CYAN}  --- Fishing (Session) ---{Style.RESET_ALL}")
            print(f"  Fished:            {Fore.GREEN}{fished}{Style.RESET_ALL}")
            print(f"  Fished Fled:       {Fore.RED}{fished_fled}{Style.RESET_ALL}")
        
        # Fangquote pro Rarity
        all_rarities = set(list(s['caught_by_rarity'].keys()) + list(s['fled_by_rarity'].keys()))
        if all_rarities:
            print(f"\n{Fore.CYAN}  --- Catch Rate per Rarity ---{Style.RESET_ALL}")
            
            rarity_colors = {
                'common': Fore.CYAN,
                'uncommon': Fore.GREEN,
                'rare': Fore.YELLOW,
                'super rare': Fore.LIGHTYELLOW_EX,
                'legendary': Fore.MAGENTA,
                'shiny': Fore.LIGHTMAGENTA_EX,
            }
            
            # Sortiert nach Seltenheit
            rarity_order = ['Common', 'Uncommon', 'Rare', 'Super Rare', 'Legendary', 'Shiny']
            sorted_rarities = sorted(all_rarities, 
                key=lambda r: next((i for i, ro in enumerate(rarity_order) if ro.lower() == r.lower()), 99))
            
            for r in sorted_rarities:
                c = s['caught_by_rarity'].get(r, 0)
                f = s['fled_by_rarity'].get(r, 0)
                t = c + f
                r_rate = (c / t * 100) if t > 0 else 0
                color = rarity_colors.get(r.lower(), Fore.WHITE)
                print(f"  {color}{r:16s}{Style.RESET_ALL}  {c}/{t}  ({Fore.YELLOW}{r_rate:.0f}%{Style.RESET_ALL})")
        
        # Egg Stats (Session)
        session_eggs = s.get('eggs_hatched', 0)
        if session_eggs > 0:
            print(f"\n{Fore.CYAN}  --- Eggs (Session) ---{Style.RESET_ALL}")
            print(f"  Eggs Hatched:      {Fore.MAGENTA}{session_eggs}{Style.RESET_ALL}")

        # All-Time Stats
        print(f"\n{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}              ALL-TIME STATISTICS{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}")
        print(f"  Total Sessions:    {Fore.WHITE}{p.get('sessions', 0)}{Style.RESET_ALL}")
        alltime_total = p.get('total_caught_alltime', 0) + p.get('total_fled_alltime', 0)
        alltime_rate = (p.get('total_caught_alltime', 0) / alltime_total * 100) if alltime_total > 0 else 0
        print(f"  Total Caught:      {Fore.GREEN}{p.get('total_caught_alltime', 0)}{Style.RESET_ALL}")
        print(f"  Total Fled:        {Fore.RED}{p.get('total_fled_alltime', 0)}{Style.RESET_ALL}")
        print(f"  Catch-Rate:        {Fore.YELLOW}{alltime_rate:.1f}%{Style.RESET_ALL}")
        
        # Fish stats (all-time)
        at_fished = p.get('total_fished_alltime', 0)
        at_fished_fled = p.get('total_fished_fled_alltime', 0)
        if at_fished > 0 or at_fished_fled > 0:
            print(f"\n  Total Fished:      {Fore.GREEN}{at_fished}{Style.RESET_ALL}")
            print(f"  Total Fished Fled: {Fore.RED}{at_fished_fled}{Style.RESET_ALL}")
        
        # Shiny & Legendary Counter
        shiny_count = p.get('shinys_caught', 0)
        legend_count = p.get('legendarys_caught', 0)
        
        print(f"  {Fore.MAGENTA}Legendaries Caught:  {legend_count}{Style.RESET_ALL}")
        print(f"\n  {Fore.LIGHTMAGENTA_EX}Shinys Caught:       {shiny_count}{Style.RESET_ALL}")
    
        # Captcha Stats (Lifetime) in All-Time section
        lifetime_captcha = p.get('captcha_attempts', {})
        lifetime_total = p.get('total_captchas_solved', 0)
        if lifetime_captcha or lifetime_total > 0:
            print(f"\n  {Fore.CYAN}--- Captcha Stats ---{Style.RESET_ALL}")
            print(f"  Total Solved:      {Fore.GREEN}{lifetime_total}{Style.RESET_ALL}")
            for attempts in sorted(lifetime_captcha.keys(), key=lambda x: int(x)):
                count = lifetime_captcha[attempts]
                attempt_label = f"{attempts} Attempt{'s' if int(attempts) > 1 else ''}"
                print(f"    {attempt_label:14s}  {Fore.YELLOW}{count}x{Style.RESET_ALL}")
        
        # === EGG STATS (All-Time) ===
        eggs_total = p.get('eggs_hatched', 0)
        if eggs_total > 0:
            print(f"\n{Fore.CYAN}  --- Egg Statistics (All-Time) ---{Style.RESET_ALL}")
            print(f"  Total Eggs Hatched: {Fore.MAGENTA}{eggs_total}{Style.RESET_ALL}")
            
            # Rarity breakdown
            egg_rarity = p.get('egg_rarity_stats', {})
            if egg_rarity:
                for rarity_name, count in sorted(egg_rarity.items()):
                    color = Fore.LIGHTMAGENTA_EX if rarity_name == 'Shiny' else Fore.WHITE
                    print(f"    {color}{rarity_name}: {count}{Style.RESET_ALL}")
            
            # Show last 5 shiny/legendary egg hatches only
            egg_list = p.get('egg_pokemon_list', [])
            notable_eggs = [e for e in egg_list if e.get('shiny')]
            if notable_eggs:
                print(f"  Last Shiny Egg Hatches:")
                for egg in notable_eggs[-5:]:
                    print(f"    {Fore.LIGHTMAGENTA_EX}> {egg['name']} (SHINY) ({egg['date']}){Style.RESET_ALL}")
        
        print(f"{Fore.CYAN}{'=' * 60}{Style.RESET_ALL}\n")
    
    # ═════════════════════════════════════════════════════════════════
    #  CAPTCHA SERVICE HELPERS
    # ═════════════════════════════════════════════════════════════════
    
