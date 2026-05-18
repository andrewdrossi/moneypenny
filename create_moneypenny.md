# Skill: Moneypenny Full-Stack Architect (The Builder)

## Description
You are a Senior Full-Stack Engineer and AI Architect. Your mission is to physically construct "Moneypenny"—a high-fidelity investment agent system. The goal is to build an application where the UI serves as a window into the agent's complex reasoning process, bridging the gap between raw financial data and personalized user wealth-tech.

## Project Definition
Moneypenny is an "Integrated Investment Intelligence" platform. It synthesizes hard financial metrics (P/E, Price) with qualitative "Soft Data" (Executive tone from earnings transcripts and macro-geopolitical events). 

## Instructions for Application Construction
When triggered by "Moneypenny, build the system," you must generate the following infrastructure and User Interface components:

### 1. Environment & Core Tools (`moneypenny/tools/`)
- **`yfinance_mcp.py`**: A robust MCP server for fetching Market Quotes, Sentiment Scores, and News via YFinance.
- **`transcript_processor.py`**: A specialized tool to parse earnings call transcripts for "Executive Tone" indicators.
- **`portfolio_database.py`**: A local persistence layer (JSON or SQLite) to store the User's Rich Profile and Recommendation History.

### 2. The User Experience Layer (`moneypenny/ui/`)
Generate a modern, dashboard-style interface (using a Python-based UI framework like Streamlit or a React-inspired layout) consisting of:

- **Component A: Central Intelligence Chat**:
    - A clean chat interface where users query Moneypenny (e.g., "Analyze my exposure to tech given today's Fed announcement").
    - Supports markdown formatting for financial tables and bold summaries.

- **Component B: The "Analyst Notebook" (Side Window)**:
    - A dedicated "Reasoning Panel" that displays the Agent's ReAct (Reason + Act) loop in real-time.
    - It must show the "Thought," "Tool Used," and "Observation" behind the current recommendation, providing 100% transparency.

- **Component C: Recommendation Vault (Historical Feed)**:
    - A persistent sidebar list showing historical recommendations (e.g., "$AAPL - Buy - 2024-05-10").
    - Clicking an item restores the original reasoning in the Analyst Notebook.

- **Component D: The "Investor Profile" Profile Dashboard**:
    - A rich-data entry form for users to input:
        - **Personal Metadata**: Age, dependants, and retirement horizon.
        - **Risk Parameters**: Tolerance for volatility (1-10) and specific industry exclusions (e.g., "No tobacco stocks").
        - **Financial Goals**: Capital preservation vs. aggressive growth.

### 3. The Synthesis Engine (`moneypenny/core/engine.py`)
Write the logic that connects the UI to the Tools:
- **Profile Injection**: Every LLM prompt must be prefixed with the "Investor Profile" to ensure recommendations are hyper-personalized.
- **Synthesis Loop**: Code that fetches data, runs the sentiment analysis, and formats the output for the Chat and Reasoning panels simultaneously.

### 4. Technical Documentation
- **`README.md`**: Technical overview for the MBA panel.
- **`USER_GUIDE.md`**: Instructions on how to input rich data and interpret the "Analyst Notebook."

## 5. Definition of Done: Functional Requirements
The system is considered complete only when the following interaction loop is fully functional:

### Phase A: Onboarding & Profile Persistence
- **Onboarding Logic**: Upon first launch, Moneypenny must initiate a diagnostic dialogue to capture the following metadata:
    - **Demographics**: Age and Job.
    - **Financial Profile**: Risk-tolerance, Financial Literacy level, and Liquid Resources available for investment.
    - **Strategy Prefs**: Management level preference (Passive vs. Active).
    - **Cognitive Bias/Interests**: Personal beliefs about the economy or specific market sectors.
- **Persistence**: These variables must be saved to `moneypenny/data/user_profile.json` and persist across sessions.

### Phase B: Context-Aware Recommendation Engine
- **The "Brain" Trigger**: Moneypenny must inject the above profile data into every analysis.
- **Data Synthesis**: Recommendations must be a weighted output of:
    - **Current Prices & Trends** (Quantitative).
    - **Earnings Sentiment & Tone** (Qualitative).
    - **User DNA** (Personal Context).
- **Format**: The final output must be a "Personalized Portfolio Action Plan" presented in the chat window, with the raw data fetch logged in the Side Window.

### Phase C: Feedback & Refinement Loop
- **Iteration Logic**: Moneypenny must respond to user feedback (e.g., "This is too risky" or "I don't like tech stocks").
- **Dynamic Adjustments**: When feedback is received, the agent must:
    1. Update the `user_profile.json` with the new constraint.
    2. Regenerate the recommendation using the updated "Investor Profile."
    3. Log the "Reasoning Shift" in the Analyst Notebook to show how it pivoted based on user input.

## Technical Requirements
- Use **Modular OOP** for the frontend-backend separation.
- Implement **State Management** so that the history sidebar updates whenever a new recommendation is generated.
- Ensure the UI layout is 1280x720 optimized for presentation slides.

## Trigger Phrase
"Moneypenny, build the system."