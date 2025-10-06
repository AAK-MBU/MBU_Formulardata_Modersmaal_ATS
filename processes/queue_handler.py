"""Module to hande queue population"""

import os
import asyncio
import logging
import json
import copy

from automation_server_client import Workqueue

import datetime

from helpers import config

from helpers import helper_functions

logger = logging.getLogger(__name__)


def retrieve_items_for_queue() -> list[dict]:
    """
    Function to populate the workqueue with items.
    """

    db_conn_string = os.getenv("DBCONNECTIONSTRINGPROD")

    form_config = copy.deepcopy(config.MODERSMAAL_CONFIG)

    ### FOR DEV TESTING ONLY - OVERRIDE SITE AND FOLDER NAME TO AVOID POLLUTING ACTUAL FOLDERS ###
    # testing = True
    # if testing:
    #     form_config["site_name"] = "MBURPA"
    #     form_config["folder_name"] = "Automation_Server"
    ### FOR DEV TESTING ONLY - OVERRIDE SITE AND FOLDER NAME TO AVOID POLLUTING ACTUAL FOLDERS ###

    submissions = []

    # today = datetime.date(2025, 9, 22)
    today = datetime.date.today()
    monday_last_week = today - datetime.timedelta(days=today.weekday() + 7)
    sunday_last_week = today - datetime.timedelta(days=today.weekday() + 1)

    os2_webform_id = form_config["os2_webform_id"]

    form_config["excel_file_name"] = str(form_config["excel_file_name"]).replace("monday_last_week", monday_last_week.strftime("%Y-%m-%d")).replace("sunday_last_week", sunday_last_week.strftime("%Y-%m-%d"))

    formular_mapping = form_config["formular_mapping"]
    del form_config["formular_mapping"]

    logger.info("STEP 1 - Fetching all active submissions.")
    all_submissions = helper_functions.get_forms_data(
        conn_string=db_conn_string,
        form_type=os2_webform_id,
    )

    logger.info(f"OS2 submissions retrieved. {len(all_submissions)} total submissions found.")

    logger.info("STEP 2 - Looping fetched submissions, looking for last weeks' submissions.")
    for form in all_submissions:
        form_serial_number = form["entity"]["serial"][0]["value"]

        completed_str = form["entity"]["completed"][0]["value"]

        if completed_str:
            completed_time = datetime.datetime.fromisoformat(completed_str).date()

            if monday_last_week <= completed_time <= sunday_last_week:
                transformed_row = helper_functions.transform_form_submission(form_serial_number, form, formular_mapping)

                submissions.append(transformed_row)

    logger.info(f"OS2 submissions looped. {len(submissions)} in the previous week.")

    work_item_data = {
        "reference": f"{os2_webform_id}_{today}",
        "data": {"config": form_config, "submissions": submissions},
    }

    if "formular_mapping" in form_config:
        del form_config["formular_mapping"]

    queue_items = [work_item_data]

    print()
    print()

    return queue_items


def create_sort_key(item: dict) -> str:
    """
    Create a sort key based on the entire JSON structure.
    Converts the item to a sorted JSON string for consistent ordering.
    """
    return json.dumps(item, sort_keys=True, ensure_ascii=False)


async def concurrent_add(workqueue: Workqueue, items: list[dict]) -> None:
    """
    Populate the workqueue with items to be processed.
    Uses concurrency and retries with exponential backoff.

    Args:
        workqueue (Workqueue): The workqueue to populate.
        items (list[dict]): List of items to add to the queue.
        logger (logging.Logger): Logger for logging messages.

    Returns:
        None

    Raises:
        Exception: If adding an item fails after all retries.
    """
    sem = asyncio.Semaphore(config.MAX_CONCURRENCY)

    async def add_one(it: dict):
        reference = str(it.get("reference") or "")
        data = {"item": it}

        async with sem:
            for attempt in range(1, config.MAX_RETRIES + 1):
                try:
                    await asyncio.to_thread(workqueue.add_item, data, reference)
                    logger.info(f"Added item to queue with reference: {reference}")
                    return True

                except Exception as e:
                    if attempt >= config.MAX_RETRIES:
                        logger.error(
                            f"Failed to add item {reference} after {attempt} attempts: {e}"
                        )
                        return False

                    backoff = config.RETRY_BASE_DELAY * (2 ** (attempt - 1))

                    logger.warning(
                        f"Error adding {reference} (attempt {attempt}/{config.MAX_RETRIES}). "
                        f"Retrying in {backoff:.2f}s... {e}"
                    )
                    await asyncio.sleep(backoff)

    if not items:
        logger.info("No new items to add.")
        return

    sorted_items = sorted(items, key=create_sort_key)
    logger.info(
        f"Processing {len(sorted_items)} items sorted by complete JSON structure"
    )

    results = await asyncio.gather(*(add_one(i) for i in sorted_items))
    successes = sum(1 for r in results if r)
    failures = len(results) - successes

    logger.info(
        f"Summary: {successes} succeeded, {failures} failed out of {len(results)}"
    )
