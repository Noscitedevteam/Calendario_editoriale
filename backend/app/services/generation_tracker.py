"""
Tracking stato generazione in memoria condivisa
"""
import logging

logger = logging.getLogger(__name__)

_generation_status = {}

def update_generation_status(project_id: int, current_batch: int, total_batches: int, percent: int):
    """Aggiorna lo stato di generazione per un progetto"""
    _generation_status[project_id] = {
        "current_batch": current_batch,
        "total_batches": total_batches,
        "percent": percent
    }
    logger.info(f"[TRACKER] Project {project_id}: Batch {current_batch}/{total_batches} - {percent}%")

def get_generation_status_cache(project_id: int):
    """Ottieni lo stato corrente di generazione"""
    return _generation_status.get(project_id, None)

def clear_generation_status(project_id: int):
    """Pulisci lo stato al termine della generazione"""
    if project_id in _generation_status:
        del _generation_status[project_id]
        logger.info(f"[TRACKER] Cleared status for project {project_id}")
