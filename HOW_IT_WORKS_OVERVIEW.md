# How Moneypenny Works: A Plain-English Guide

This document explains the inner workings of **Moneypenny**, our AI-powered investment advisor. It is designed to be easy to understand, even if you don't have a background in software engineering.

---

## 1. The Big Picture

At its core, Moneypenny acts like a digital wealth manager. When you ask it a question (e.g., *"Is Apple a good investment for my retirement?"*), it doesn't just guess or rely on old information. Instead, it securely looks up **real-time market data**, reads the latest news, applies professional financial theories, and builds a customized portfolio just for you.

---

## 2. The Core Tools (The "Tech Stack")

Here is a simple breakdown of the software tools that make Moneypenny work:

*   **The Interface (Streamlit):** This is the website or dashboard you actually see and click on. It handles the chat window and draws the interactive pie charts and graphs.
*   **The Brain (Gemini 2.5 Flash):** This is the Artificial Intelligence model developed by Google. It is highly intelligent and understands finance, but out-of-the-box, it only knows historical data. It needs help to see what is happening in the stock market *today*.
*   **The Data Bridge (Model Context Protocol / MCP):** This is a special tool that acts like a secure translator. It allows the AI "Brain" to safely reach out to the real internet and pull live data.
*   **The Glue (Python):** Python is the programming language running behind the scenes, acting like a traffic cop orchestrating all these tools so they talk to each other smoothly.

---

## 3. Where Does the Data Come From?

Moneypenny gets its real-time market data directly from **Yahoo Finance** (using a tool called `yfinance`). 

When the AI needs to investigate a company, it connects to Yahoo Finance and pulls two specific types of data:
1.  **Live Pricing Data:** It looks at the current stock price, the highest and lowest prices of the day, the previous day's closing price, and the general business summary of the company.
2.  **Market Sentiment (News):** It pulls the headlines and links to the 5 most recent news articles published about that specific company.

---

## 4. How Does It Use the Data? (The "Reasoning Loop")

The most impressive part of Moneypenny is how it "thinks." It doesn't just answer instantly; it uses a "Reasoning Loop." Here is what happens step-by-step when you ask it for advice:

**Step 1: The Request**
You ask: *"I have $10,000. Should I invest heavily in Tesla (TSLA)?"*

**Step 2: The AI Pauses**
The AI looks at your question and realizes, *"I know what Tesla is, but I don't know what its stock price is right now, and I don't know if there is any breaking news about them today."* Instead of guessing, the AI pauses its thinking and asks the system for help.

**Step 3: Fetching the Data**
The Python code intercepts the AI's pause and uses the **Data Bridge (MCP)** to connect to Yahoo Finance. It downloads the live Tesla stock price and the latest news articles.

**Step 4: The Analysis**
The system hands that fresh Yahoo Finance data back to the AI. Now, the AI reads the news (e.g., maybe Tesla just announced a huge recall, or maybe they just hit record sales) and looks at the current price. 

**Step 5: The Final Recommendation**
The AI combines this fresh data with your personal profile (your age, how much risk you want to take, etc.) and applies established financial rules (like Modern Portfolio Theory). It then generates a final response, telling the dashboard exactly how to draw your portfolio pie chart (e.g., *"Put 10% in Tesla, but keep 40% in safe bonds because the news is highly volatile today."*).

---

## 5. The User Profile (Memory)

Moneypenny refuses to give generic advice. Before it does any of the steps above, it forces you to fill out a **Profile** (Age, Industry, Retirement Age, Risk Tolerance). 

This data is saved in a lightweight, local database (a JSON file). This means if you close the app and come back tomorrow, Moneypenny still remembers that you are a 30-year-old teacher who hates high-risk investments, and it will automatically filter all of its future advice through that lens.
