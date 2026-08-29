import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path.cwd()
TOOL = ROOT / "action/K-Action_creator/tools/create_instance.py"

def make_vault(root: Path, provider="software-system_dev", prov_impl=None):
    (root / ".knowledge" / "state").mkdir(parents=True)
    (root / ".knowledge" / "events").mkdir(parents=True)
    if prov_impl is not None:
        pp = root / "action" / provider
        pp.mkdir(parents=True, exist_ok=True)
        (pp / "design_model.py").write_text(prov_impl, encoding="utf-8")
    manifest = root / ".knowledge" / "manifest.yaml"
    manifest.write_text(chr(10).join([
        "version: \"1\"",
        "action_types:",
        f"  - id: software-system",
        f"    creators: [{provider}]",
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

PROVIDER_IMPL = chr(10).join([
    "def create_instance(spec, vault=None):",
    "    return {\"exit\": 0, \"instance\": {\"instance_type\": \"FakeSoftwareInstance/v1\", \"subject\": spec.get(\"subject\", \"\"), \"state\": \"created\"}}",
    "",
    "def schema():",
    "    return {\"exit\": 0, \"objects\": []}",
])

def test_create_instance_calls_provider_capability():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        spec = make_vault(vault, provider="fake_ss", prov_impl=PROVIDER_IMPL)
        env = dict(os.environ); env["KA_VAULT_ROOT"] = str(vault)
        p = subprocess.run([sys.executable, str(TOOL), "create", str(spec)], env=env, capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr
        data = json.loads((vault / ".knowledge/state/action-instances.json").read_text(encoding="utf-8"))
        inst = data["instances"][0]
        assert inst["provider"] == "fake_ss"
        assert inst["capability_instance"]["instance_type"] == "FakeSoftwareInstance/v1"
        assert inst["capability_instance"]["subject"] == "stock-analysis-system"

def test_create_instance_falls_back_to_record_without_provider():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        spec = make_vault(vault, provider="missing_provider")
        env = dict(os.environ); env["KA_VAULT_ROOT"] = str(vault)
        p = subprocess.run([sys.executable, str(TOOL), "create", str(spec)], env=env, capture_output=True, text=True, timeout=60)
        assert p.returncode == 0, p.stderr
        data = json.loads((vault / ".knowledge/state/action-instances.json").read_text(encoding="utf-8"))
        inst = data["instances"][0]
        assert inst["capability_instance"] is None
        assert inst["capability_error"]

def test_create_instance_rejects_unapproved_and_unknown_type():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        spec = make_vault(vault, provider="fake_ss", prov_impl=PROVIDER_IMPL)
        root = spec.parent
        un = root / "spec-unapproved.md"
        un.write_text(spec.read_text(encoding="utf-8").replace("status: approved", "status: proposed", 1).replace("review_status: approved", "review_status: needs_review", 1), encoding="utf-8")
        env = dict(os.environ); env["KA_VAULT_ROOT"] = str(vault)
        p1 = subprocess.run([sys.executable, str(TOOL), "create", str(un)], env=env, capture_output=True, text=True, timeout=60)
        assert p1.returncode == 2, p1.stdout
        unk = root / "spec-unknown.md"
        unk.write_text(spec.read_text(encoding="utf-8").replace("action_type: software-system", "action_type: quantum-computer", 1), encoding="utf-8")
        p2 = subprocess.run([sys.executable, str(TOOL), "create", str(unk)], env=env, capture_output=True, text=True, timeout=60)
        assert p2.returncode == 2, p2.stdout

