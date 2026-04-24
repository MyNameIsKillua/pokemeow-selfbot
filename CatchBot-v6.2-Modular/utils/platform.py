"""Platform-specific helpers, feature flags and shared constants used across modules."""
import os
import sys

# Bot version (used in startup screen and update checks)
CATCHBOT_VERSION = "v6.2"

# HTTP Requests for 2Captcha API
try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

# Windows-specific imports
try:
    import winsound
    import msvcrt
    WINDOWS = True
except ImportError:
    WINDOWS = False

# Desktop-Notification (Native Windows Toast - works in .exe / Nuitka)
HAS_PLYER = False  # Legacy flag kept for compatibility
HAS_TOAST = False
if os.name == 'nt':
    try:
        import ctypes
        from ctypes import wintypes
        HAS_TOAST = True
    except ImportError:
        HAS_TOAST = False


def _show_windows_toast(title, message, timeout=10):
    """Show a native Windows toast notification using PowerShell.
    Works reliably in .exe compiled with Nuitka."""
    if not os.name == 'nt':
        return
    try:
        import subprocess
        # Escape single quotes for PowerShell
        title_safe = title.replace("'", "''").replace('"', '`"')
        msg_safe = message.replace("'", "''").replace('"', '`"')
        # Use BurntToast if available, otherwise fallback to .NET
        ps_script = f"""
Add-Type -AssemblyName System.Windows.Forms
$n = New-Object System.Windows.Forms.NotifyIcon
$n.Icon = [System.Drawing.SystemIcons]::Information
$n.BalloonTipTitle = '{title_safe}'
$n.BalloonTipText = '{msg_safe}'
$n.Visible = $true
$n.ShowBalloonTip({timeout * 1000})
Start-Sleep -Seconds 3
$n.Dispose()
"""
        subprocess.Popen(
            ['powershell', '-WindowStyle', 'Hidden', '-Command', ps_script],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=0x08000000  # CREATE_NO_WINDOW
        )
    except Exception:
        pass


def _generate_alarm_wav(volume=50, frequency=700, duration_ms=400):
    """Generate a soft alarm WAV tone in memory with adjustable volume (0-100).
    Returns bytes of a valid WAV file."""
    import struct
    import math
    sample_rate = 22050
    num_samples = int(sample_rate * duration_ms / 1000)
    # Clamp volume 0-100, scale to amplitude (max 32767 for 16-bit)
    vol = max(0, min(100, volume)) / 100.0
    amplitude = int(32767 * vol * 0.6)  # 0.6 cap so even 100% isn't ear-splitting

    # Generate a pleasant sine wave with fade-in/fade-out
    samples = []
    fade_samples = int(num_samples * 0.15)  # 15% fade
    for i in range(num_samples):
        t = i / sample_rate
        # Gentle sine wave
        val = math.sin(2 * math.pi * frequency * t)
        # Apply fade envelope
        if i < fade_samples:
            val *= i / fade_samples
        elif i > num_samples - fade_samples:
            val *= (num_samples - i) / fade_samples
        samples.append(int(val * amplitude))

    # Build WAV file in memory
    data = struct.pack('<' + 'h' * len(samples), *samples)
    wav = bytearray()
    wav += b'RIFF'
    wav += struct.pack('<I', 36 + len(data))
    wav += b'WAVE'
    wav += b'fmt '
    wav += struct.pack('<I', 16)  # chunk size
    wav += struct.pack('<H', 1)   # PCM
    wav += struct.pack('<H', 1)   # mono
    wav += struct.pack('<I', sample_rate)
    wav += struct.pack('<I', sample_rate * 2)  # byte rate
    wav += struct.pack('<H', 2)   # block align
    wav += struct.pack('<H', 16)  # bits per sample
    wav += b'data'
    wav += struct.pack('<I', len(data))
    wav += data
    return bytes(wav)


# SOCKS Proxy Support (optional)
try:
    from aiohttp_socks import ProxyConnector
    HAS_AIOHTTP_SOCKS = True
except ImportError:
    HAS_AIOHTTP_SOCKS = False


def _is_compiled():
    """Prueft ob wir als kompilierte .exe laufen (PyInstaller ODER Nuitka)."""
    if getattr(sys, 'frozen', False):
        return True
    if globals().get('__compiled__', False):
        return True
    exe_name = os.path.basename(sys.executable).lower()
    if exe_name.endswith('.exe') and 'python' not in exe_name:
        return True
    return False


def _get_base_dir():
    """Gibt das Verzeichnis zurueck, in dem die .exe / .py Dateien liegen."""
    if _is_compiled():
        return os.path.dirname(os.path.abspath(sys.argv[0]))
    else:
        # utils/ is one level below the package root — go up one
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
