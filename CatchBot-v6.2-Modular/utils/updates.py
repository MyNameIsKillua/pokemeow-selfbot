"""Synchronous GitHub release checker used on startup."""
from utils.platform import CATCHBOT_VERSION


def check_for_updates_sync():
    """Check GitHub for updates (synchronous version for startup)"""
    try:
        import urllib.request
        import json

        api_url = "https://api.github.com/repos/MyNameIsKillua/pokemeow-selfbot/releases/latest"
        req = urllib.request.Request(api_url, headers={'User-Agent': 'CatchBot'})

        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            remote_version = data.get('tag_name', '').strip()

            if remote_version:
                # Parse versions
                local_ver = CATCHBOT_VERSION.lstrip('v').split('.')
                remote_ver = remote_version.lstrip('v').split('.')

                # Convert to tuples for comparison
                try:
                    local_tuple = tuple(int(p) for p in local_ver)
                    remote_tuple = tuple(int(p) for p in remote_ver)

                    if remote_tuple > local_tuple:
                        download_url = data.get('html_url', 'github.com/MyNameIsKillua/pokemeow-selfbot/releases')
                        return True, remote_version, download_url
                except:
                    pass
    except:
        pass
    return False, None, None
