"""Script to upload fetch an OS2-formular submission and upload it in pdf format to Sharepoint."""

import json

import urllib.parse

import ast

from datetime import datetime

import requests

import pandas as pd

from sqlalchemy import create_engine


def transform_form_submission(form_serial_number: str, form: dict, mapping: dict) -> dict:
    """
    Transforms a form submission using a mapping of form keys to output labels.
    Supports both flat and nested mappings (e.g., tables of questions).
    """

    transformed = {}
    form_data = form.get("data", {})

    for source_key, target in mapping.items():
        if isinstance(target, dict):
            nested_data = form_data.get(source_key, {})
            for nested_key, output_column in target.items():
                transformed[output_column] = _clean_value(nested_data.get(nested_key))
        else:
            transformed[target] = _clean_value(form_data.get(source_key))

    # Add entity fields
    entity = form.get("entity", {})
    transformed["Serial number"] = form_serial_number
    transformed["Oprettet"] = _parse_datetime(entity, "created")
    transformed["Gennemført"] = _parse_datetime(entity, "completed")

    return transformed


def _clean_value(value):
    """Cleans and flattens lists or JSON-encoded strings."""
    if isinstance(value, list):
        return ", ".join(str(v) for v in value)

    if isinstance(value, str):
        value = value.replace("\r\n", ". ").replace("\n", ". ")

        try:
            parsed = ast.literal_eval(value)

            if isinstance(parsed, list):
                return ", ".join(str(v) for v in parsed)

        except Exception:
            return value.strip("[]").replace("'", "").replace('"', "").strip()

    return value


def _parse_datetime(entity, key):
    try:
        raw = entity[key][0]["value"]

        return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M:%S")

    except Exception:
        return None


def get_workqueue_items(url, token, workqueue_id):
    """
    Retrieve items from the specified workqueue.
    If the queue is empty, return an empty list.
    """

    workqueue_items = set()

    if not url or not token:
        raise EnvironmentError("ATS_URL or ATS_TOKEN is not set in the environment")

    headers = {"Authorization": f"Bearer {token}"}

    full_url = f"{url}/workqueues/{workqueue_id}/items"

    response = requests.get(full_url, headers=headers, timeout=60)

    res_json = response.json().get("items", [])

    for row in res_json:
        ref = row.get("reference")

        workqueue_items.add(ref)

    return workqueue_items


def get_forms_data(conn_string: str, form_type: str) -> list[dict]:
    """
    Retrieve form_data['data'] for all matching submissions for the given form type,
    excluding purged entries.
    """

    query = """
        SELECT
            form_id,
            form_data,
            CAST(form_submitted_date AS datetime) AS form_submitted_date
        FROM
            [RPA].[journalizing].view_Journalizing
        WHERE
            form_type = ?
            AND form_data IS NOT NULL
            AND form_submitted_date IS NOT NULL
        ORDER BY form_submitted_date DESC
    """

    # Create SQLAlchemy engine
    encoded_conn_str = urllib.parse.quote_plus(conn_string)
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={encoded_conn_str}")

    try:
        df = pd.read_sql(sql=query, con=engine, params=(form_type,))

    except Exception as e:
        print("Error during pd.read_sql:", e)

        raise

    if df.empty:
        print("No submissions found for the given form type.")

        return []

    extracted_data = []

    for _, row in df.iterrows():
        try:
            parsed = json.loads(row["form_data"])

            if "purged" not in parsed:  # Skip purged entries
                extracted_data.append(parsed)

        except json.JSONDecodeError:
            print("Invalid JSON in form_data, skipping row.")

    return extracted_data
