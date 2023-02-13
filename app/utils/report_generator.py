# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import uuid

from docx.document import Document

from app.conf import BASE_DIR
from app.schema.campaign_schema import CampaignFull
from app.utils.project_alias import provide


def test_plan_from_campaign(campaign: CampaignFull) -> str:
    document = Document()
    document.add_heading("Test Plan", 0)
    subtitle = document.add_paragraph(f"Campaign for {campaign.project_name} "
                                      f"in version {campaign.version}", style="Subtitle")
    document.add_page_break()
    document.add_heading("Test scope")
    # Create table of tickets with a default column for acceptance criteria

    document.add_heading("Test environment")
    # Add test environment

    document.add_heading("Test scope impediments and non-testable items")
    # Create table of ticket with two column for testability and reason

    document.add_heading("Test scope estimation")
    # Add table of ticket with one column for estimation
    # Add total estimation 
    # Add start and end forecast

    document.add_heading("Campaign scenario")
    # Create subsection for each tickets with table of scenario

    filename = BASE_DIR / "static" / f"Test_Plan_{provide(campaign.project_name)}_{campaign.version}_{uuid.uuid4()}.docx"

    document.save(filename)

    return filename



def test_exit_report_from_campaign(campaign: CampaignFull) -> str:
    document = Document()
    document.add_heading("Test Plan", 0)
    subtitle = document.add_paragraph(f"Campaign for {campaign.project_name} "
                                      f"in version {campaign.version}", style="Subtitle")
    document.add_page_break()
    document.add_heading("Test campaign overview")
    # Add go/no go sentence

    document.add_heading("Test scope")
    # Create table of ticket

    document.add_heading("Test campaign indicators")
    document.add_heading("Environment", 2)
    # Add template for test environment

    document.add_heading("Schedule", 2)
    # Add test campaign start/end dates or leave it blank

    document.add_heading("Impediment", 2)
    # Add template for impediment section

    document.add_heading("Test result summary")
    # Create table of ticket with computed status based on scenarios status

    document.add_heading("Defect status")
    # Create table of defect within the version

    filename = BASE_DIR / "static" / f"TER_{provide(campaign.project_name)}_{campaign.version}_{campaign.occurrence}{uuid.uuid4()}.docx"

    document.save(filename)

    return filename