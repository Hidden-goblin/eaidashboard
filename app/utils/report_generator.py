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
    document.add_heading("Campaign summary")
    # Create table of tickets with a default column for acceptance criteria

    document.add_heading("Testability and impediment")
    # Create table of ticket with two column for testability and reason

    document.add_heading("Campaign scenario")
    # Create subsection for each tickets with table of scenario

    filename = BASE_DIR / "static" / f"Test_Plan_{provide(campaign.project_name)}_{campaign.version}_{uuid.uuid4()}.docx"

    document.save(filename)

    return filename