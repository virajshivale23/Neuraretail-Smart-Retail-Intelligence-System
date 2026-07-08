"""
Individual dashboard page renderers for NeuralRetail.

Each module exposes a `render(...)` function that takes the already-loaded
DataFrames it needs and draws its section of the Streamlit UI. app_v2.py
stays the single entry point / router; these modules keep each page's
logic isolated and testable.
"""
