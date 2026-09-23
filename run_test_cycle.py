import sys
import io
import time

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from src.config import cfg
cfg.reload()
from src.llm_client import llm
llm._refresh()
from src.agent_runner import run_agent
from src.memory import memory
from src.reward_system import rewards

print("=== STARTING LIVE END-TO-END AUTONOMOUS CYCLE TEST ===")
before = memory.get_stats()
print(f"Soul State BEFORE: Level {before['level']} | XP {before['xp']} | Tasks {before['tasks_completed']}")

t0 = time.time()
result = run_agent(autonomous=True)
elapsed = time.time() - t0

if result:
    rewards.on_task_completed(task_title="Live Autonomous Run", task_type="autonomous_cycle")

after = memory.get_stats()
print("\n=== LIVE TEST EXECUTION SUMMARY ===")
print(f"run_agent Result: {result} | Time: {elapsed:.1f}s")
print(f"Soul State AFTER : Level {after['level']} | XP {after['xp']} | Tasks {after['tasks_completed']}")
print("====================================")
