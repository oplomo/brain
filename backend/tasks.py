from celery import shared_task
from backend.adams_square import Jerusalem
from backend.models import TaskProgress
import time
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def fetch_data_for_matches(self, matches):
    """Fetches data for matches and updates progress."""
    total_matches = len(matches)
    if total_matches == 0:
        logger.warning("No matches to process.")
        return {"status": "No matches", "result": "No data was processed"}

    logger.info(f"Total matches to process: {total_matches}")
    
    for idx, match in enumerate(matches):
        logger.info(f"Processing match {idx + 1} of {total_matches}")
        
        # Simulate processing
        jerusalem = Jerusalem()
        jerusalem.receive_match(match)

        # Simulate a time-consuming task (example delay)
        time.sleep(60)  # Use smaller sleep time for testing; adjust as needed

        # Calculate and update progress
        progress = (idx + 1) / total_matches * 100
        TaskProgress.objects.update_or_create(
            task_id=self.request.id,
            defaults={"progress": progress},
        )

        # Update task state with progress for frontend tracking
        self.update_state(
            state="PROGRESS",
            meta={"current": idx + 1, "total": total_matches, "progress": progress},
        )

    logger.info("Task completed")
    return {"status": "Task completed", "result": f"Fetched data for {total_matches} matches"}

from celery import shared_task
from backend.grace_isha import analyze_data


@shared_task
def analyze_fetched_data(data):
    analyze_data(data)  # Assuming analyze_data is the analysis function



# celery -A brain purge    ||this is for removing wor from ceery qeue
# redis-cli flushall   || for cearing tas saved in database
# celery -A brain worker --loglevel=info --pool=solo   || for starting ceery