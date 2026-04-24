"""Core CatchBot class. Composes every mixin and holds __init__, _setup_client, check_for_updates."""
import os
import sys
import re
import json
import asyncio
import atexit
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

from utils.platform import (
    CATCHBOT_VERSION,
    HAS_AIOHTTP_SOCKS,
    WINDOWS,
)

if HAS_AIOHTTP_SOCKS:
    try:
        from aiohttp_socks import ProxyConnector
    except ImportError:
        ProxyConnector = None
else:
    ProxyConnector = None

# === Mixin imports ===
from config.io import ConfigMixin
from ui.logs import LogsMixin
from ui.header import HeaderMixin
from ui.menus import MenuMixin
from utils.pokemon_names import PokemonNamesMixin
from utils.discord_io import DiscordIOMixin
from utils.stats import StatsMixin
from utils.net import NetMixin
from captcha.detection import CaptchaDetectionMixin
from captcha.services import CaptchaServicesMixin
from captcha.menus import CaptchaMenuMixin
from catching.catch import CatchingMixin
from catching.results import CatchResultsMixin
from catching.fishing import FishingMixin
from features.egg import EggMixin
from features.autobuyer import AutoBuyerMixin
from features.auto_release import AutoReleaseMixin
from features.anti_ban import AntiBanMixin
from features.rate_limit import RateLimitMixin
from features.quests import QuestsMixin
from features.remote_control import RemoteControlMixin
from webhooks.sender import WebhookMixin
from core.main_loop import MainLoopMixin


class CatchBot(
    ConfigMixin,
    LogsMixin,
    HeaderMixin,
    MenuMixin,
    PokemonNamesMixin,
    DiscordIOMixin,
    StatsMixin,
    NetMixin,
    CaptchaDetectionMixin,
    CaptchaServicesMixin,
    CaptchaMenuMixin,
    CatchingMixin,
    CatchResultsMixin,
    FishingMixin,
    EggMixin,
    AutoBuyerMixin,
    AutoReleaseMixin,
    AntiBanMixin,
    RateLimitMixin,
    QuestsMixin,
    RemoteControlMixin,
    WebhookMixin,
    MainLoopMixin,
):
    # === SHARED SUCCESS WEBHOOK (disabled by default) ===
    # Set to a Discord webhook URL (e.g. "https://discord.com/api/webhooks/...")
    # to broadcast every successful catch to a shared channel.
    # When None or empty, the shared-feed senders are silently skipped.
    SHARED_SUCCESS_WEBHOOK = None
    CATCHBOT_VERSION = "v6.2"

    def __init__(self, account_name=None):
        # === MULTI-ACCOUNT SUPPORT ===
        self.account_name = account_name  # e.g. "acc1", "main", "alt" etc.
        
        # Separate file paths per account
        if account_name:
            self.config_path = f'config_{account_name}.json'
            self.stats_path = f'stats_{account_name}.json'
            self.logs_dir = os.path.join('logs', account_name)
            self.prefix = f'[{account_name.upper()}] '
        else:
            self.config_path = 'config.json'
            self.stats_path = 'stats.json'
            self.logs_dir = 'logs'
            self.prefix = ''
        
        self.client = None
        self.running = False
        self.startup_phase = True    # True during startup (inv, egg, dailys) - no catching
        self.paused = False          # Manually paused (Hotkey)
        self.anti_ban_paused = False # Anti-Ban random pause active
        self.anti_ban_next_pause = None  # Next scheduled pause time
        self.captcha_active = False   # Captcha detected -> Bot waiting
        self.captcha_solve_attempts = 0  # Current number of auto-solve attempts
        self.captcha_detected_at = None  # Timestamp when captcha was detected
        self.captcha_timeout_triggered = False  # True if 70s timeout alarm fired
        self.captcha_last_message = None  # Last captcha message for retry
        self._solving_captcha = False     # Dedup guard: prevents duplicate concurrent solve calls
        self.config = self.load_config()
        self.logs = []
        self.p_counter = 0
        self.catching = False
        self.start_time = None
        self.ready_event = None
        self.egg_busy = False         # Egg action in progress
        self.temp_banned = False      # Temporarily banned (captcha failed)
        self.buying_balls = False     # AutoBuyer currently purchasing
        self.catch_limit_reached = False  # Daily catch limit reached
        self.last_catch_result = None     # Last catch result ("caught"/"fled"/None)
        self.last_catch_is_event = False  # Whether last catch attempt was an Event Pokemon
        self.releasing = False            # Auto-Release in progress
        self.release_counter = 0          # Counter for catches since last release
        self.doing_dailys = False         # Daily tasks in progress (disables scanning)
        self.fishing_active = False       # Fishing sequence in progress
        self._fish_rarity = None          # Rarity from MeowHelper for current fish spawn
        self._fish_forced_ball = None     # Forced ball ('pb'/'gb'/'ub'/'prb'/'mb') parsed from PokeMeow's *_unlocked emoji on fish spawn
        self._quest_renew_scrolls = None   # Track scroll count for AutoQuestRenewer
        self._quest_renew_event = None     # Event to wait for quest response
        self._last_quest_claim_ts = None   # monotonic ts of last AutoQuestClaim run (None = set on main loop start)
        self._last_captcha_task_id = None   # Task ID of last captcha attempt (for report)
        self._last_captcha_service = None   # Service of last captcha attempt (for report)
        
        # === RATE LIMIT PROTECTION ===
        self._no_response_counter = 0        # Consecutive commands without PokeMeow response
        self._last_pokemeow_response = None  # Timestamp of last PokeMeow response
        self._rate_limit_sleeping = False    # Currently in rate-limit sleep mode

        
        # === SESSION STATISTICS ===
        self.session_stats = {
            'total_caught': 0,
            'total_fled': 0,
            'total_encounters': 0,
            'total_fished': 0,
            'total_fished_fled': 0,
            'caught_by_rarity': {},    # e.g. {'Common': 5, 'Rare': 2}
            'fled_by_rarity': {},
            'best_catches': [],        # List of best catches (Legendary, Shiny, etc.)
            'session_start': None,
        }
        
        # === PERSISTENT STATS (Shiny/Legendary Counter) ===
        self.persistent_stats = self.load_persistent_stats()
        
        # === LOAD POKEMON NAMES ===
        self.pokemon_names = self.load_pokemon_names()
        
        # Create logs directory
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Save logs on exit
        atexit.register(self.save_logs_on_stop)
        
        # Create client
        self._setup_client()
        
    def _setup_client(self):
        """Creates a new Discord Client with all Event Handlers"""
        import discord
        
        # For discord.py-self selfbots, no intents needed
        client_kwargs = {}
        proxy_url = self.config.get('proxy', '')
        
        if proxy_url:
            parsed = urlparse(proxy_url)
            
            if parsed.scheme.startswith('socks'):
                # SOCKS Proxy (requires aiohttp_socks)
                if HAS_AIOHTTP_SOCKS:
                    try:
                        connector = ProxyConnector.from_url(proxy_url)
                        client_kwargs['connector'] = connector
                    except Exception as e:
                        print(f"{Fore.RED}⚠ SOCKS Proxy Error: {str(e)}{Style.RESET_ALL}")
                else:
                    print(f"{Fore.RED}⚠ 'aiohttp_socks' is required for SOCKS proxies!{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}  Install with: py -m pip install aiohttp_socks{Style.RESET_ALL}")
            else:
                # HTTP/HTTPS Proxy
                if parsed.username:
                    import aiohttp
                    clean_url = f"{parsed.scheme}://{parsed.hostname}"
                    if parsed.port:
                        clean_url += f":{parsed.port}"
                    client_kwargs['proxy'] = clean_url
                    client_kwargs['proxy_auth'] = aiohttp.BasicAuth(
                        parsed.username, parsed.password or ''
                    )
                else:
                    client_kwargs['proxy'] = proxy_url
        
        self.client = discord.Client(**client_kwargs)
        self.ready_event = None
        
        @self.client.event
        async def on_ready():
            self.log(f'Bot logged in as {self.client.user}')
            print(f'\n{Fore.GREEN}✓ Successfully logged in as {self.client.user}{Style.RESET_ALL}')
            # Check for updates asynchronously
            asyncio.create_task(self.check_for_updates())
            # Signal that the bot is ready
            if self.ready_event:
                self.ready_event.set()
    
    async def check_for_updates(self):
        """Check GitHub latest release tag for newer bot version"""
        try:
            import aiohttp
            import json
            
            # GitHub API for latest release
            api_url = "https://api.github.com/repos/MyNameIsKillua/pokemeow-selfbot/releases/latest"
            
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            remote_version = data.get('tag_name', '').strip()
                            
                            if remote_version:
                                local_ver = self._parse_version(CATCHBOT_VERSION)
                                remote_ver = self._parse_version(remote_version)
                                
                                if remote_ver > local_ver:
                                    download_url = data.get('html_url', 'github.com/MyNameIsKillua/pokemeow-selfbot/releases')
                                    print(f"\n{Fore.GREEN}{'='*50}{Style.RESET_ALL}")
                                    print(f"{Fore.YELLOW}  [UPDATE] New version available!{Style.RESET_ALL}")
                                    print(f"{Fore.YELLOW}  Local:  {CATCHBOT_VERSION}{Style.RESET_ALL}")
                                    print(f"{Fore.YELLOW}  Remote: {remote_version}{Style.RESET_ALL}")
                                    print(f"{Fore.YELLOW}  Download: {download_url}{Style.RESET_ALL}")
                                    print(f"{Fore.GREEN}{'='*50}{Style.RESET_ALL}\n")
                                    
                                    # Send to control channel if available
                                    rc = self.config.get('remote_control', {})
                                    if rc.get('enabled', False) and rc.get('control_channel_id', ''):
                                        try:
                                            ch = self.client.get_channel(int(rc.get('control_channel_id')))
                                            if ch:
                                                await ch.send(f"```yaml\n[UPDATE] New version available!\nLocal:  {CATCHBOT_VERSION}\nRemote: {remote_version}\nDownload: {download_url}```")
                                        except:
                                            pass
                except asyncio.TimeoutError:
                    pass  # Silently fail if GitHub is slow
        except Exception as e:
            pass  # Silently fail if update check fails
        
        @self.client.event
        async def on_message(message):
            # === REMOTE CONTROL: Check for commands in control channel ===
            rc = self.config.get('remote_control', {})
            if rc.get('enabled', False) and rc.get('control_channel_id', ''):
                if str(message.channel.id) == str(rc.get('control_channel_id', '')):
                    # Check whitelist if configured
                    whitelist = rc.get('whitelist_user_ids', [])
                    if not whitelist or str(message.author.id) in [str(uid) for uid in whitelist]:
                        await self.handle_remote_command(message)
                    return
            
            # DEBUG: Log all messages in channel (helps with Multi-Account debugging)
            if str(message.channel.id) == self.config.get('channel_id', ''):
                has_embeds = len(message.embeds) > 0
                has_components = hasattr(message, 'components') and len(message.components) > 0
                num_buttons = 0
                if has_components:
                    try:
                        num_buttons = len(message.components[0].children)
                    except Exception:
                        pass
                self.log(f"[MSG] Author={message.author} (ID={message.author.id}), Embeds={len(message.embeds)}, Buttons={num_buttons}, Content={message.content[:80] if message.content else '(empty)'}")
            
            # Only in our configured channel
            if str(message.channel.id) != self.config.get('channel_id', ''):
                return
            
            # Ignore own messages
            if message.author.id == self.client.user.id:
                return
            
            # === CAPTCHA DETECTION (always active, independent of Auto-Catch) ===
            await self.check_captcha(message)
            
            # === DAILY CATCH LIMIT DETECTION (always active) ===
            await self.check_catch_limit(message)
            
            # === CATCH RESULT DETECTION ===
            # PokeMeow sends catch results as message edits (on_message_edit).
            # Do NOT call check_catch_result here to avoid duplicate webhook posts.
            
            # === EGG DETECTION (if enabled) ===
            if self.config.get('egg_enabled', False) and not self.paused and not self.captcha_active and not self.temp_banned and not self.catch_limit_reached:
                await self.check_egg(message)
            
            # === AUTOBUYER: Check ball inventory ===
            if self.config.get('autobuyer', {}).get('enabled', False) and not self.paused and not self.captcha_active and not self.temp_banned and not self.catch_limit_reached:
                await self.check_ball_stock(message)
            
            # === AUTO-RELEASE: Release duplicates ===
            if self.config.get('auto_release', {}).get('enabled', False) and not self.paused and not self.captcha_active and not self.temp_banned and not self.catch_limit_reached:
                await self.check_auto_release(message)
            
            # === AUTO QUEST RENEWER: Capture quest responses ===
            if self._quest_renew_event is not None and not self._quest_renew_event.is_set():
                await self._handle_quest_response(message)
            
            # === AUTO-CATCH (only when enabled and not paused) ===
            if not self.config.get('auto_catch_enabled', True):
                self.log(f"[GUARD] Auto-Catch is disabled!")
                return
            
            if self.startup_phase or self.paused or self.anti_ban_paused or self.captcha_active or self.egg_busy or self.temp_banned or self.catch_limit_reached or self.releasing or self.doing_dailys:
                self.log(f"[GUARD] Auto-Catch blocked: startup={self.startup_phase}, paused={self.paused}, anti_ban={self.anti_ban_paused}, captcha={self.captcha_active}, egg={self.egg_busy}, banned={self.temp_banned}, limit={self.catch_limit_reached}, releasing={self.releasing}, dailys={self.doing_dailys}")
                return
            
            await self.check_and_catch_pokemon(message)
        
        @self.client.event
        async def on_message_edit(before, after):
            """Detects edited messages (PokeMeow edits the captcha message after solving)"""
            # Only in our configured channel
            if str(after.channel.id) != self.config.get('channel_id', ''):
                return
            
            # Ignore own messages
            if after.author.id == self.client.user.id:
                return
            
            # Check captcha if active
            if self.captcha_active:
                await self.check_captcha(after)
            
            # === DAILY CATCH LIMIT also check on edited messages ===
            await self.check_catch_limit(after)
            
            # === CATCH RESULT DETECTION on edited messages ===
            await self.check_catch_result(after)
            
            # === AUTOBUYER: Also check ball inventory on edited messages ===
            # PokeMeow sends the catch confirmation (with "Balls left") often as an Edit
            if self.config.get('autobuyer', {}).get('enabled', False) and not self.paused and not self.captcha_active and not self.temp_banned and not self.catch_limit_reached:
                await self.check_ball_stock(after)
            
            # === AUTO-RELEASE: Also check on edited messages ===
            if self.config.get('auto_release', {}).get('enabled', False) and not self.paused and not self.captcha_active and not self.temp_banned and not self.catch_limit_reached:
                await self.check_auto_release(after)
            
            # === AUTO QUEST RENEWER: Also capture on edited messages ===
            if self._quest_renew_event is not None and not self._quest_renew_event.is_set():
                await self._handle_quest_response(after)
