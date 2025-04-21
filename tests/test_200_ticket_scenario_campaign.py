# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from app.schema.campaign_schema import TicketScenarioCampaign
from app.schema.respository.feature_schema import Feature
from app.schema.respository.scenario_schema import BaseScenario


class TestTicketScenarioCampaign:
    def test_no_feature(self: "TestTicketScenarioCampaign") -> None:
        ticket_ref = TicketScenarioCampaign(ticket_reference="ticket_2")
        assert ticket_ref.to_features("test_project") == [], f"Get '{ticket_ref.to_features('test_project')}'"

    def test_one_base_scenario(self: "TestTicketScenarioCampaign") -> None:
        ticket_ref = TicketScenarioCampaign(
            ticket_reference="ticket_2",
            scenarios=BaseScenario(scenario_id="test1", epic="epic1", feature_name="feature1"),
        )
        expected = [Feature(epic_name="epic1", name="feature1", project_name="test_project", scenario_ids=["test1"])]
        assert ticket_ref.to_features("test_project") == expected, (
            f"{ticket_ref.to_features('test_project')} instead of {expected}"
        )

    def test_list_one_scenario(self: "TestTicketScenarioCampaign") -> None:
        ticket_ref = TicketScenarioCampaign(
            ticket_reference="ticket_2",
            scenarios=[BaseScenario(scenario_id="test1", epic="epic1", feature_name="feature1")],
        )
        expected = [Feature(epic_name="epic1", name="feature1", project_name="test_project", scenario_ids=["test1"])]
        assert ticket_ref.to_features("test_project") == expected, (
            f"{ticket_ref.to_features('test_project')} instead of {expected}"
        )

    def test_list_scenarios_same_feature(self: "TestTicketScenarioCampaign") -> None:
        ticket_ref = TicketScenarioCampaign(
            ticket_reference="ticket_2",
            scenarios=[
                BaseScenario(scenario_id="test1", epic="epic1", feature_name="feature1"),
                BaseScenario(scenario_id="test2", epic="epic1", feature_name="feature1"),
            ],
        )
        expected = [
            Feature(epic_name="epic1", name="feature1", project_name="test_project", scenario_ids=["test1", "test2"])
        ]
        assert ticket_ref.to_features("test_project") == expected, (
            f"{ticket_ref.to_features('test_project')} instead of {expected}"
        )

    def test_list_scenarios_different_features(self: "TestTicketScenarioCampaign") -> None:
        ticket_ref = TicketScenarioCampaign(
            ticket_reference="ticket_2",
            scenarios=[
                BaseScenario(scenario_id="test1", epic="epic1", feature_name="feature1"),
                BaseScenario(scenario_id="test1", epic="epic1", feature_name="feature2"),
                BaseScenario(scenario_id="test1", epic="epic2", feature_name="feature1"),
            ],
        )
        expected = [
            Feature(epic_name="epic1", name="feature1", project_name="test_project", scenario_ids=["test1"]),
            Feature(epic_name="epic1", name="feature2", project_name="test_project", scenario_ids=["test1"]),
            Feature(epic_name="epic2", name="feature1", project_name="test_project", scenario_ids=["test1"]),
        ]
        assert ticket_ref.to_features("test_project") == expected, (
            f"{ticket_ref.to_features('test_project')} instead of {expected}"
        )
