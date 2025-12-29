# Stato generazione in memoria (per progetto)
generation_status = {}

def set_status(project_id: int, current_batch: int, total_batches: int, status: str = "generating"):
    generation_status[project_id] = {
        "current_batch": current_batch,
        "total_batches": total_batches,
        "status": status,  # "generating", "completed", "error"
        "percent": int((current_batch / total_batches) * 100) if total_batches > 0 else 0
    }

def get_status(project_id: int):
    return generation_status.get(project_id, {"status": "idle", "percent": 0})

def clear_status(project_id: int):
    if project_id in generation_status:
        del generation_status[project_id]
