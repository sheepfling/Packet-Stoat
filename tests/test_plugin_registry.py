from __future__ import annotations

import pytest

from fastdis.plugins import ENTRY_POINT_GROUPS, entry_point_group


def test_known_plugin_groups_are_stable() -> None:
    assert ENTRY_POINT_GROUPS["entity_publishers"] == "fastdis.entity_publishers"
    assert ENTRY_POINT_GROUPS["entity_streams"] == "fastdis.entity_streams"
    assert ENTRY_POINT_GROUPS["workflows"] == "fastdis.workflows"


def test_unknown_plugin_group_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown fastdis plugin kind"):
        entry_point_group("does-not-exist")
