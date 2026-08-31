import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path.cwd()
TOOL = ROOT / "action/K-Action_orchestrator/tools/action_ops.py"

def make_vault(root: Path, provider="fake_ss", prov_impl=None):
    (root / ".knowledge" / "state").mkdir(parents=True)
    (root / ".knowledge" / "events").mkdir(parents=True)
    if prov_impl is not None:
        pp = root / "action" / provider
        pp.mkdir(parents=True, exist_ok=True)
        (pp / "design_model.py").write_text(prov_impl, encoding="utf-8")
    mf = root / ".knowledge" / "manifest.yaml"
    mf.write_text(chr(10).join([
        "version: \"1\"",
        "action_types:",
        "  - id: software-system",
        "    creators: [" + provider + "]",
        "    operations: [create, update, execute, validate]",
        "  - id: agentic-software",
        "    creators: [agentic-software]",
        "    operations: [create, update, execute, validate]",
    ]), encoding="utf-8")
    return root

def make_spec(root: Path, name="spec.md", op="create"):
    spec = root / name
    body = [
        "---",
        "spec_id: spec-001",
        "action_type: software-system",
        "operation: " + op,
        "subject: stock-analysis-system",
    ]
    if op != "create":
        body.append("instance_id: act-0001")
    body += ["status: approved", "review_status: approved", "---", "# Spec", "requirements: ..."]
    spec.write_text(chr(10).join(body), encoding="utf-8")
    return spec

PROVIDER_IMPL = chr(10).join([
    "def create_instance(spec, vault=None):",
    '    return {"exit": 0, "instance": {"instance_type": "FakeSoftwareInstance/v1", "subject": spec.get("subject", ""), "state": "created"}}',
    "def execute(instance, spec=None, vault=None):",
    '    return {"exit": 0, "executed": True, "state": "done"}',
    "def validate(instance, spec=None, vault=None):",
    '    return {"exit": 0, "valid": True}',
    "def schema():",
    '    return {"exit": 0, "objects": []}',
])

def run(root: Path, *args):
    env = dict(os.environ); env["KA_VAULT_ROOT"] = str(root)
    return subprocess.run([sys.executable, str(TOOL), *args], env=env, capture_output=True, text=True, timeout=60)

def test_create_operation_creates_instance():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        make_vault(vault, provider="fake_ss", prov_impl=PROVIDER_IMPL)
        spec = make_spec(vault)
        p = run(vault, "create", str(spec))
        assert p.returncode == 0, p.stderr
        data = json.loads((vault / ".knowledge/state/action-instances.json").read_text(encoding="utf-8"))
        inst = data["instances"][0]
        assert inst["action_type"] == "software-system"
        assert inst["state"] == "created"
        assert inst["provider"] == "fake_ss"

def test_update_and_execute_operations_mutate_instance_state():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        make_vault(vault, provider="fake_ss", prov_impl=PROVIDER_IMPL)
        spec = make_spec(vault)
        p0 = run(vault, "create", str(spec))
        assert p0.returncode == 0, p0.stderr
        state = vault / ".knowledge/state/action-instances.json"
        inst_id = json.loads(state.read_text(encoding="utf-8"))["instances"][0]["instance_id"]
        uspec = make_spec(vault, name="update.md", op="update")
        uspec.write_text(uspec.read_text(encoding="utf-8").replace("instance_id: act-0001", "instance_id: " + inst_id, 1), encoding="utf-8")
        p1 = run(vault, "update", str(uspec))
        assert p1.returncode == 0, p1.stderr
        inst = json.loads(state.read_text(encoding="utf-8"))["instances"][0]
        assert inst["state"] == "updated" or inst.get("updated_at")
        espec = make_spec(vault, name="exec.md", op="execute")
        espec.write_text(espec.read_text(encoding="utf-8").replace("instance_id: act-0001", "instance_id: " + inst_id, 1), encoding="utf-8")
        p2 = run(vault, "execute", str(espec))
        assert p2.returncode == 0, p2.stderr
        inst = json.loads(state.read_text(encoding="utf-8"))["instances"][0]
        assert inst["state"] in ("running", "done", "failed")
        assert inst.get("last_run")

def test_validate_operation_checks_instance_and_provider():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        make_vault(vault, provider="fake_ss", prov_impl=PROVIDER_IMPL)
        spec = make_spec(vault)
        p0 = run(vault, "create", str(spec))
        state = vault / ".knowledge/state/action-instances.json"
        inst_id = json.loads(state.read_text(encoding="utf-8"))["instances"][0]["instance_id"]
        vspec = make_spec(vault, name="val.md", op="validate")
        vspec.write_text(vspec.read_text(encoding="utf-8").replace("instance_id: act-0001", "instance_id: " + inst_id, 1), encoding="utf-8")
        p = run(vault, "validate", str(vspec))
        assert p.returncode == 0, p.stderr
        assert "valid" in p.stdout.lower() or "ok" in p.stdout.lower()

def test_operation_rejects_unknown_operation():
    with tempfile.TemporaryDirectory() as td:
        vault = Path(td)
        make_vault(vault, provider="fake_ss", prov_impl=PROVIDER_IMPL)
        spec = make_spec(vault, name="bad.md", op="delete")
        p = run(vault, "delete", str(spec))
        assert p.returncode == 2, p.stdout
