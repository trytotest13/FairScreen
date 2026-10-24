import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Offline, deterministic ranking
os.environ["FAIRSCREEN_EMBEDDINGS"] = "off"
os.environ["FAIRSCREEN_CUTOFF"] = "8"

from streamlit.testing.v1 import AppTest


def test_rank_flow_produces_table_and_audit():
    fixture = ROOT / "sample_data" / "out"
    if not fixture.exists():
        from sample_data.generate import build_fixture

        build_fixture(fixture)

    at = AppTest.from_file(str(ROOT / "fairscreen" / "app.py"), default_timeout=180)
    at.run()
    assert not at.exception

    at.sidebar.button[0].click().run()  # "Rank candidates"
    assert not at.exception
    assert at.dataframe, "ranking table should render"
    assert at.tabs, "Ranking / detail / audit / export tabs should render"


def test_toggle_change_invalidates_stale_ranking():
    at = AppTest.from_file(str(ROOT / "fairscreen" / "app.py"), default_timeout=180)
    at.run()
    at.sidebar.button[0].click().run()
    assert at.dataframe

    at.sidebar.toggle[0].set_value(False).run()  # turn redaction off
    assert not at.exception
    # the main block shows the "load candidates" info again when ranking is gone
    assert len(at.info) >= 1, "stale ranking should be invalidated when the redaction toggle changes"
