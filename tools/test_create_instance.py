import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path.cwd()
TOOL = ROOT / "action/K-Action_creator/tools/create_instance.py"

def make_vault(root: Path):
    (root / ".knowledge" / "state").mkdir(parents=True)
    (root / ".knowledge" / "events").mkdir(parents=True)
    manifest = root / ".knowledge" / "manifest.yaml"
    manifest.write_text(chr(10).join([
        "version: \"1\"",
        "action_types:",
        "  - id: software-system",
        "    creators: [software-system_dev]",
        "  - id: agent",
        "    creators: [agentic-software]",
    ]), encoding="utf-8")
    spec = root / "spec.md"
    spec.write_text(chr(10).join([
        "---",
        "spec_id: spec-001",
        "action_type: software-system",
        "intent: create",
        "subject: stock-analysis-system",
        "status: approved",
        "review_status: approved",
        "---",
        "# Spec",
        "requirements: build stock analysis system",
    ]), encoding="utf-8")
    return spec

def test_create_instance_creates_state_record_from_approved_spec():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        spec = make_vault(vault)
        env = dict(os.environ)
        env["KA_VAULT_ROOT"] = str(vault)
        p = subprocess.run([sys.executable, str(TOOL), "create", str(spec)], env=env, capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr
        state = vault / ".knowledge/state/action-instances.json"
        assert state.exists()
        data = json.loads(state.read_text(encoding="utf-8"))
        inst = next(i for i in data["instances"] if i["spec_id"] == "spec-001")
        assert inst["action_type"] == "software-system"
        assert inst["provider"] == "software-system_dev"
        assert inst["state"] == "created"
        assert inst["subject"] == "stock-analysis-system"
        events = "".join(f.read_text(encoding="utf-8") for f in (vault / ".knowledge/events").glob("events-*.jsonl"))
        assert "action.instance.created" in events

def test_create_instance_rejects_unapproved_and_unknown_type():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        spec = make_vault(vault)
        (root := spec.parent)
        # unapproved
        un = root / "spec-unapproved.md"
        un.write_text(spec.read_text(encoding="utf-8").replace("status: approved", "status: proposed", 1).replace("review_status: approved", "review_status: needs_review", 1), encoding="utf-8")
        env = dict(os.environ)
        env["KA_VAULT_ROOT"] = str(vault)
        p1 = subprocess.run([sys.executable, str(TOOL), "create", str(un)], env=env, capture_output=True, text=True, timeout=60)
        assert p1.returncode == 2, p1.stdout
        # unknown type
        unk = root / "spec-unknown.md"
        unk.write_text(spec.read_text(encoding="utf-8").replace("action_type: software-system", "action_type: quantum-computer", 1), encoding="utf-8")
        p2 = subprocess.run([sys.executable, str(TOOL), "create", str(unk)], env=env, capture_output=True, text=True, timeout=60)
        assert p2.returncode == 2, p2.stdout

