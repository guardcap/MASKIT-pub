# scripts/schema_utils.py
import os
import json
from jsonschema import Draft202012Validator, RefResolver
from typing import Any

def load_schema(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_schema(instance: Any, schema: dict) -> None:
    """
    Raise jsonschema.ValidationError if invalid.
    """
    schema_dir = os.path.join(os.path.dirname(__file__), "../schemas")
    schema_dir = os.path.abspath(schema_dir)

    # common.json 경로
    common_path = os.path.join(schema_dir, "common.json")
    with open(common_path, "r", encoding="utf-8") as f:
        common_schema = json.load(f)

    # store에 직접 등록
    store = {
        f"file://{schema_dir}/common.json": common_schema
    }

    resolver = RefResolver(base_uri=f"file://{schema_dir}/", referrer=schema, store=store)

    Draft202012Validator(schema, resolver=resolver).validate(instance)
