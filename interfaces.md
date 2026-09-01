# K-Action Orchestrator Public Interfaces

> Public interface summary for `action/K-Action_orchestrator` (component id: action-orchestrator). Cognition capabilities owner: `cognition/K-Action_orchestrator/capabilities.md`.

## Action Request → Action Operation（运行时统一入口）

Action Request 统一模型：AI Client / KA-System 提交 Action Request（action_type + operation），经 `tools/action_ops.py` 执行：

```text
Action Request（action_type + operation）
  → manifest action_types.operations 白名单校验
  → Type Capability resolve（manifest creators ↔ component.yaml 双向声明）
  → provider 调用（action/<type_provider> 组件）
  → Action Instance（.knowledge/state/action-instances.json）+ events
```

- 门控：create 需 `review_status: approved`（ActionSpecification v1）。
- 请求盒通道：knowledge-network poller 的 `create-action` 请求路由到本入口（operation 默认 create，可用 frontmatter `operation` 覆盖）。
- 运行时信封（dispatch / schedule / health / retry / audit）由 KA-System 提供；操作执行统一走本入口，不绕过。


## `action-candidate-intake`

- Owner: K-Action_orchestrator.
- Producer: knowledge-network candidate-generation, KA-system dispatch, or human operator.
- Consumer: K-Action_orchestrator generation workflow.
- Input: reviewed `ActionCandidate v1`, target cognition SSOT, capability summary, expected safe write paths, and constraints.
- Output: generation request.
- Review behavior: unreviewed candidates remain pending.

## `subsystem-skeleton-generation`

- Owner: K-Action_orchestrator.
- Producer: reviewed generation request.
- Consumer: generation tool or skill.
- Output: initial action subsystem skeleton, README draft, registry draft, and handoff note.
- Allowed side effects: create new action subsystem skeleton only within the requested target path.
- Forbidden coupling: do not own generated subsystem lifecycle or business semantics after handoff.

## `generation-handoff`

- Owner: K-Action_orchestrator.
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
action_type: string          # canonical Action Type (from Action Type Catalog; Cognition semantic result)
requested_capability: string # resolve result = manifest creators[action_type]
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
- 通道：开发环境直接调用（CLI / SKILL）；生产请求盒 `type: create-action` 已收敛到 `tools/action_ops.py` 统一入口，不再路由到本工具。门控 `review_status: approved`；`--dry-run` 预演；人工显式授权用 `--allow-unreviewed`。
- GenerationRequest v1 frontmatter 示例：id / candidate_id / subsystem / description / review_status: approved。

- `tools/action_ops.py`（统一 Action Operation 编排：create / update / execute / validate / register；按 action_type + operation 解析 Type Capability（manifest operations 白名单）并调用 provider；实例状态落 `.knowledge/state/action-instances.json`；`register` 对账 Type Contract → manifest（默认 dry-run，`--apply` 落盘）；`--dry-run` 预演）。
