"""Smoke test for Streamlit app ensuring it loads and runs without exceptions when GROQ_API_KEY is absent."""

import os
from streamlit.testing.v1 import AppTest


def test_streamlit_app_loads_without_exceptions_no_api_key(monkeypatch):
    """Verify that streamlit_app.py initializes cleanly without exceptions even if no API key is present."""
    # Ensure GROQ_API_KEY is absent from environment
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    # Initialize and run AppTest
    at = AppTest.from_file("streamlit_app.py", default_timeout=30)
    at.run()

    # Assert no exceptions occurred during execution
    assert not at.exception
    # Assert main title is rendered
    assert len(at.title) > 0
    assert "Government Scheme Finder" in at.title[0].value

    # Verify clicking Find Schemes button runs without crashing (uses explainer fallback)
    at.button[0].click().run()
    assert not at.exception
