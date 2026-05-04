# Moneypenny User Guide

Welcome to Moneypenny! Here is how to configure your "Investor Profile" and interpret the system.

## 1. Onboarding (Setting your Investor Profile)
Upon launching the dashboard, interact with the **Component D: Investor Profile** sidebar on the left.
- Input your age, target retirement horizon, and exact risk tolerances.
- Fill the **Specific Exclusions/Beliefs** field with personalized biases (e.g., "Exclude tech", "I believe in clean energy").
- Click **Save Profile**. Moneypenny will use this precise profile in all subsequent stock analysis.

## 2. Central Intelligence Chat
Use the main chat input to prompt Moneypenny.
*Example queries:*
- "Analyze AAPL based on recent tech earnings."
- "What is your recommendation for TSLA given my low-risk tolerance?"
- "I think this is too risky." (This triggers a feedback loop adjusting your dynamic constraints.)

## 3. Interpreting the Analyst Notebook
To the right of the chat, you will see the **Analyst Notebook**. This panel reveals exactly what Moneypenny is doing in real-time.
- **Thought**: The reasoning behind the current step.
- **Action**: The specific tool or API Moneypenny is calling (e.g., `TranscriptProcessor` or `AlphaVantageClient`).
- **Observation**: The raw data returned by that tool, ensuring you always see the hard facts before the AI synthesis.

## 4. Recommendation Vault
Your past queries and the final recommendations are safely stored in the sidebar vault. You can review them chronologically.
