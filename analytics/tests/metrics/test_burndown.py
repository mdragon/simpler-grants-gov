"""Test the analytics.metrics.burndown module."""
from datetime import datetime, timedelta, timezone

import pandas as pd
import pytest
from analytics.datasets.sprint_board import SprintBoard
from analytics.metrics.burndown import SprintBurndown, Unit

from tests.conftest import (
    DAY_0,
    DAY_1,
    DAY_2,
    DAY_3,
    DAY_4,
    sprint_row,
)


def result_row(
    day: str,
    opened: int,
    closed: int,
    delta: int,
    total: int,
) -> dict:
    """Create a sample result row."""
    return {
        "date": pd.Timestamp(day, tz="UTC"),
        "opened": opened,
        "closed": closed,
        "delta": delta,
        "total_open": total,
    }


class TestSprintBurndownByTasks:
    """Test the SprintBurndown class with unit='tasks'."""

    def test_exclude_tix_assigned_to_other_sprints(self):
        """The burndown should exclude tickets that are assigned to other sprints."""
        # setup - create test data
        sprint_data = [
            # fmt: off
            # include this row - assigned to sprint 1
            sprint_row(issue=1, sprint=1, sprint_start=DAY_1, created=DAY_1, closed=DAY_3),
            # exclude this row - assigned to sprint 2
            sprint_row(issue=1, sprint=2, sprint_start=DAY_4, created=DAY_0, closed=DAY_4),
            # fmt: on
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        df = output.results
        # validation - check min and max dates
        assert df[output.date_col].min() == pd.Timestamp(DAY_1, tz="UTC")
        assert df[output.date_col].max() == pd.Timestamp(DAY_3, tz="UTC")
        # validation - check burndown output
        expected = [
            result_row(day=DAY_1, opened=1, closed=0, delta=1, total=1),
            result_row(day=DAY_2, opened=0, closed=0, delta=0, total=1),
            result_row(day=DAY_3, opened=0, closed=1, delta=-1, total=0),
        ]
        assert df.to_dict("records") == expected

    def test_count_tix_created_before_sprint_start(self):
        """Burndown should include tix opened before the sprint but closed during it."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, closed=DAY_2),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, closed=DAY_3),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        df = output.results
        # validation - check min and max dates
        assert df[output.date_col].min() == pd.Timestamp(DAY_0, tz="UTC")
        assert df[output.date_col].max() == pd.Timestamp(DAY_3, tz="UTC")
        # validation - check burndown output
        expected = [
            result_row(day=DAY_0, opened=2, closed=0, delta=2, total=2),
            result_row(day=DAY_1, opened=0, closed=0, delta=0, total=2),
            result_row(day=DAY_2, opened=0, closed=1, delta=-1, total=1),
            result_row(day=DAY_3, opened=0, closed=1, delta=-1, total=0),
        ]
        assert df.to_dict("records") == expected

    def test_count_tix_closed_after_sprint_start(self):
        """Burndown should include tix closed after the sprint ended."""
        # setup - create test data
        sprint_data = [
            sprint_row(  # closed before sprint end
                issue=1,
                sprint_start=DAY_1,
                sprint_length=2,
                created=DAY_1,
                closed=DAY_2,
            ),
            sprint_row(  # closed after sprint end
                issue=1,
                sprint_start=DAY_1,
                sprint_length=2,
                created=DAY_1,
                closed=DAY_4,
            ),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        df = output.results
        # validation - check min and max dates
        assert df[output.date_col].min() == pd.Timestamp(DAY_1, tz="UTC")
        assert df[output.date_col].max() == pd.Timestamp(DAY_4, tz="UTC")
        # validation - check burndown output
        expected = [
            result_row(day=DAY_1, opened=2, closed=0, delta=2, total=2),
            result_row(day=DAY_2, opened=0, closed=1, delta=-1, total=1),
            result_row(day=DAY_3, opened=0, closed=0, delta=0, total=1),
            result_row(day=DAY_4, opened=0, closed=1, delta=-1, total=0),
        ]
        assert df.to_dict("records") == expected

    def test_count_tix_created_after_sprint_start(self):
        """Burndown should include tix opened and closed during the sprint."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, closed=DAY_2),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_2, closed=DAY_3),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        df = output.results
        # validation - check burndown output
        expected = [
            result_row(day=DAY_0, opened=1, closed=0, delta=1, total=1),
            result_row(day=DAY_1, opened=0, closed=0, delta=0, total=1),
            result_row(day=DAY_2, opened=1, closed=1, delta=0, total=1),
            result_row(day=DAY_3, opened=0, closed=1, delta=-1, total=0),
        ]
        assert df.to_dict("records") == expected

    def test_include_all_sprint_days_if_tix_closed_early(self):
        """All days of the sprint should be included even if all tix were closed early."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, closed=DAY_1),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, closed=DAY_1),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        df = output.results
        # validation - check max date is end of sprint not last closed date
        assert df[output.date_col].max() == pd.Timestamp(DAY_3, tz="UTC")

    def test_raise_value_error_if_sprint_arg_not_in_dataset(self):
        """A ValueError should be raised if the sprint argument isn't valid."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, closed=DAY_1),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # validation
        with pytest.raises(
            ValueError,
            match="Sprint value doesn't match one of the available sprints",
        ):
            SprintBurndown(test_data, sprint="Fake sprint", unit=Unit.issues)

    def test_calculate_burndown_for_current_sprint(self):
        """A ValueError should be raised if the sprint argument isn't valid."""
        # setup - create test data
        now = datetime.now(tz=timezone.utc)
        day_1 = now.strftime("%Y-%m-%d")
        day_2 = (now + timedelta(days=1)).strftime("%Y-%m-%d")
        day_3 = (now + timedelta(days=2)).strftime("%Y-%m-%d")
        sprint_data = [
            sprint_row(issue=1, sprint_start=day_1, created=day_1, closed=day_2),
            sprint_row(issue=1, sprint_start=day_1, created=day_1),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        df = output.results
        # validation - check burndown output
        expected = [
            result_row(day=day_1, opened=2, closed=0, delta=2, total=2),
            result_row(day=day_2, opened=0, closed=1, delta=-1, total=1),
            result_row(day=day_3, opened=0, closed=0, delta=0, total=1),
        ]
        assert df.to_dict("records") == expected


class TestSprintBurndownByPoints:
    """Test the SprintBurndown class with unit='points'."""

    def test_burndown_works_with_points(self):
        """Burndown should be calculated correctly with points."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, points=2),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_2, points=3),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.points)
        df = output.results
        # validation
        expected = [
            result_row(day=DAY_0, opened=2, closed=0, delta=2, total=2),
            result_row(day=DAY_1, opened=0, closed=0, delta=0, total=2),
            result_row(day=DAY_2, opened=3, closed=0, delta=3, total=5),
            result_row(day=DAY_3, opened=0, closed=0, delta=0, total=5),
        ]
        assert df.to_dict("records") == expected

    def test_burndown_excludes_tix_without_points(self):
        """Burndown should exclude tickets that are not pointed."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_1, points=2),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_2, points=0),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_2, points=None),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.points)
        df = output.results
        # validation
        expected = [
            result_row(day=DAY_1, opened=2, closed=0, delta=2, total=2),
            result_row(day=DAY_2, opened=0, closed=0, delta=0, total=2),
            result_row(day=DAY_3, opened=0, closed=0, delta=0, total=2),
        ]
        assert df.to_dict("records") == expected


class TestGetStats:
    """Test the SprintBurndown.get_stats() method."""

    SPRINT_START = "Sprint start date"
    SPRINT_END = "Sprint end date"
    TOTAL_OPENED = "Total opened"
    TOTAL_CLOSED = "Total closed"
    PCT_CLOSED = "Percent closed"
    PCT_POINTED = "Percent pointed"

    def test_sprint_start_and_sprint_end_not_affected_by_unit(self):
        """Test that sprint start and end are the same regardless of unit."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, closed=DAY_2),
            sprint_row(issue=2, sprint_start=DAY_1, created=DAY_2, closed=DAY_4),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        points = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.points)
        issues = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        # validation - check they're calculated correctly
        assert points.stats.get(self.SPRINT_START).value == DAY_1
        assert points.stats.get(self.SPRINT_END).value == DAY_3
        # validation - check that they are the same
        # fmt: off
        assert points.stats.get(self.SPRINT_START) == issues.stats.get(self.SPRINT_START)
        assert points.stats.get(self.SPRINT_END) == issues.stats.get(self.SPRINT_END)
        # fmt: on

    def test_get_total_closed_and_opened_when_unit_is_issues(self):
        """Test that total_closed is calculated correctly when unit is issues."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint=1, created=DAY_0, closed=DAY_2),
            sprint_row(issue=2, sprint=1, created=DAY_0, closed=DAY_3),
            sprint_row(issue=3, sprint=1, created=DAY_2),  # not closed
            sprint_row(issue=4, sprint=1, created=DAY_2),  # not closed
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        print(output.results)
        # validation - check that stats were calculated correctly
        assert output.stats.get(self.TOTAL_CLOSED).value == 2
        assert output.stats.get(self.TOTAL_OPENED).value == 4
        assert output.stats.get(self.PCT_CLOSED).value == 50.0
        # validation - check that message contains string value of Unit.issues
        assert Unit.issues.value in output.stats.get(self.TOTAL_CLOSED).suffix
        assert Unit.issues.value in output.stats.get(self.TOTAL_OPENED).suffix
        assert "%" in output.stats.get(self.PCT_CLOSED).suffix

    def test_get_total_closed_and_opened_when_unit_is_points(self):
        """Test that total_closed is calculated correctly when unit is issues."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint=1, created=DAY_1, points=2, closed=DAY_2),
            sprint_row(issue=2, sprint=1, created=DAY_2, points=1, closed=DAY_4),
            sprint_row(issue=3, sprint=1, created=DAY_2, points=2),  # not closed
            sprint_row(issue=4, sprint=1, created=DAY_2, points=4),  # not closed
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.points)
        # validation
        assert output.stats.get(self.TOTAL_CLOSED).value == 3
        assert output.stats.get(self.TOTAL_OPENED).value == 9
        assert output.stats.get(self.PCT_CLOSED).value == 33.33  # rounded to 2 places
        # validation - check that message contains string value of Unit.points
        assert Unit.points.value in output.stats.get(self.TOTAL_CLOSED).suffix
        assert Unit.points.value in output.stats.get(self.TOTAL_OPENED).suffix
        assert "%" in output.stats.get(self.PCT_CLOSED).suffix

    def test_include_issues_closed_after_sprint_end(self):
        """Issues that are closed after sprint ended should be included in closed count."""
        # setup - create test data
        sprint_data = [
            sprint_row(  # closed during sprint
                issue=1,
                sprint_start=DAY_1,
                sprint_length=2,
                created=DAY_1,
                closed=DAY_2,
            ),
            sprint_row(  # closed after sprint
                issue=2,
                sprint_start=DAY_1,
                sprint_length=2,
                created=DAY_2,
                closed=DAY_4,
            ),
            sprint_row(  # not closed
                issue=3,
                sprint_start=DAY_1,
                sprint_length=2,
                created=DAY_2,
            ),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        # validation
        assert output.stats.get(self.TOTAL_CLOSED).value == 2
        assert output.stats.get(self.TOTAL_OPENED).value == 3
        assert output.stats.get(self.PCT_CLOSED).value == 66.67  # rounded to 2 places

    def test_get_percent_pointed(self):
        """Test that percent pointed is calculated correctly."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint=1, created=DAY_1, points=2, closed=DAY_2),
            sprint_row(issue=2, sprint=1, created=DAY_2, points=1, closed=DAY_4),
            sprint_row(issue=3, sprint=1, created=DAY_2, points=None),  # not pointed
            sprint_row(issue=4, sprint=1, created=DAY_2, points=0),  # not closed
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.points)
        # validation
        assert output.stats.get(self.TOTAL_CLOSED).value == 3
        assert output.stats.get(self.TOTAL_OPENED).value == 3
        assert output.stats.get(self.PCT_CLOSED).value == 100
        assert output.stats.get(self.PCT_POINTED).value == 50
        # validation - check that stat contains '%' suffix
        assert f"% of {Unit.issues.value}" in output.stats.get(self.PCT_POINTED).suffix

    def test_exclude_other_sprints_in_percent_pointed(self):
        """Only include issues in this sprint when calculating percent pointed."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint=1, created=DAY_1, points=2, closed=DAY_2),
            sprint_row(issue=2, sprint=1, created=DAY_2, points=1, closed=DAY_4),
            sprint_row(issue=3, sprint=1, created=DAY_2, points=None),  # not pointed
            sprint_row(issue=4, sprint=2, created=DAY_2, points=None),  # other sprint
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        # validation
        assert output.stats.get(self.TOTAL_CLOSED).value == 2
        assert output.stats.get(self.TOTAL_OPENED).value == 3
        assert output.stats.get(self.PCT_POINTED).value == 66.67  # exclude final row


class TestFormatSlackMessage:
    """Test the DeliverablePercentComplete.format_slack_message()."""

    def test_slack_message_contains_right_number_of_lines(self):
        """Message should contain one line for the title and one for each stat."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, points=2),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_2, points=3),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.points)
        lines = output.format_slack_message().splitlines()
        for line in lines:
            print(line)
        # validation
        assert len(lines) == len(list(output.stats)) + 1

    def test_title_includes_issues_when_unit_is_issue(self):
        """Test that the title is formatted correctly when unit is issues."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, points=2),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_2, points=3),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.issues)
        title = output.format_slack_message().splitlines()[0]
        # validation
        assert Unit.issues.value in title

    def test_title_includes_points_when_unit_is_points(self):
        """Test that the title is formatted correctly when unit is points."""
        # setup - create test data
        sprint_data = [
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_0, points=2),
            sprint_row(issue=1, sprint_start=DAY_1, created=DAY_2, points=3),
        ]
        test_data = SprintBoard.from_dict(sprint_data)
        # execution
        output = SprintBurndown(test_data, sprint="Sprint 1", unit=Unit.points)
        title = output.format_slack_message().splitlines()[0]
        # validation
        assert Unit.points.value in title
