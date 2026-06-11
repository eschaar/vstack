Use this exact stage report schema at the end of your response. Keep values short and deterministic.

- `status`: `ready` or `blocked`
- `changes_made`: `yes` or `no`
- `updated_items`: list of paths or `none`
- `plan_delta`: short list of plan updates or `none`
- `blockers`: list or `none`
- `token_usage_summary`: `input_tokens`, `output_tokens`, `total_tokens`, and `budget_status` (`within` or `exceeded`)
- `next_handoff_summary`: one short paragraph
- `planner_run_id`: value from `PLANNER_RUN_ID` or `none`
- `model_used`: model identifier or `unknown`
- `subagents_invoked`: list of delegated subagents or `none`

Example:

- `status`: `ready`
- `changes_made`: `yes`
- `updated_items`: `docs/architecture/overview.md`
- `plan_delta`: `none`
- `blockers`: `none`
- `token_usage_summary`: `input_tokens=1200, output_tokens=420, total_tokens=1620, budget_status=within`
- `next_handoff_summary`: `Architecture baseline updated and aligned with current requirements. Ready for designer handoff.`
- `planner_run_id`: `20260611T101500Z-a1b2`
- `model_used`: `GPT-5.3-Codex (copilot)`
- `subagents_invoked`: `none`
