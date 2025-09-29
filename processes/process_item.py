"""Module to handle item processing"""

import os
import logging

from io import BytesIO

import pandas as pd

from dotenv import load_dotenv

from mbu_msoffice_integration.sharepoint_class import Sharepoint

from helpers import config

load_dotenv()  # Loads variables from .env

SHAREPOINT_SITE_URL = "https://aarhuskommune.sharepoint.com"
SHAREPOINT_DOCUMENT_LIBRARY = "Delte dokumenter"

SHEET_NAME = "Besvarelser"

SHAREPOINT_KWARGS = {
    "tenant": os.getenv("TENANT"),
    "client_id": os.getenv("CLIENT_ID"),
    "thumbprint": os.getenv("APPREG_THUMBPRINT"),
    "cert_path": os.getenv("GRAPH_CERT_PEM"),
}

logger = logging.getLogger(__name__)


def process_item(item_data: dict):
    """Function to handle item processing"""

    forn_config = item_data.get("config", {})

    site_name = forn_config["site_name"]
    folder_name = forn_config["folder_name"]
    excel_file_name = forn_config["excel_file_name"]

    formular_mapping = config.MODERSMAAL_CONFIG["formular_mapping"]

    new_submissions = item_data.get("submissions", [])
    if len(new_submissions) == 0:
        logger.info("No new submissions for the given week, process completed")

        return "No new submissions for the given week"

    try:
        sharepoint_api = Sharepoint(
            tenant=SHAREPOINT_KWARGS["tenant"],
            client_id=SHAREPOINT_KWARGS["client_id"],
            thumbprint=SHAREPOINT_KWARGS["thumbprint"],
            cert_path=SHAREPOINT_KWARGS["cert_path"],
            site_url=SHAREPOINT_SITE_URL,
            site_name=site_name,
            document_library=SHAREPOINT_DOCUMENT_LIBRARY,
        )

    except Exception as e:
        logger.info(f"Error when trying to authenticate: {e}")

    try:
        files_in_sharepoint = sharepoint_api.fetch_files_list(folder_name=folder_name)
        file_names = [f["Name"] for f in files_in_sharepoint]

    except Exception as e:
        logger.info(f"Error when trying to fetch existing files in SharePoint: {e}")

    if excel_file_name in file_names:
        logger.info("Excel file already exists, process completed")

        return "Excel file already exists"

    # Force column order according to formular_mapping
    column_order = list(formular_mapping.values())

    normalized_submissions = [
        {col: row.get(col, None) for col in column_order}
        for row in new_submissions
    ]

    all_submissions_df = pd.DataFrame(normalized_submissions, columns=column_order)

    # Ensure no extra columns slipped in
    all_submissions_df = all_submissions_df[column_order]

    excel_stream = BytesIO()
    all_submissions_df.to_excel(
        excel_stream,
        index=False,
        engine="openpyxl",
        sheet_name=SHEET_NAME
    )
    excel_stream.seek(0)

    try:
        sharepoint_api.upload_file_from_bytes(
            binary_content=excel_stream.getvalue(),
            file_name=excel_file_name,
            folder_name=folder_name,
        )

    except Exception as e:
        logger.info(f"Error when trying to upload excel file to SharePoint: {e}")

    logger.info("Formatting and sorting excel file")
    try:
        sharepoint_api.format_and_sort_excel_file(
            folder_name=folder_name,
            excel_file_name=excel_file_name,
            sheet_name=SHEET_NAME,
            sorting_keys=[
                {"key": "Ønsket sprog", "ascending": True, "type": "str"},
                {"key": "A", "ascending": False, "type": "int"}
            ],
            bold_rows=[1],
            align_horizontal="left",
            align_vertical="top",
            italic_rows=None,
            font_config=None,
            column_widths=100,
            freeze_panes="A2",
        )

    except Exception as e:
        logger.info(f"Error when trying format and sort excel file: {e}")

    return "Process completed without exceptions"
