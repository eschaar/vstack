Use this exact stage report schema at the end of your response:

- `status`: `ready` or `blocked`
- `changes_made`: `yes` or `no`
- `updated_items`: list of paths (or `none`)
- `blockers`: list (or `none`)
- `next_handoff_summary`: one short paragraph
- `planner_run_id`: value received in `PLANNER_RUN_ID` (or `none` when not provided)
- `model_used`: model identifier used for this stage (or `unknown`)
- `subagents_invoked`: list of delegated subagents called during this stage (or `none`)
