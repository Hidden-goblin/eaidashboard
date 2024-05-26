# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from logging import getLogger

import requests
from eaiBat import EaiBat

from helpers.models.models import ApiUserModel, UserModel

log = getLogger(__name__)


class ApiDashboard(EaiBat):
    def __init__(self, url, push_event, step, evidence_location):
        super().__init__()
        self.__user: ApiUserModel | None = None
        self.url = url
        self.push_event = push_event
        self.step = step
        self.evidence_location = evidence_location

    @property
    def user(self):
        return self.__user

    @user.setter
    def user(self, user: UserModel):
        self.__user = ApiUserModel(**user.dict())

    def headers(self):
        if self.__user.token is None:
            self.log_in()
        return {"Authorization": f"Bearer {self.__user.token}"}

    def log_in(self):
        _resp = requests.post(f"{self.url}/api/v1/token",
                              data={"username": self.__user.username,
                                    "password": self.__user.password})
        if _resp.status_code == 200:
            self.__user.token = _resp.json()["access_token"]
        else:
            raise Exception(f"Cannot log in. Receive code '{_resp.status_code}' \n message: '{_resp.text}'")

    def list_of_projects(self):

        _resp = requests.get(f"{self.url}/api/v1/settings/projects",
                             headers=self.headers())
        if _resp.status_code != 200:
            raise Exception(f"Cannot retrieve project lists.\nCode:'{_resp.status_code}'\n message: '{_resp.text}")
        return _resp.json()

    def create_project(self, project_name: str):
        _resp = requests.post(f"{self.url}/api/v1/settings/projects",
                              headers=self.headers(),
                              data={"name": project_name})
        if _resp.status_code != 200:
            raise Exception(
                f"Cannot create project '{project_name}'.\nCode :'{_resp.status_code}'\n message: '{_resp.text}'")
