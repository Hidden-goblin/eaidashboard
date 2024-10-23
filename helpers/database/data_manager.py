from json import load
from logging import getLogger
from pathlib import Path

from dpath import merge

log = getLogger(__name__)


# Update the default value in order to match your needs
def build_dataset(base_path: str = "resources/pages") -> dict:
    """Build a single dictionary from a collection of json files"""
    try:
        path = Path(base_path)
        merged_json = {}
        for filepath in path.glob("**/*.json"):
            log.debug(f"Processing {filepath}")
            with open(filepath, "r") as file:
                merge(merged_json, load(file))
        return merged_json
    except Exception as exception:
        log.error(exception)
        raise
