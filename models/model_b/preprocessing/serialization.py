def serialize_state(state: dict) -> str:
    def fmt_field(val):
        if val is None or val == "NOT_AVAILABLE":
            return "NOT_AVAILABLE"
        if isinstance(val, list):
            if len(val) == 0:
                return "NONE"
            return ", ".join(str(x) for x in val)
        return str(val)

    return (
        f"APPLICATIONS: {fmt_field(state.get('applications'))} | "
        f"FILES: {fmt_field(state.get('files'))} | "
        f"BROWSER TABS: {fmt_field(state.get('browser_tabs'))} | "
        f"PROCESSES: {fmt_field(state.get('processes'))} | "
        f"COMPLETED SUBTASKS: {fmt_field(state.get('completed_subtasks'))}"
    )
