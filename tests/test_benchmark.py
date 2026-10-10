from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

import benchmark


ROOT = Path(__file__).resolve().parents[1]


class HarnessTests(unittest.TestCase):
    def generate(self, root: Path) -> Path:
        project = root / "northstar"
        subprocess.run([sys.executable, str(ROOT / "task" / "make_project.py"), str(project)], check=True,
                       capture_output=True, text=True)
        return project

    def check(self, project: Path) -> dict:
        process = subprocess.run([sys.executable, str(ROOT / "task" / "check.py"), str(project)],
                                 capture_output=True, text=True)
        return json.loads(process.stdout.strip().splitlines()[-1])

    def test_project_has_expected_files_and_baseline_fails_all_tasks(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.generate(Path(temp))
            self.assertGreaterEqual(sum(path.is_file() for path in project.rglob("*")), 160)
            self.assertEqual(self.check(project)["tasks_ok"], 0)

    def test_checker_accepts_a_complete_behavioral_fix(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.generate(Path(temp))

            tax = project / "src/billing/tax_policy.py"
            tax.write_text(tax.read_text().replace('Decimal("0.19")', 'Decimal("0.20")'))
            reporting = project / "src/billing/reporting.py"
            reporting.write_text(reporting.read_text().replace('Decimal("1.19")', 'Decimal("1.20")'))

            repository = project / "src/customers/repository.py"
            repository.write_text(repository.read_text().replace('"email", "country")', '"email", "country", "phone")'))
            serializers = project / "src/customers/serializers.py"
            serializers.write_text(serializers.read_text().replace('"email", "country")', '"email", "country", "phone")'))
            service = project / "src/customers/service.py"
            service.write_text(service.read_text().replace(
                '"country": data.get("country", "DE")}',
                '"country": data.get("country", "DE"), "phone": data.get("phone")}'))
            events = project / "src/customers/events.py"
            events.write_text(events.read_text().replace(
                '"country": customer.get("country")}',
                '"country": customer.get("country"), "phone": customer.get("phone")}'))

            reset = project / "src/identity/reset_tokens.py"
            reset.write_text(reset.read_text().replace(
                'now - token["issued_at"] < RESET_TTL_MINUTES',
                'now - token["issued_at"] < RESET_TTL_MINUTES * 60'))

            webhook = project / "src/payments/webhooks.py"
            webhook.write_text(webhook.read_text().replace(
                '    charge = payload["data"]["object"]',
                '    if not ledger.claim_webhook(event_id):\n'
                '        return {"processed": True, "duplicate": True, "event_id": event_id}\n'
                '    charge = payload["data"]["object"]'))
            result = self.check(project)
            self.assertEqual(result["tasks_ok"], 4, result)

    def test_verdict_prioritizes_correctness(self):
        plain = [{"tasks_ok": 3, "fresh_tokens": 1000, "wall_s": 50, "first_run_s": 50}]
        codebone = [{"tasks_ok": 4, "fresh_tokens": 1200, "wall_s": 60, "index_s": 2, "first_run_s": 62}]
        verdict, _, _ = benchmark.verdict_for(plain, codebone)
        self.assertEqual(verdict, "HELPS")

    def test_verdict_rejects_equal_but_more_expensive_run(self):
        plain = [{"tasks_ok": 4, "fresh_tokens": 1000, "wall_s": 50, "first_run_s": 50}]
        codebone = [{"tasks_ok": 4, "fresh_tokens": 1200, "wall_s": 60, "index_s": 2, "first_run_s": 62}]
        verdict, _, _ = benchmark.verdict_for(plain, codebone)
        self.assertEqual(verdict, "DOES NOT HELP")

    def test_efficiency_label_uses_human_direction(self):
        self.assertEqual(benchmark.efficiency_label(12.34, "less", "more"), "12.3% less")
        self.assertEqual(benchmark.efficiency_label(-12.34, "less", "more"), "12.3% more")

    def test_generator_preserves_existing_destination(self):
        with tempfile.TemporaryDirectory() as temp:
            project = self.generate(Path(temp))
            original = (project / "README.md").read_bytes()
            process = subprocess.run([sys.executable, str(benchmark.GENERATOR), str(project)],
                                     capture_output=True, text=True)
            self.assertNotEqual(process.returncode, 0)
            self.assertEqual((project / "README.md").read_bytes(), original)

    def test_failed_and_unpaired_runs_are_inconclusive(self):
        valid = {"tasks_ok": 4, "exit_code": 0, "fresh_tokens": 1000, "wall_s": 50}
        failed = {**valid, "exit_code": 1}
        self.assertEqual(benchmark.verdict_for([valid], [failed])[0], "INCONCLUSIVE")
        self.assertEqual(benchmark.verdict_for([valid, valid], [valid])[0], "INCONCLUSIVE")

    def test_timeout_is_recorded_and_workdir_cleaned(self):
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp) / "trial"
            work.mkdir()
            with patch.object(benchmark.tempfile, "mkdtemp", return_value=str(work)), \
                 patch.object(benchmark, "run_agent", side_effect=subprocess.TimeoutExpired("codex", 1)):
                row = benchmark.trial("plain", "codex", None, 1, ROOT, Path(sys.executable), False, "test", 1)
            self.assertEqual(row["exit_code"], 1)
            self.assertIn("TimeoutExpired", row["error"])
            self.assertFalse(work.exists())

    def test_codex_usage_counts_cached_input_separately(self):
        usage = benchmark.codex_usage([{"usage": {"input_tokens": 100, "cached_input_tokens": 80,
                                                 "output_tokens": 10}}])
        self.assertEqual(usage["fresh_tokens"], 30)
        self.assertEqual(usage["total_tokens"], 110)

    def test_claude_api_error_is_a_failed_process(self):
        process = subprocess.CompletedProcess([], 0, json.dumps({"is_error": True, "result": "Auth failed"}), "")
        with patch.object(benchmark, "run", return_value=process):
            row = benchmark.run_claude(ROOT, "test", None, 1)
        self.assertEqual(row["exit_code"], 1)

    def test_codex_json_output_is_parsed(self):
        events = [
            {"type": "item.completed", "item": {"type": "agent_message", "text": "Done"}},
            {"type": "turn.completed", "usage": {"input_tokens": 50, "output_tokens": 10}},
        ]
        process = subprocess.CompletedProcess([], 0, "\n".join(map(json.dumps, events)), "")
        with patch.object(benchmark, "run", return_value=process):
            row = benchmark.run_codex(ROOT, "test", "explicit-model", 1)
        self.assertEqual(row["response"], "Done")
        self.assertEqual(row["model"], "explicit-model")
        self.assertEqual(row["fresh_tokens"], 60)


if __name__ == "__main__":
    unittest.main()
