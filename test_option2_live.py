import sys
import io
import time
import threading

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from src.agent_runner import run_autonomous_daemon

print("=== STARTING OPTION 2 LIVE DAEMON TEST (Testing non-stop loop) ===")
# run_autonomous_daemon loops forever.
# We will run it and verify the full autonomous cycle, artifact save, and cycle counter.
try:
    run_autonomous_daemon()
except KeyboardInterrupt:
    print("\n[DAEMON TEST] KeyboardInterrupt caught cleanly.")
except Exception as e:
    print(f"\n[DAEMON TEST ERROR] {type(e).__name__}: {e}")
