"""ConfigMixin: load/save config + persistent stats."""
import os
import sys
import json
import threading
import time as time_module
from datetime import datetime, timedelta
from colorama import Fore, Style


class ConfigMixin:
    def load_persistent_stats(self):
        """Laedt die persistenten Statistiken aus stats.json"""
        try:
            if os.path.exists(self.stats_path):
                with open(self.stats_path, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                # Migration: add missing egg stats keys for existing stats files
                if 'eggs_hatched' not in stats:
                    stats['eggs_hatched'] = 0
                if 'egg_pokemon_list' not in stats:
                    stats['egg_pokemon_list'] = []
                if 'egg_rarity_stats' not in stats:
                    stats['egg_rarity_stats'] = {}
                # Migration: add missing fish stats keys
                if 'total_fished_alltime' not in stats:
                    stats['total_fished_alltime'] = 0
                if 'total_fished_fled_alltime' not in stats:
                    stats['total_fished_fled_alltime'] = 0
                return stats
        except Exception:
            pass
        return {
            'total_caught_alltime': 0,
            'total_fled_alltime': 0,
            'shinys_caught': 0,
            'legendarys_caught': 0,
            'shiny_list': [],       # [{"name": "Pikachu", "date": "18.02.2026 14:30"}]
            'legendary_list': [],
            'sessions': 0,
            'total_fished_alltime': 0,
            'total_fished_fled_alltime': 0,
            'eggs_hatched': 0,
            'egg_pokemon_list': [],  # [{"name": "Elekid", "date": "20.02.2026 13:25", "shiny": true}]
            'egg_rarity_stats': {},  # {"Normal": 10, "Shiny": 1}
        }
    
    def save_persistent_stats(self):
        """Speichert die persistenten Statistiken in stats.json"""
        try:
            with open(self.stats_path, 'w', encoding='utf-8') as f:
                json.dump(self.persistent_stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"Error saving stats: {str(e)}")
    
    def load_config(self):
        """Lädt die Konfiguration oder erstellt Default-Config"""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = json.load(f)
            
            if 'auto_catch_enabled' not in config:
                config['auto_catch_enabled'] = True
            if 'catch_rules' not in config:
                config['catch_rules'] = {
                    'common': 'pb', 'uncommon': 'pb', 'rare': 'gb',
                    'super_rare': 'ub', 'legendary': 'mb', 'shiny': 'mb',
                    'golden': 'mb'
                }
            # Migration: ensure golden rarity exists for fishing catches
            if 'golden' not in config.get('catch_rules', {}):
                config['catch_rules']['golden'] = 'mb'
            if 'notification_enabled' not in config:
                config['notification_enabled'] = True
            if 'pokemon_whitelist' not in config:
                config['pokemon_whitelist'] = {}
            if 'sound_enabled' not in config:
                config['sound_enabled'] = True
            if 'egg_enabled' not in config:
                config['egg_enabled'] = False
            if 'twocaptcha_api_key' not in config:
                config['twocaptcha_api_key'] = ''
            if 'anticaptcha_api_key' not in config:
                config['anticaptcha_api_key'] = ''
            if 'auto_solve_captcha' not in config:
                config['auto_solve_captcha'] = False
            if 'captcha_service' not in config:
                # Auto-detect based on existing keys
                if config.get('twocaptcha_api_key', ''):
                    config['captcha_service'] = '2captcha'
                elif config.get('anticaptcha_api_key', ''):
                    config['captcha_service'] = 'anticaptcha'
                else:
                    config['captcha_service'] = 'manual'
            if 'captcha_max_retries' not in config:
                config['captcha_max_retries'] = 3
            # Migration: CatchBot AI settings
            if 'catchbot_ai_tta' not in config:
                config['catchbot_ai_tta'] = False
            if 'catchbot_ai_delay_min' not in config:
                config['catchbot_ai_delay_min'] = 7
            if 'catchbot_ai_delay_max' not in config:
                config['catchbot_ai_delay_max'] = 15
            if 'autobuyer' not in config:
                config['autobuyer'] = {
                    'enabled': False,
                    'pb': {'threshold': 10, 'amount': 200},
                    'gb': {'threshold': 10, 'amount': 100},
                    'ub': {'threshold': 10, 'amount': 25},
                    'mb': {'threshold': 1, 'amount': 1},
                    'spawn_command': 'p_only',
                    'spawn_p_chance': 50
                }
            if 'auto_release' not in config:
                config['auto_release'] = {
                    'enabled': False,
                    'interval': 50,  # Alle X Catches releasen
                }
            # Migration: autobuyer spawn command settings
            ab = config.get('autobuyer', {})
            if 'spawn_command' not in ab:
                ab['spawn_command'] = 'p_only'
            if 'spawn_p_chance' not in ab:
                ab['spawn_p_chance'] = 50
            if ab:
                config['autobuyer'] = ab
            if 'alarm_volume' not in config:
                config['alarm_volume'] = 33  # 0-100
            if 'auto_quest_renewer' not in config:
                config['auto_quest_renewer'] = {
                    'enabled': False,
                    'battle_quests': True,    # "Defeat", "Battle", "Battles"
                    'fish_quests': True,      # "Pokemon from Fishing", "Fish"
                    'receive_quests': True,   # "from another player"
                    'catch_quests': True,     # "Encounter", "Catch"
                }
            # Migration: auto_quest_claim
            if 'auto_quest_claim' not in config:
                config['auto_quest_claim'] = {
                    'enabled': True,
                    'interval_minutes': 130,  # min 120 (2h); default 2h10m
                    'pause_seconds': 20,      # min 20
                }
            if 'proxy' not in config:
                config['proxy'] = ''
            if 'webhook' not in config:
                config['webhook'] = {
                    'enabled': False,
                    'url': '',
                    'notify_rarities': ['legendary', 'shiny'],
                    'notify_fled': True,
                    'notify_catch_limit': True,
                    'forward_pokemeow_embed': True,
                    'egg_hatch_enabled': False,
                    'egg_hatch_notify_rarities': ['shiny'],
                }
            # Migration: forward_pokemeow_embed hinzufuegen falls fehlend
            if 'forward_pokemeow_embed' not in config.get('webhook', {}):
                config['webhook']['forward_pokemeow_embed'] = True
            # Migration: egg_hatch_enabled + egg_hatch_notify_rarities
            if 'egg_hatch_enabled' not in config.get('webhook', {}):
                config['webhook']['egg_hatch_enabled'] = False
            if 'egg_hatch_notify_rarities' not in config.get('webhook', {}):
                config['webhook']['egg_hatch_notify_rarities'] = ['shiny']
            # Migration: alarm_repeat
            if 'alarm_repeat' not in config:
                config['alarm_repeat'] = 1
            # Migration: event_pokemon
            if 'event_pokemon' not in config:
                config['event_pokemon'] = {
                    'premierball_enabled': True,
                    'masterball_enabled': True,
                    'webhook_enabled': True,  # Send Event Pokemon to private webhook
                    'event_ball_lower': 'prb',
                    'event_ball_upper': 'mb',
                }
            # Migration: add webhook_enabled to event_pokemon if missing
            if 'webhook_enabled' not in config.get('event_pokemon', {}):
                config['event_pokemon']['webhook_enabled'] = True
            # Migration: add configurable event ball choices 
            if 'event_ball_lower' not in config.get('event_pokemon', {}):
                config['event_pokemon']['event_ball_lower'] = 'prb'
            if 'event_ball_upper' not in config.get('event_pokemon', {}):
                config['event_pokemon']['event_ball_upper'] = 'mb'
            # Migration: startup_lootbox & startup_grazz
            if 'startup_lootbox' not in config:
                config['startup_lootbox'] = False
            if 'startup_grazz' not in config:
                config['startup_grazz'] = False
            # Migration: custom_message spawn command settings
            cm = config.get('custom_message', {})
            if 'command' not in cm:
                cm['command'] = 'p_only'
            if 'p_chance' not in cm:
                cm['p_chance'] = 50
            if cm:
                config['custom_message'] = cm
            
            return config
        else:
            default_config = {
                'token': 'Your_Discord_Token_Here',
                'channel_id': 'Your_Channel_ID_Here',
                'daily_enabled': False,
                'hunt_enabled': False,
                'swap_enabled': False,
                'quest_enabled': False,
                'fish_enabled': False,
                'fish_interval': 2,
                'auto_catch_enabled': True,
                'notification_enabled': True,
                'sound_enabled': True,
                'egg_enabled': False,
                'twocaptcha_api_key': '',
                'anticaptcha_api_key': '',
                'auto_solve_captcha': True,
                'captcha_service': 'catchbot_ai',
                'captcha_max_retries': 3,
                'autobuyer': {
                    'enabled': False,
                    'pb': {'threshold': 10, 'amount': 200},
                    'gb': {'threshold': 10, 'amount': 100},
                    'ub': {'threshold': 10, 'amount': 25},
                    'mb': {'threshold': 1, 'amount': 1}
                },
                'catch_rules': {
                    'common': 'pb',
                    'uncommon': 'pb',
                    'rare': 'gb',
                    'super_rare': 'ub',
                    'legendary': 'mb',
                    'shiny': 'mb',
                    'golden': 'mb'
                },
                'pokemon_whitelist': {},
                'auto_release': {
                    'enabled': False,
                    'interval': 50,
                },
                'alarm_volume': 33,
                'auto_quest_renewer': {
                    'enabled': False,
                    'battle_quests': True,
                    'fish_quests': True,
                    'receive_quests': True,
                    'catch_quests': False,
                },
                'auto_quest_claim': {
                    'enabled': False,
                    'interval_minutes': 130,  # min 120 (2h); default 2h10m
                    'pause_seconds': 20,      # min 20
                },
                'proxy': '',
                'alarm_repeat': 1,
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'notify_rarities': ['legendary', 'shiny'],
                    'notify_fled': True,
                    'notify_catch_limit': True,
                    'egg_hatch_enabled': False,
                    'egg_hatch_notify_rarities': ['shiny'],
                },
                'event_pokemon': {
                    'premierball_enabled': True,
                    'masterball_enabled': True,
                    'webhook_enabled': True,  # Send Event Pokemon to private webhook
                    'event_ball_lower': 'prb',  # Ball for Event Common-Super Rare
                    'event_ball_upper': 'mb',   # Ball for Event Legendary & Shiny
                },
                'startup_lootbox': False,
                'startup_grazz': False,
                'anti_ban': {
                    'enabled': False,
                    'pause_interval_min': 60,
                    'pause_interval_max': 180,
                    'pause_duration_min': 10,
                    'pause_duration_max': 30,
                    'catch_reaction_min': 1,
                    'catch_reaction_max': 3,
                    'spawn_delay_min': 11,
                    'spawn_delay_max': 15,
                },
                'custom_message': {
                    'enabled': False,
                    'message': '',
                    'chance': 50,
                },
                'custom_message_fish': {
                    'enabled': False,
                    'message': '',
                    'chance': 50,
                },
                'rate_limit_protection': {
                    'enabled': True,
                    'max_no_response': 3,       # Sleep after X commands without response
                    'sleep_min': 200,            # Min sleep time in seconds
                    'sleep_max': 400,            # Max sleep time in seconds
                },
            }
            self.save_config(default_config)
            return default_config
    
    def save_config(self, config=None):
        """Speichert die Konfiguration"""
        if config is None:
            config = self.config
        with open(self.config_path, 'w') as f:
            json.dump(config, indent=4, fp=f)
    
