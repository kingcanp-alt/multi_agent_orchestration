import os, csv

_DEFAULT_FIELDS: list[str] = [
    "engine", # "langchain" | "langgraph" | "dspy"
    "input_chars", # input text
    "summary_len", # length of summary
    "meta_len", # meta-summary
    "latency_s", # time in sec
    "reader_s",
    "summarizer_s",
    "critic_s",
    "integrator_s",
]

# Weights & Biases integration optional
_WANDB_ENABLED = os.getenv("WANDB_ENABLED", "").lower() in {"1", "true", "yes", "on"}
_WANDB_PROJECT = os.getenv("WANDB_PROJECT") or "multi_agent_orchestration"
_WANDB_ENTITY = os.getenv("WANDB_ENTITY")
_wandb_run = None

def _get_wandb():
    global _wandb_run
    if not _WANDB_ENABLED:
        return None
    if _wandb_run is not None:
        return _wandb_run
    try:
        import wandb
        _wandb_run = wandb.init(
            project=_WANDB_PROJECT,
            entity=_WANDB_ENTITY,
            reinit=False,
            anonymous="allow",
            settings=wandb.Settings(start_method="thread"),
        )
        return _wandb_run
    except Exception:
        _wandb_run = None
        return None


def _ensure_fields(row: dict) -> list[str]:
    """Add extra keys from row to default columns."""
    fields = list(_DEFAULT_FIELDS)
    for k in row.keys():
        if k not in fields:
            fields.append(k)
    return fields

def log_row(row: dict, path: str = "telemetry.csv"):
    """
    Write telemetry row to CSV.

    """
    row = dict(row or {})
    fields = _ensure_fields(row)

    exists = os.path.exists(path)
    if exists:
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                r = csv.reader(f)
                first = next(r, None)
                if first:
                    old_fields = list(first)
                    for k in fields:
                        if k not in old_fields:
                            old_fields.append(k)
                    fields = old_fields
        except Exception:
            pass

    write_header = not exists
    if exists:
        try:
            with open(path, "r", encoding="utf-8", newline="") as f:
                rd = csv.reader(f)
                first = next(rd, None)
                write_header = (not first) or (first != fields)
        except Exception:
            write_header = True

    if exists and write_header:
        base, ext = os.path.splitext(path)
        rotated = f"{base}.bak"
        try:
            os.replace(path, rotated)
            exists = False
        except Exception:
            pass

    with open(path, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        if not exists:
            w.writeheader()
        w.writerow(row)
    run = _get_wandb()
    if run:
        try:
            run.log(row)
        except Exception:
            pass
