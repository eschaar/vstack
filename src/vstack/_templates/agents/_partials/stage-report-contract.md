Use this exact stage report schema at the end of your response. Keep values short and deterministic.

- `status`: `ready` or `blocked`
- `changes_made`: `yes` or `no`
- `updated_items`: list of paths or `none`
- `plan_delta`: short list of plan updates or `none`
- `blockers`: list or `none`
- `token_usage_summary`: `input_tokens`, `output_tokens`, `total_tokens`, and `budget_status` (`within` or `exceeded`)
- `next_handoff_summary`: one short paragraph
- `planner_run_id`: value from `PLANNER_RUN_ID`, the coordinating run id, or `none`
- `model_used`: model identifier or `unknown`
- `subagents_invoked`: list of delegated subagents or `none`
