import logging
import os
import re
import sys
from logging import getLogger
from pathlib import Path
from shutil import copytree, rmtree

import dotenv
from behave.model import Feature, Scenario, Step
from behave.runner import Context
from eaiBat import folder_file_name_cleaning

from helpers.conversion_utils import status_to_string, string_to_bool
from helpers.database import data_holder
from helpers.database.data_holder import retrieve_data
from helpers.database.data_manager import build_dataset
from helpers.models.dashboard import Dashboard

log = getLogger("environment")


def set_logger(log_name: str, is_debug: bool = False) -> None:
    """Set the logger with a debug mode"""
    # Keeping the last execution log
    if os.path.exists(f"{log_name}_log.log"):
        if os.path.exists(f"{log_name}_log_back.log"):
            os.remove(f"{log_name}_log_back.log")
        os.rename(f"{log_name}_log.log", f"{log_name}_log_back.log")
    logging.basicConfig(level=logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s -- %(filename)s.%(funcName)s-- %(levelname)s -- %(message)s")
    handler = logging.FileHandler(f"{log_name}_log.log", mode="w", encoding="utf-8")
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.DEBUG)

    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    logger.addHandler(stream_handler)

    # Some packages are only in warning level
    logging.getLogger("behave").setLevel(level=logging.WARNING)
    logging.getLogger("xmlschema").setLevel(level=logging.WARNING)
    logging.getLogger("jsonschema").setLevel(level=logging.WARNING)
    logging.getLogger("dpath").setLevel(level=logging.WARNING)
    logging.getLogger("parse").setLevel(level=logging.WARNING)
    logging.getLogger("resquests").setLevel(level=logging.WARNING)
    logging.getLogger("urllib3").setLevel(level=logging.WARNING)
    logging.getLogger("selenium").setLevel(level=logging.WARNING)
    logging.getLogger("polling2").setLevel(level=logging.WARNING)
    logging.getLogger("PIL").setLevel(level=logging.WARNING)
    # Automation packages depend on the required level
    if is_debug:
        logging.getLogger("eaiBat").setLevel(logging.DEBUG)
        logging.getLogger("eaiautomatontools").setLevel(logging.DEBUG)
        logging.getLogger("helpers").setLevel(logging.DEBUG)
        logging.getLogger("builtins").setLevel(logging.DEBUG)
    else:
        logging.getLogger("eaiBat").setLevel(logging.WARNING)
        logging.getLogger("eaiautomatontools").setLevel(logging.WARNING)
        logging.getLogger("helpers").setLevel(logging.WARNING)
        logging.getLogger("builtins").setLevel(logging.WARNING)


def make_evidence_rotation(max_keep: int) -> None:
    """
    Delete the oldest and make the rotation
    :param max_keep: the max number of evidence to keep i.e. 0 is no conservation , 1 is keep one
    :return:
    """
    try:

        def increase_number(folder: str) -> str:
            folder_name, number = re.search("([a-zA-Z]*)([0-9]*)", folder).groups()
            return f"{folder_name}{int(number) + 1}"

        if max_keep != 0:
            folders = [
                f
                for f in os.listdir(".")
                if os.path.isdir(os.path.join(".", f))
                and re.match(r"^evidence[0-9]+$", f)
                and int(re.search("evidence([0-9]+)", f).groups()[0]) <= max_keep
            ]
            folders.reverse()
            # last = max([int(item.replace("evidence", "")) for item in folders if folders])
            process = [(folder, increase_number(folder)) for folder in folders if folder != f"evidence{max_keep}"]

            for evidence in process:
                rmtree(evidence[1], ignore_errors=True)
                copytree(evidence[0], evidence[1])
            rmtree("evidence1", ignore_errors=True)
            if os.path.exists("evidence") and os.path.isdir("evidence"):
                log.debug("evidence folder exists")
                copytree("evidence", "evidence1")
                rmtree("evidence")
            elif os.path.exists("evidence") and not os.path.isdir("evidence"):
                log.debug("evidence exists and is not a folder. Try to delete")
                os.remove("evidence")
            else:
                log.warning("No evidence folder")
            os.makedirs("evidence", exist_ok=True)
    except Exception as exception:
        log.error(f"Passing the evidence rotation. Receive error message {exception.args[0]}")


def before_all(context: Context) -> None:
    try:
        # Retrieve the execution mode from the command line input
        # NOTICE that the variable is 'modeDebug'
        set_logger("automaton", string_to_bool(context.config.userdata["modeDebug"]))

        # Create evidence folder (add rotation in here)
        make_evidence_rotation(3)

        # Manage your environment here.
        # Environment resource is a json file which primary key is the environment you want to run to
        log.debug(context.config.userdata)
        try:
            env = {**dotenv.dotenv_values(context.config.userdata["environment"]), **os.environ}
        except Exception as exception:
            log.error(exception)
        context.environment = {key: value for key, value in env.items() if key in ("URL",)}

        # Set here your model you want to access anytime in your steps
        # This model allows a history and reporting mechanism.
        # Use inheritance to create your own powerful model
        context.model = Dashboard()
        context.model.url = context.environment.get("URL")

        # For Web testing #####################################
        # Create a model which holds page elements as dictionary structure.
        # Build your pages as one dictionary and set for an anytime access
        ## Uncomment next
        context.model.elements = build_dataset("resources/ui_dataset")

        # For Web testing #######################################
        # Set the browser you want to use in this run
        # Retrieve the browser name from the command line
        # NOTICE that the variable is 'browser'
        ## Uncomment next
        context.model.browser.browser_name = context.config.userdata["browser"]

        # Managing dataset ######################################
        # Dataset is meant to be a single dictionary you can access anytime in your steps
        # Build your dataset and store it in the singleton holder
        # Map the singleton accessor to the context to ease the access
        # Update the path to match your base storage folder
        ## Uncomment next two lines
        data_holder.TEST_DATA = build_dataset("resources/dataset")
        context.retrieve_data = retrieve_data

    except Exception as exception:
        log.error(exception.args)
        raise Exception(exception)


def before_feature(
    context: Context,
    feature: Feature,
) -> None:
    log.info(f"==== Feature: {feature.name} ====")


def before_scenario(
    context: Context,
    scenario: Scenario,
) -> None:
    try:
        log.info(f"++++ Scenario: {scenario.name} ++++")
        log.info(f"++++ Tags are {scenario.tags} ++++")
        # Set pre_requisites dictionary in order to store data for future update and use
        context.pre_requisites = {}
        # Set post_conditions dictionary in order to store complex data for future validation
        context.post_conditions = {}
        # Build the evidence folder location for the current scenario, create it and store the path in the model
        evidence_folder = Path(
            f"evidence/{folder_file_name_cleaning(scenario.feature.name)}"
            f"/{folder_file_name_cleaning(scenario.name)}"
        )
        os.makedirs(evidence_folder.absolute(), exist_ok=True)
        context.model.evidence_location = evidence_folder.absolute()
        context.model.serve_and_access()
        # Clear the model history in order to record this scenario only events
        context.model.clear_history()
    except Exception as exception:
        log.exception(exception)


def before_step(context: Context, step: Step) -> None:
    log.debug(f"processing step: {step}")
    # Set the current step for the event historic
    context.model.step = step


def after_scenario(context: Context, scenario: Scenario) -> None:
    try:
        log.debug(f"{scenario.name} is {scenario.status}")
        context.model.create_evidence(
            f"{folder_file_name_cleaning(scenario.name)}-" f"{status_to_string(scenario.status)}.docx", "word"
        )
        # For Web testing #######################################
        # Your model should have a method to close the current browser.
        # The aim is to isolate tests from each others
        # Uncomment next if your method's name is 'close_browser'
        context.model.close_browser()

        # Clear current scenario history. Will be done again before starting a scenario
        context.model.clear_history()
        log.debug("End after_scenario")
    except Exception as exception:
        log.error(exception)


def after_all(context: Context) -> None:
    # For Web testing #######################################
    # Uncomment next if your method's name for closing a browser is 'close_browser'
    # context.model.close_browser()
    pass
