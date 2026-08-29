#!/usr/bin/env python3
"""K-Action_creator Runtime API: create Action Instance from an approved ActionSpecification v1.

Flow: ActionSpecification -> resolve action_type via manifest Action Type Catalog + creators ->
call provider capability create_instance(spec) -> record in .knowledge/state/action-instances.json
+ action.instance.created event.
Stdlib only. Runtime path (not capability-dev scaffolding).
"""
import argparse, importlib.util, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.environ.get("KA_VAULT_ROOT", ".")).resolve()
STATE = VAULT / ".knowledge/state"
INSTANCES = STATE / "action-instances.json"
EVENTS = VAULT / ".knowledge/events"
N = chr(10)

def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def parse_fm(text):
    fm = {}
    if text.startswith("---" + N):
        end = text.find(N + "---", 4)
        if end != -1:
            for line in text[4:end].splitlines():
                s = line.strip()
                if not s or s.startswith("#") or s.startswith("- "):
                    continue
                if ":" in s:
                    k, v = s.split(":", 1)
                    fm[k.strip()] = v.strip().strip(chr(34))
    return fm

def load_action_types():
    mf = VAULT / ".knowledge/manifest.yaml"
    types = {}
    if not mf.exists():
        return types
    text = mf.read_text(encoding="utf-8", errors="ignore")
    in_types = False
    cur = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("action_types:"):
            in_types = True
            continue
        if not in_types or not s or s.startswith("#"):
            continue
        if s.startswith("- id:"):
            if cur:
                types[cur["id"]] = cur["creators"]
            cur = {"id": s.split(":", 1)[1].strip(), "creators": []}
        elif s.startswith("creators:") and cur is not None:
            raw = s.split(":", 1)[1].strip()
            cur["creators"] = [c.strip().strip(chr(91)) for c in raw.strip(chr(93)).split(",") if c.strip().strip(chr(91))]
        elif s.startswith("-") and cur is not None and s[1:].strip():
            cur["creators"].append(s[1:].strip())
    if cur:
        types[cur["id"]] = cur["creators"]
    return types

def call_provider_create(provider, spec):
    """Load provider component create_instance(spec) entry (design_model*.py)."""
    for mod in ("design_model.py", "design_model_provider.py"):
        path = VAULT / "action" / provider / mod
        if not path.exists():
            continue
        try:
            spec_l = importlib.util.spec_from_file_location("p_" + provider + "_" + mod.split(".")[0], path)
            m = importlib.util.module_from_spec(spec_l)
            spec_l.loader.exec_module(m)
            fn = getattr(m, "create_instance", None)
            if fn:
                return fn(spec, vault=VAULT), None
        except Exception as e:
            return None, "provider load failed: " + str(e)[:200]
    return None, "provider create_instance not found"

def event(payload):
    EVENTS.mkdir(parents=True, exist_ok=True)
    f = EVENTS / ("events-" + datetime.now(timezone.utc).strftime("%Y%m%d") + ".jsonl")
    rec = {"event": "action.instance.created", "ts": now_iso()}
    rec.update(payload)
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + N)

def load_instances():
    if INSTANCES.exists():
        try:
            return json.loads(INSTANCES.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["create"])
    ap.add_argument("spec", nargs="?", default="-")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    text = sys.stdin.read() if args.spec == "-" else Path(args.spec).read_text(encoding="utf-8", errors="ignore")
    fm = parse_fm(text)
    atype = str(fm.get("action_type", "")).strip()
    review = str(fm.get("review_status", "")).strip()
    status = str(fm.get("status", "")).strip()
    if review != "approved" and status != "approved":
        print("gate: spec must be approved (review_status or status = approved)", file=sys.stderr)
        return 2
    types = load_action_types()
    if atype not in types:
        print("unknown action_type: " + atype + " (known: " + ",".join(sorted(types)) + ")", file=sys.stderr)
        return 2
    creators = types[atype]
    if not creators:
        print("no creator capability registered for action_type: " + atype, file=sys.stderr)
        return 2
    provider = creators[0]
    spec_id = fm.get("spec_id") or ("spec-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"))
    cap_instance, cap_err = call_provider_create(provider, fm)
    cap_out = cap_instance.get("instance") if cap_instance and cap_instance.get("exit") == 0 else None
    cap_err = cap_err or (cap_instance.get("error") if cap_instance and cap_instance.get("exit") != 0 else None)
    instance = {
        "instance_id": "act-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "spec_id": spec_id,
        "action_type": atype,
        "intent": fm.get("intent", ""),
        "subject": fm.get("subject", ""),
        "provider": provider,
        "state": "created",
        "input": {k: fm[k] for k in ("requirements", "input") if fm.get(k)},
        "capability_instance": cap_out,
        "capability_error": cap_err,
        "created_at": now_iso(),
        "last_run": "",
        "health": "ok",
    }
    if args.dry_run:
        print(json.dumps({"dry_run": True, "instance": instance}, ensure_ascii=False, indent=1))
        return 0
    data = load_instances()
    data.setdefault("version", 1)
    data.setdefault("instances", []).append(instance)
    data["updated"] = now_iso()
    STATE.mkdir(parents=True, exist_ok=True)
    INSTANCES.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    event({"instance_id": instance["instance_id"], "spec_id": spec_id, "action_type": atype, "provider": provider, "state": "created"})
    print(json.dumps({"status": "created", "instance": instance}, ensure_ascii=False, indent=1))
    return 0

if __name__ == "__main__":
    sys.exit(main())