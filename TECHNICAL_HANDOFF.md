# Technical Product Handoff: Moneypenny AI Investment Advisor

This document provides a comprehensive technical and strategic summary of the "Moneypenny" project. It is designed to serve as the technical foundation for formal white papers and executive presentations.

---

## 1. UI/UX Design Rationale

The Moneypenny interface is architected as a **Dual-Stream Financial Dashboard**, diverging from standard "chatbot" patterns to prioritize data persistence and user trust.

### **Cognitive Load & Data Persistence**
*   **Independent Columnar Scrolling:** The interface utilizes a split-column layout where the **Chat Stream** (left) and **Visualization Panel** (right) operate on independent scroll tracks. This ensures that while the user explores deep conversational reasoning, their **Portfolio Snapshot** remains "locked" in view, preventing the cognitive overhead of scrolling back and forth to correlate text with data.
*   **Single-Column Vertical Viz:** To maximize vertical real estate, the visualization panel follows a hierarchical vertical flow: *Pie Chart (Macro) → Growth Metrics (Projection) → Nested Product Breakdowns (Granularity).*

### **The Trust-Based "Intake Protocol"**
*   **Mandatory Profiling:** Unlike generic AI, Moneypenny enforces a hard "Intake Protocol." The interface blocks analytical output until six key variables (Age, Capital, Industry, Risk, Retirement, Literacy) are captured. This friction is a deliberate design choice to mirror the professional due diligence of a human wealth manager, establishing a psychological "Fiduciary Baseline."
*   **Visual Transparency:** The use of **nested expanders** for sub-allocations (e.g., clicking "Bonds" to reveal specific ETFs like BND or BNDX) provides a "Glass Box" experience, allowing users to verify the granular components of the AI's abstract recommendations.

---

## 2. High-Level Technology Stack

Moneypenny is built on a modern agentic architecture designed for low-latency reasoning and real-time data grounding.

### **Agent Framework & Core LLM**
*   **Framework:** Built on a **Custom Python Orchestration Engine** (`core/engine.py`). Rather than relying on heavy off-the-shelf frameworks, Moneypenny uses native Python `asyncio` and custom `while` loops to manually manage state transitions and orchestrate the agentic tool-calling ping-pong.
*   **Model:** Powered by **Gemini 2.5 Flash** via the `google.genai` SDK. This model was selected for its high performance-to-latency ratio and its native ability to handle complex tool-calling loops (Function Calling) without the overhead of heavy-weight reasoning models.

### **Model Context Protocol (MCP) Integration**
*   **The Data Bridge:** Moneypenny utilizes the **Model Context Protocol (MCP)** via a custom **FastMCP** server. This architectural choice decouples the LLM from the data source, allowing the agent to interact with live financial APIs (YFinance) as if they were internal functions.
*   **Deployment Versatility:** The architecture supports both local MCP execution and remote execution via **SSE (Server-Sent Events)**, enabling the data-fetching layer to live on secured, high-uptime hardware (e.g., a Raspberry Pi gateway) separate from the frontend.

### **Tool Ecosystem**
*   **`get_stock_data`:** Retrieves real-time price action, day highs/lows, and business summaries.
*   **`get_company_news`:** Fetches recent market sentiment and headlines.
*   **`PortfolioDatabase`:** A persistent storage layer (SQLite-backed) that manages user profiles and historical recommendation traces, ensuring context persistence across sessions.

---

## 3. The Agentic Loop & Reasoning Architecture

Moneypenny follows a rigorous, multi-stage reasoning loop that prioritizes strategic integrity over short-term "noise."

### **Stage 1: The Intent Router**
Every user input is first processed by an **Intent Router**. This stage performs two critical tasks:
1.  **Metadata Extraction:** Identifying if the user has provided new profile information (e.g., "I just turned 31") and updating the database silently.
2.  **Logic Gating:** Determining if the request is "Conversational" (Chat) or "Analytical" (Analyze). If analysis is requested but the Intake Protocol is incomplete, the router intercepts the request and re-routes to a conversational interrogation mode.

### **Stage 2: The Synthesis Agent (The Analytical Phase)**
Once gated, the Synthesis Agent takes over with a specific system instruction to apply **Modern Portfolio Theory (MPT)**. The reasoning follows a "Macro-to-Micro" path:
*   **Baseline Strategy:** LLM calculates the ideal asset allocation (Equities vs. Bonds vs. Cash) based on the user's age and risk tolerance.
*   **The Reasoning Loop:** The agent identifies gaps in its current knowledge (e.g., "I need the latest P/E ratio for VTI") and triggers a dynamic tool-calling loop. A custom Python `while` loop intercepts the LLM's `function_calls`, executes the requested external tools via the MCP server, and feeds the real-world observations back into the context window. This loop repeats until the LLM has sufficient data to synthesize a final answer.

### **Stage 3: The Tactical Overlay**
The core innovation of Moneypenny is the **Tactical Overlay**. The agent is instructed to:
*   **Fetch Live Signals:** Query recent news and price volatility.
*   **Synthesize Context:** If a user is bullish on a sector, the agent evaluates that sentiment against live market data. 
*   **Decision Logic:** The agent calculates whether current market events justify a "Tactical Tilt" (a temporary deviation) from the strategic baseline. For example, it may recommend increasing a cash position if news indicates high imminent volatility, while maintaining the long-term goal of 80% equity exposure.

### **Stage 4: Structured Output Synthesis**
The final step is the generation of a rigid JSON object. This ensures that the frontend can reliably render complex financial metrics, pie charts, and projections without the risk of markdown "hallucinations" or formatting errors.
