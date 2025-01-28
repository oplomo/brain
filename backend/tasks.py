from celery import shared_task
from backend.adams_square import Jerusalem
from backend.models import TaskProgress
import time
import logging
from backend.grace_isha import analyze_data

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def fetch_data_for_matches(self, matches):
    """Fetches data for matches, tracks progress, and calculates successful and failed tasks."""
    total_matches = len(matches)
    if total_matches == 0:
        logger.warning("No matches to process.")
        return {"status": "No matches", "result": "No data was processed"}

    logger.info(f"Total matches to process: {total_matches}")

    success_count = 0  # Counter for successful tasks
    failure_count = 0  # Counter for failed tasks

    for idx, match in enumerate(matches):
        logger.info(f"Processing match {idx + 1} of {total_matches}")

        # Fetch data for the match
        jerusalem = Jerusalem()
        every_data = jerusalem.receive_match(match)

        # Analyze the fetched data
        result = analyze_fetched_data(every_data)

        # Update success or failure count based on the result
        if result:
            success_count += 1
        else:
            failure_count += 1

        # Calculate and update progress
        progress = (idx + 1) / total_matches * 100
        TaskProgress.objects.update_or_create(
            task_id=self.request.id,
            defaults={
                "progress": progress,
                "successful": success_count,
                "failed": failure_count,
                "total":total_matches,
                
            },
        )

        # Update task state with progress for frontend tracking
        self.update_state(
            state="PROGRESS",
            meta={
                "current": idx + 1,
                "total": total_matches,
                "progress": progress,
                "successful": success_count,
                "failed": failure_count,
            },
        )

        # Simulate a time-consuming task (example delay)
        time.sleep(6)

    logger.info("Task completed")
    return {
        "status": "Task completed",
        "result": {
            "total_matches": total_matches,
            "successful": success_count,
            "failed": failure_count,
        },
    }


def analyze_fetched_data(every_data):
    """Analyzes a single unit of data and returns True for success, False for failure."""
    try:
        logger.info("Starting analysis for the provided data.")

        # Analyze the data using an external function
        analyzer = analyze_data()
        analyzer.save_every_data(every_data)

        logger.info("Data analysis successful.")
        return True
    except Exception as e:
        logger.error(f"Data analysis failed: {e}")
        return False
