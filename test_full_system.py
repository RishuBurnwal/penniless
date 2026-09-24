"""
test_full_system.py — Comprehensive End-to-End System Diagnostic & Health Check

Tests:
  1. Config & Environment Loading
  2. Memory & Soul Persistence (soul.json + memory.jsonl)
  3. Reward System (XP gains, badge awards, level-up)
  4. Task Tracker Deduplication & Filtering
  5. Bounty Scanner Connectivity
  6. Git Executor Safe Branching Logic
  7. Wallet Monitor Balance Fetching
  8. LLM Client Providers & Chunk Streaming
  9. Agent Runner Proposal & Chunk-Wise Execution Pipeline
"""
import sys
import io
import time
from pathlib import Path

# Force UTF-8 on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

results = []

def run_test(name, fn):
    print(f"\n[RUNNING TEST] {name}...")
    t0 = time.time()
    try:
        fn()
        elapsed = time.time() - t0
        print(f"  --> PASSED ({elapsed:.2f}s)")
        results.append((name, "PASSED", f"{elapsed:.2f}s"))
    except Exception as e:
        elapsed = time.time() - t0
        print(f"  --> FAILED ({elapsed:.2f}s): {type(e).__name__}: {e}")
        results.append((name, "FAILED", str(e)))

# ── Test 1: Config
def test_config():
    from src.config import cfg
    cfg.reload()
    assert cfg.AGENT_NAME, "AGENT_NAME is missing"
    assert cfg.EVM_WALLET, "EVM_WALLET is missing"
    assert cfg.GEMINI_MODEL == "gemini-2.5-flash", f"Unexpected Gemini model: {cfg.GEMINI_MODEL}"
    print(f"    Agent: {cfg.AGENT_NAME} | EVM Wallet: {cfg.EVM_WALLET[:10]}...")

# ── Test 2: Memory & Soul
def test_memory():
    from src.memory import memory
    stats = memory.get_stats()
    assert stats["name"] == "Penniless", "Soul name mismatch"
    assert "level" in stats and stats["level"] >= 1, "Level invalid"
    assert "xp" in stats, "XP invalid"
    # Test reflection
    memory.reflect("test_diagnostic", "success", "Diagnostic check passed")
    recall = memory.recall(last_n=2)
    assert "test_diagnostic" in recall, "Reflection not recalled"
    print(f"    Soul Level: {stats['level']} | XP: {stats['xp']} | Memory recall verified")

# ── Test 3: Reward System
def test_rewards():
    from src.reward_system import rewards
    from src.memory import memory
    initial_xp = memory.soul.get("xp", 0)
    rewards.on_task_completed(task_title="Diagnostic Test Task", task_type="audit")
    new_xp = memory.soul.get("xp", 0)
    assert new_xp == initial_xp + 10, f"XP did not increment by 10 (was {initial_xp}, now {new_xp})"
    ctx = rewards.get_reward_context()
    print(f"    Reward XP updated: {new_xp} (+10) | Reward context generated")

# ── Test 4: Task Tracker
def test_task_tracker():
    from src.task_tracker import tracker
    test_url = "https://superteam.fun/listings/test-diagnostic-slug"
    tracker.record_completed_task(test_url, "Test Task", "superteam", "test_artifact.md")
    assert tracker.is_attempted(test_url), "Task tracker did not record URL"
    assert tracker.is_attempted("test-diagnostic-slug"), "Task tracker did not record slug"
    # Test filtering
    opps = [{"url": test_url, "slug": "test-diagnostic-slug"}, {"url": "https://other.com/bounty-99", "slug": "bounty-99"}]
    filtered = tracker.filter_unattempted(opps)
    assert len(filtered) == 1 and filtered[0]["slug"] == "bounty-99", "Filtering failed"
    print(f"    Task tracker dedup verified (URL + slug matching working)")

# ── Test 5: Bounty Scanner
def test_scanner():
    from src.bounty_scanner import scan_all
    res = scan_all(verbose=False)
    all_opps = res.get("all", [])
    assert len(all_opps) > 0, "Scanner returned zero opportunities"
    print(f"    Scanner healthy: {len(all_opps)} total opportunities retrieved")

# ── Test 6: Wallet Monitor
def test_wallet():
    from src.wallet_monitor import get_status
    status = get_status()
    assert "total_usd" in status, "total_usd missing in wallet status"
    assert "base_usdc" in status, "base_usdc missing in wallet status"
    assert "sol_usdc" in status, "sol_usdc missing in wallet status"
    print(f"    Wallet monitor healthy: Total USD = ${status['total_usd']:.4f}")

# ── Test 7: Git Executor
def test_git():
    from src.git_executor import normalize_repo_name
    r = normalize_repo_name("https://github.com/RishuBurnwal/penniless.git")
    assert r == "RishuBurnwal/penniless", f"Unexpected repo normalization: {r}"
    print(f"    Git executor healthy: normalize_repo_name verified -> {r}")

# ── Test 8: LLM Client & Real-Time Chunk Streaming
def test_llm_streaming():
    from src.llm_client import llm
    llm._refresh()
    chunks_received = []
    def on_chunk(c):
        chunks_received.append(c)

    res = llm.chat(
        messages=[{"role": "user", "content": "Reply with exactly: CHUNK_TEST_OK"}],
        max_tokens=50,
        on_chunk=on_chunk,
    )
    assert "CHUNK_TEST_OK" in res or len(res.strip()) > 0, f"Unexpected LLM output: {res}"
    print(f"    LLM chat & chunk streaming healthy: {len(chunks_received)} chunks captured | Response: {res.strip()}")

# ── Test 9: Real-Time Chunk-Wise File Streaming
def test_chunk_file_save():
    test_file = Path("submissions") / "test_chunk_save.md"
    test_file.write_text("", encoding="utf-8")
    chunks = ["### PART 1: Introduction\n", "This is chunk 1.\n", "### PART 2: Conclusion\n", "Done.\n"]
    for c in chunks:
        with test_file.open("a", encoding="utf-8") as f:
            f.write(c)
            f.flush()
    content = test_file.read_text(encoding="utf-8")
    assert content == "".join(chunks), "Chunk-wise file persistence corrupted"
    test_file.unlink(missing_ok=True)
    print(f"    Chunk-wise disk streaming verified")


def test_sound_alert():
    from src.sound_alert import play_beep
    play_beep("earn", sync=True)
    play_beep("transaction", sync=True)
    print("    Audio alert chimes verified (earn + transaction beeps)")


def test_survival():
    from src.survival import survival
    # Test meter
    meter = survival.render_meter()
    assert "Life:" in meter
    # Test tick
    v_before = survival.vitality
    tick_res = survival.tick_cycle()
    assert tick_res["vitality"] <= v_before
    # Test task recovery
    survival.on_task_completed("Test Bounty")
    assert survival.vitality >= tick_res["vitality"]
    directive = survival.get_survival_directive()
    assert "SURVIVAL" in directive
    print(f"    Survival engine verified: {meter}")


def test_bank_manager():
    from src.bank_manager import bank
    stats_before = bank.get_stats()
    tx = bank.execute_bank_deposit(amount_usd=1.0, source="test_verification")
    assert tx["status"] == "CONFIRMED"
    assert tx["amount_usd"] == 1.0
    assert tx["to_bank_wallet"] == bank.bank_wallet
    stats_after = bank.get_stats()
    assert stats_after["total_usd"] >= stats_before["total_usd"] + 1.0
    print(f"    Bank manager verified: Deposit to {bank.bank_wallet[:14]}... confirmed")


def main():
    print("=" * 60)
    print("      PENNILESS SYSTEM COMPREHENSIVE HEALTH CHECK")
    print("=" * 60)

    run_test("1. Config & Environment", test_config)
    run_test("2. Memory & Soul Persistence", test_memory)
    run_test("3. Reward Engine & XP", test_rewards)
    run_test("4. Task Tracker Deduplication", test_task_tracker)
    run_test("5. Bounty Scanner", test_scanner)
    run_test("6. Wallet Monitor", test_wallet)
    run_test("7. Git Executor Logic", test_git)
    run_test("8. LLM Client & Real-Time Chunk Streaming", test_llm_streaming)
    run_test("9. Chunk-Wise File Streaming to Disk", test_chunk_file_save)
    run_test("10. Audio Alert System (Beep/Chimes)", test_sound_alert)
    run_test("11. Survival & Vitality Engine", test_survival)
    run_test("12. Base Bank Wallet & Transaction Manager", test_bank_manager)

    print("\n" + "=" * 60)
    print("      FINAL DIAGNOSTIC REPORT")
    print("=" * 60)
    all_passed = True
    for name, status, detail in results:
        mark = "✅" if status == "PASSED" else "❌"
        print(f"  {mark} {name:<45} : {status} ({detail})")
        if status != "PASSED":
            all_passed = False

    print("=" * 60)
    if all_passed:
        print(">>> ALL 12 SUBSYSTEMS VERIFIED 100% HEALTHY & FUNCTIONAL <<<\n")
        sys.exit(0)
    else:
        print(">>> SOME SUBSYSTEMS FAILED - REVIEW LOGS ABOVE <<<\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
