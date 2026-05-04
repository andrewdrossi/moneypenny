# Moneypenny Integrated Investment Intelligence

Moneypenny is a high-fidelity investment agent system built to bridge the gap between hard financial metrics and personalized "Soft Data" like executive tone and macro-geopolitical events. The UI showcases the core agent reasoning (ReAct loop).

## Technical Rigor & Architecture
This project is separated into distinct, modular components:
1. **Tools (`core/tools`)**: Contains scripts for external data fetching (Alpha Vantage for quantitative data) and simulated transcript processing for qualitative data ("Executive Tone"). Local persistence is managed via JSON.
2. **Synthesis Engine (`core/engine.py`)**: The brain of Moneypenny. It implements a ReAct loop:
   - Injects the user's "Investor Profile" (risk tolerance, biases, demographics).
   - Fetches structural market data and qualitative executive tone.
   - Synthesizes findings using an LLM (Google Gemini by default).
   - Implements dynamic profile adjustments based on direct feedback in chat.
3. **User Experience (`ui/app.py`)**: A Streamlit application providing 100% transparency into the engine's real-time reasoning.

## Reproducibility Guide
### Prerequisites
- Python 3.10+
- An API Key for Gemini (set `GEMINI_API_KEY` in environment, e.g., via `.env` file or export)
- (Optional) An API Key for Alpha Vantage (set `ALPHA_VANTAGE_API_KEY` in environment, otherwise a demo key is used).

### Installation & Execution

```bash
# 1. Navigate to the directory
cd moneypenny

# 2. Set up virtual environment and install dependencies
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Run the Streamlit Application
streamlit run ui/app.py
```
