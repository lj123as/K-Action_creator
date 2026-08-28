# K-Action Creator Public Interfaces

> Public interface summary for `action/K-Action_creator`. Cognition capabilities owner: `cognition/K-Action_creator/capabilities.md`.

## `action-candidate-intake`

- Owner: K-Action_creator.
- Producer: knowledge-network candidate-generation, KA-system dispatch, or human operator.
- Consumer: K-Action_creator generation workflow.
- Input: reviewed `ActionCandidate v1`, target cognition SSOT, capability summary, expected safe write paths, and constraints.
- Output: generation request.
- Review behavior: unreviewed candidates remain pending.

## `subsystem-skeleton-generation`

- Owner: K-Action_creator.
- Producer: reviewed generation request.
- Consumer: generation tool or skill.
- Output: initial action subsystem skeleton, README draft, registry draft, and handoff note.
- Allowed side effects: create new action subsystem skeleton only within the requested target path.
- Forbidden coupling: do not own generated subsystem lifecycle or business semantics after handoff.

## `generation-handoff`

- Owner: K-Action_creator.
- Producer: generation workflow.
- Consumer: action-system lifecycle and KA-system registry.
- Output: handoff record describing generated files, initial status, owner cognition, and follow-up checks.
- Compatibility: action-system owns lifecycle after the generated subsystem is accepted.
## `ActionCandidate v1`

Input from knowledge-network after review:

```yaml
version: 1
candidate_type: action
candidate_id: string
source_draft_id: string
intent: string
requested_capability: string
target_subsystem_hint: string
inputs:
  cognition_links: []
  state_links: []
  object_links: []
review_status: accepted
```

## `GenerationRequest v1`

```yaml
version: 1
request_id: string
request_type: action_subsystem_generation
action_candidate: ActionCandidate v1
requested_by: KA-system|human
requested_at: ISO-8601
constraints:
  target_path: string
  allow_code_generation: boolean
  require_review_before_activation: true
```

## `GenerationHandoff v1`

```yaml
version: 1
handoff_id: string
status: proposed|generated|needs_review|rejected
generated_paths: []
registry_hint:
  subsystem_name: string
  target_path: string
  lifecycle_status: proposed
notes: string
```

Generated output remains proposed until action-system lifecycle review and KA-system orchestration accept it.

## Implementation（2026-08-24）

- `tools/capability_dev.py`：GenerationRequest v1 -> 本地骨架（init_system.py --no-github）-> component.yaml -> action-registry proposed -> handoff 报告与 `action.generation.handoff` 事件。
- 通道：请求盒 `type: create-action`（由 knowledge-network poller 路由到本工具）；门控 `review_status: approved`；`--dry-run` 预演；人工显式授权用 `--allow-unreviewed`。
- GenerationRequest v1 frontmatter 示例：id / candidate_id / subsystem / description / review_status: approved。
