"""
sound_alert.py — Audio alerts for Penniless AI Agent

Plays distinctive audio tones using Windows winsound.Beep():
- "earn": Victory coin chime on receiving USDC earnings
- "transaction": Treasury / bank transfer confirmation chime
- "warning": Vitality / hunger alert when energy drops below 30%
- "critical": Near-death survival alert when energy drops below 10%
"""
from __future__ import annotations

import sys
import threading
import time

_HAS_WINSOUND = False
if sys.platform == "win32":
    try:
        import winsound
        _HAS_WINSOUND = True
    except Exception:
        _HAS_WINSOUND = False

_SOUND_LOCK = threading.Lock()


def _play_tones_sync(tone: str) -> None:
    """Execute audio frequency sequence synchronously, protected by lock."""
    with _SOUND_LOCK:
        if _HAS_WINSOUND:
            try:
                if tone == "earn":
                    # Coin victory fanfare: D5 -> G5 -> C6
                    winsound.Beep(587, 90)
                    time.sleep(0.03)
                    winsound.Beep(784, 90)
                    time.sleep(0.03)
                    winsound.Beep(1046, 180)
                elif tone == "transaction":
                    # Bank cash transfer tone: A5 -> E6
                    winsound.Beep(880, 100)
                    time.sleep(0.04)
                    winsound.Beep(1318, 160)
                elif tone == "warning":
                    # Vitality low alert: A4
                    winsound.Beep(440, 220)
                elif tone == "critical":
                    # Critical survival alert: Low warning
                    winsound.Beep(350, 180)
                    time.sleep(0.05)
                    winsound.Beep(300, 260)
                else:
                    winsound.Beep(1000, 100)
                return
            except Exception:
                pass

        # Fallback to terminal bell if winsound fails
        try:
            sys.stdout.write("\a")
            sys.stdout.flush()
        except Exception:
            pass


def play_beep(tone: str = "earn", sync: bool = False) -> None:
    """
    Play an audio alert. Runs in a daemon thread by default
    so agent operations are never blocked.
    """
    if sync:
        _play_tones_sync(tone)
    else:
        t = threading.Thread(target=_play_tones_sync, args=(tone,), daemon=True)
        t.start()
