#!/usr/bin/env python3
"""K-Action Orchestrator Runtime API: unified Action Operation entry.

Action Request (target + action_type + operation) -> resolve Type Capability
via manifest Action Type Catalog -> call provider capability ->
record/update .knowledge/state/action-instances.json + events.

Operations: create (new instance), update (existing instance fields/state),
execute (state machine running/done), validate (instance + provider check).
create is just one operation; maintenance is NOT a separate architecture.
Stdlib only.
"""
import argparse, importlib.util, json, os, sys
from datetime import datetime, timezone
from pathlib import Path

VAULT = Path(os.environ.get("KA_VAULT_ROOT", ".")).resolve()
STATE = VAULT / ".knowledge/state"
INSTANCES = STATE / "action-instances.json"
EVENTS = VAULT / ".knowledge/events"
N = chr(10)
OPS = ("create", "update", "execute", "validate")

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
                types[cur["id"]] = cur
            cur = {"id": s.split(":", 1)[1].strip(), "creators": [], "operations": []}
        elif s.startswith("creators:") and cur is not None:
            raw = s.split(":", 1)[1].strip()
            cur["creators"] = [c.strip().strip(chr(91)) for c in raw.strip(chr(93)).split(",") if c.strip().strip(chr(91))]
        elif s.startswith("operations:") and cur is not None:
            raw = s.split(":", 1)[1].strip()
            cur["operations"] = [c.strip() for c in raw.strip(chr(91)).strip(chr(93)).split(",") if c.strip()]
        elif s.startswith("-") and cur is not None and s[1:].strip():
            cur["creators"].append(s[1:].strip())
    if cur:
        types[cur["id"]] = cur
    return types

def load_provider(provider, mod, fn_name):
    path = VAULT / "action" / provider / mod
    if not path.exists():
        return None, None
    try:
        spec_l = importlib.util.spec_from_file_location("p_" + provider + "_" + mod.split(".")[0], path)
        m = importlib.util.module_from_spec(spec_l)
        spec_l.loader.exec_module(m)
        return m, getattr(m, fn_name, None)
    except Exception as e:
        return None, "provider load failed: " + str(e)[:200]

def call_provider(provider, fn_name, *args):
    for mod in ("action_provider.py", "design_model.py", "design_model_provider.py"):
        m, fn = load_provider(provider, mod, fn_name)
        if isinstance(fn, str):
            return None, fn
        if fn:
            try:
                return fn(*args), None
            except Exception as e:
                return None, fn_name + " failed: " + str(e)[:200]
    return None, fn_name + " not found in provider " + provider

def event(name, payload):
    EVENTS.mkdir(parents=True, exist_ok=True)
    f = EVENTS / ("events-" + datetime.now(timezone.utc).strftime("%Y%m%d") + ".jsonl")
    rec = {"event": name, "ts": now_iso()}
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

def save_instances(data):
    STATE.mkdir(parents=True, exist_ok=True)
    data.setdefault("version", 1)
    data["updated"] = now_iso()
    INSTANCES.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")

def find_instance(data, fm):
    iid = str(fm.get("instance_id", "")).strip()
    subj = str(fm.get("subject", "")).strip()
    for inst in data.get("instances", []):
        if iid and inst.get("instance_id") == iid:
            return inst
        if subj and inst.get("subject") == subj and str(inst.get("action_type")) == str(fm.get("action_type", "")).strip():
            return inst
    return None

def op_create(fm, types):
    atype = str(fm.get("action_type", "")).strip()
    provider = (types[atype]["creators"] or [""])[0]
    cap_instance, cap_err = call_provider(provider, "create_instance", fm, VAULT)
    cap_out = cap_instance.get("instance") if cap_instance and cap_instance.get("exit") == 0 else None
    cap_err = cap_err or (cap_instance.get("error") if cap_instance and cap_instance.get("exit") != 0 else None)
    instance = {
        "instance_id": "act-" + datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
        "spec_id": fm.get("spec_id", ""),
        "action_type": atype,
        "intent": fm.get("intent", ""),
        "subject": fm.get("subject", ""),
        "provider": provider,
        "state": "created",
        "input": {k: fm[k] for k in ("requirements", "input") if fm.get(k)},
        "capability_instance": cap_out,
        "capability_error": cap_err,
        "created_at": now_iso(),
        "updated_at": "",
        "last_run": "",
        "health": "ok",
    }
    data = load_instances()
    data.setdefault("instances", []).append(instance)
    save_instances(data)
    event("action.instance.created", {"instance_id": instance["instance_id"], "spec_id": instance["spec_id"], "action_type": atype, "provider": provider})
    return {"status": "created", "instance": instance}

def op_update(fm, types):
    data = load_instances()
    inst = find_instance(data, fm)
    if not inst:
        return {"exit": 2, "error": "instance not found (need instance_id or subject+action_type)"}
    cap_out, cap_err = call_provider(inst["provider"], "update_instance", inst, fm, VAULT)
    if cap_out and cap_out.get("exit") == 0:
        inst.update(cap_out.get("instance") or {})
    inst["state"] = "updated"
    inst["updated_at"] = now_iso()
    if cap_err:
        inst["capability_error"] = cap_err
    save_instances(data)
    event("action.instance.updated", {"instance_id": inst["instance_id"], "action_type": inst["action_type"]})
    return {"status": "updated", "instance": inst}

def op_execute(fm, types):
    data = load_instances()
    inst = find_instance(data, fm)
    if not inst:
        return {"exit": 2, "error": "instance not found (need instance_id or subject+action_type)"}
    inst["state"] = "running"
    inst["last_run"] = now_iso()
    save_instances(data)
    cap_out, cap_err = call_provider(inst["provider"], "execute", inst, fm, VAULT)
    final = "done"
    if cap_out and cap_out.get("exit") == 0:
        final = cap_out.get("state", "done")
        if cap_out.get("executed") is False:
            final = "failed"
    elif cap_out and cap_out.get("exit") != 0:
        final = "failed"
    elif cap_err:
        final = "failed"
    inst["state"] = final
    inst["last_end"] = now_iso() if final in ("done", "failed") else ""
    if isinstance(cap_out, dict):
        for k in ("maintenance", "note"):
            if cap_out.get(k) is not None:
                inst[k] = cap_out[k]
        if cap_out.get("error"):
            inst["capability_error"] = cap_out["error"]
    if cap_err:
        inst["capability_error"] = cap_err
    save_instances(data)
    event("action.instance.executed", {"instance_id": inst["instance_id"], "state": final})
    return {"status": final, "instance": inst}

def op_validate(fm, types):
    data = load_instances()
    inst = find_instance(data, fm)
    issues = []
    if not inst:
        issues.append("instance not found")
    else:
        if not inst.get("provider"):
            issues.append("missing provider")
        cap_out, cap_err = call_provider(inst["provider"], "validate", inst, fm, VAULT) if inst else (None, None)
        if cap_out and cap_out.get("exit") == 0:
            pass
        else:
            issues.append(cap_err or "provider validate failed")
    if issues:
        return {"exit": 2, "valid": False, "issues": issues}
    return {"exit": 0, "valid": True, "instance": inst}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=list(OPS))
    ap.add_argument("request", nargs="?", default="-")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    text = sys.stdin.read() if args.request == "-" else Path(args.request).read_text(encoding="utf-8", errors="ignore")
    fm = parse_fm(text)
    op = args.command
    atype = str(fm.get("action_type", "")).strip()
    review = str(fm.get("review_status", "")).strip()
    status = str(fm.get("status", "")).strip()
    types = load_action_types()
    if atype not in types:
        print("unknown action_type: " + atype + " (known: " + ",".join(sorted(types)) + ")", file=sys.stderr)
        return 2
    allowed = types[atype].get("operations") or []
    if op not in allowed:
        print("operation " + op + " not allowed for action_type " + atype + " (allowed: " + ",".join(allowed) + ")", file=sys.stderr)
        return 2
    if op == "create":
        if review != "approved" and status != "approved":
            print("gate: create spec must be approved", file=sys.stderr)
            return 2
        result = op_create(fm, types)
    elif op == "update":
        result = op_update(fm, types)
    elif op == "execute":
        result = op_execute(fm, types)
    else:
        result = op_validate(fm, types)
    if result.get("exit") == 2:
        print(result.get("error", "failed"), file=sys.stderr)
        return 2
    if args.dry_run:
        result = dict(result, dry_run=True)
    print(json.dumps(result, ensure_ascii=False, indent=1))
    return 0

if __name__ == "__main__":
    sys.exit(main())
