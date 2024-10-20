# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import abc
import csv
import uuid
from abc import ABC
from datetime import datetime
from math import pi
from typing import List, Tuple

from bokeh import resources
from bokeh.io import output_file, save
from bokeh.models import CategoricalColorMapper, ColumnDataSource
from bokeh.plotting import figure

from app.conf import BASE_DIR


class OutputStrategy(ABC):
    @staticmethod
    @abc.abstractmethod
    async def render(
        table_rows: List[Tuple],
    ) -> str | dict:
        pass


class StakedHtml(OutputStrategy):
    @staticmethod
    async def render(
        table_rows: List[Tuple],
    ) -> str:
        _json = await StakedJson().render(table_rows)
        max_y = max(
            _json["passed"][index] + _json["skipped"][index] + _json["failed"][index]
            for index in range(len(_json["run_date"]))
        )
        filename = BASE_DIR / "static" / f"testoutput_{uuid.uuid4()}.html"
        output_file(
            filename=filename,
            title="Stacked status over time",
        )
        p = figure(
            y_range=(0, max_y),
            x_axis_type="datetime",
            sizing_mode="stretch_both",
        )
        p.varea_stack(
            stackers=[
                "failed",
                "skipped",
                "passed",
            ],
            x="run_date",
            color=[
                "red",
                "gray",
                "green",
            ],
            legend_label=[
                "failed",
                "skipped",
                "passed",
            ],
            source=ColumnDataSource(_json),
        )
        save(
            p,
            resources=resources.INLINE,
        )
        return filename.name


class StakedCsv(OutputStrategy):
    @staticmethod
    async def render(
        table_rows: List[Tuple],
    ) -> str:
        # TODO add triggered background task to remove old files [Register here]
        filename = BASE_DIR / "static" / f"testoutput_{uuid.uuid4()}.csv"
        with open(
            filename,
            "w",
            newline="",
        ) as file:
            _csv = csv.writer(
                file,
                quoting=csv.QUOTE_ALL,
            )
            _csv.writerow(
                (
                    "run_date",
                    "passed",
                    "failed",
                    "skipped",
                ),
            )
            _csv.writerows(table_rows)
        return filename.name


class StakedJson(OutputStrategy):
    @staticmethod
    async def render(
        table_rows: List[Tuple],
    ) -> dict:
        result = {
            "run_date": [],
            "passed": [],
            "failed": [],
            "skipped": [],
        }
        for row in table_rows:
            result["run_date"].append(row[0])
            result["passed"].append(row[1])
            result["skipped"].append(row[2])
            result["failed"].append(row[3])
        return result


class MapHtml(OutputStrategy):
    @staticmethod
    async def render(table_rows: List[Tuple]) -> str:
        _json = await MapJson().render(table_rows)

        mapper = CategoricalColorMapper(
            palette=[
                "red",
                "green",
                "gray",
            ],
            factors=[
                "failed",
                "passed",
                "skipped",
            ],
        )
        item: datetime  # noqa: F842
        _dates_range = [
            item.strftime("%Y-%m-%dT%H:%M:%S")
            for item in sorted(
                set(
                    _json["run_date"],
                ),
            )
        ]
        _dates = [item.strftime("%Y-%m-%dT%H:%M:%S") for item in _json["run_date"]]
        _json["run_date"] = _dates
        _elements_names = sorted(list(set(_json["element_name"])))
        filename = BASE_DIR / "static" / f"testoutput_{uuid.uuid4()}.html"
        output_file(
            filename=filename,
            title="Status map over time",
        )
        TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom"
        p = figure(
            title="Test map result",
            x_range=_dates_range,
            y_range=_elements_names,
            x_axis_location="above",
            sizing_mode="stretch_both",
            tools=TOOLS,
            toolbar_location="below",
            tooltips=[
                ("Test: ", "@element_name"),
                ("Result_date", "@run_date"),
                ("Status", "@element_status"),
            ],
        )

        p.grid.grid_line_color = None
        p.axis.axis_line_color = None
        p.axis.major_tick_line_color = None
        p.axis.major_label_text_font_size = "7px"
        p.axis.major_label_standoff = 0
        p.xaxis.major_label_orientation = pi / 3
        p.rect(
            x="run_date",
            y="element_name",
            width=1,
            height=1,
            source=_json,
            fill_color={
                "field": "element_status",
                "transform": mapper,
            },
            line_color=None,
        )
        save(p, resources=resources.INLINE)
        return filename.name


class MapCsv(OutputStrategy):
    @staticmethod
    async def render(table_rows: List[Tuple]) -> str:
        filename = BASE_DIR / "static" / f"testoutput_{uuid.uuid4()}.csv"
        with open(filename, "w", newline="") as file:
            _csv = csv.writer(
                file,
                quoting=csv.QUOTE_ALL,
            )
            _csv.writerow(
                (
                    "run_date",
                    "element_id",
                    "status",
                    "element_name",
                ),
            )
            _csv.writerows(table_rows)
        return filename.name


class MapJson(OutputStrategy):
    @staticmethod
    async def render(table_rows: List[Tuple]) -> dict:
        result = {
            "run_date": [],
            "element_id": [],
            "element_status": [],
            "element_name": [],
        }
        for row in table_rows:
            result["run_date"].append(row[0])
            result["element_id"].append(row[1])
            result["element_status"].append(row[2])
            result["element_name"].append(row[3])
        return result


REGISTERED_OUTPUT = {
    "map": {
        "text/csv": MapCsv,
        "application/json": MapJson,
        "text/html": MapHtml,
    },
    "stacked": {
        "text/csv": StakedCsv,
        "application/json": StakedJson,
        "text/html": StakedHtml,
    },
}
