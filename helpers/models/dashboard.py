# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from copy import deepcopy
from logging import getLogger

import dpath
from eaiautomatontools.browserServer import BrowserServer
from eaiBat import EaiBat

from helpers.models.models import UserModel

log = getLogger(__name__)


class Dashboard(EaiBat):
    def __init__(self: "Dashboard") -> None:
        super().__init__()
        self.__browser: BrowserServer = BrowserServer()
        self.__is_serving = False
        self.__elements = None

    @property
    def browser(self: "Dashboard") -> BrowserServer:
        return self.__browser

    @browser.setter
    def browser(self: "Dashboard", browser_name: str) -> None:
        self.__browser.browser_name = browser_name

    @property
    def elements(self: "Dashboard") -> dict:
        return self.__elements

    @elements.setter
    def elements(self: "Dashboard", elements: dict) -> None:
        self.__elements = elements

    def composer(self: "Dashboard") -> dict:
        return {
            "url": self.url,
            "push_event": self.push_event,
            "step": self.step,
            "evidence_location": self.evidence_location,
        }

    def ui_element(self: "Dashboard", path: str) -> dict | str:
        """Access the data dictionary by its path and returns a deepcopy"""
        try:
            # noinspection PyTypeChecker
            return deepcopy(dpath.get(self.__elements, path))
        except KeyError as ke:
            log.error(repr(ke))
            raise Exception(f"Could not find {path} within the ui elements")

    def take_screenshot(self: "Dashboard", message: str = None) -> None:
        if message is not None:
            self.push_event(message)
        self.push_event((self.__browser.take_a_screenshot(self.evidence_location), "img"))

    def serve_and_access(self: "Dashboard") -> None:
        log.info("Starting browser")
        if not self.__browser.is_launched:
            self.__browser.serve()
        self.__browser.go_to(self.url)
        self.__browser.is_field_displayed(self.ui_element("headers/documentation"), wait_until=2)
        self.__is_serving = True

    def close_browser(self: "Dashboard") -> None:
        if self.__browser.is_launched:
            self.__browser.close()
        self.__is_serving = False

    def log_in(self: "Dashboard", user: UserModel) -> None:
        log.info(f"User to process is {user}")
        self.__browser.is_field_displayed(self.ui_element("headers/log"), wait_until=2)
        self.take_screenshot("Page ready for log in")
        self.__browser.click_element(self.ui_element("headers/log"))
        self.__browser.is_field_displayed(self.ui_element("forms/authentication/username"), wait_until=2)
        self.__browser.fill_element(field=self.ui_element("forms/authentication/username"), value=user.username)
        self.__browser.fill_element(field=self.ui_element("forms/authentication/password"), value=user.password)
        self.take_screenshot("Authentication form filled")
        self.__browser.click_element(self.ui_element("forms/authentication/submit"))
        self.__browser.is_field_displayed(self.ui_element("headers/unlog"), wait_until=1)
        self.take_screenshot("Authentication form submitted")

    def create_user(self: "Dashboard", new_user: UserModel) -> None:
        try:
            self.__browser.click_element(self.ui_element("headers/user_management"))
            self.__browser.is_field_displayed(self.ui_element("user_management/create_user"), wait_until=2)
            self.take_screenshot("Move to the User management page")
            self.__browser.click_element(self.ui_element("user_management/create_user"))
            self.take_screenshot("Open the create user form")

        except Exception as exception:
            log.error(exception)
            raise
