import os
import sys
import logging
import json
import asyncio
import threading
from typing import Dict, Any, Tuple
from google import genai
from google.genai import types

from tools.transcript_processor import TranscriptProcessor
from tools.portfolio_database import PortfolioDatabase

from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

class Engine:
    def __init__(self):
        self.tp_client = TranscriptProcessor()
        self.db = PortfolioDatabase()

        # --- Persistent background event loop ---
        # A single loop running in its own daemon thread is the only safe way
        # to call asyncio.run() from Streamlit's multi-threaded context without
        # triggering anyio TaskGroup teardown races (MCP 1.27 / Python 3.13).
        self._loop = asyncio.new_event_loop()
        self._loop_thread = threading.Thread(
            target=self._loop.run_forever, daemon=True, name="mcp-event-loop"
        )
        self._loop_thread.start()
        
        self.base_prompt = ""
        prompt_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "moneypenny_prompt.md")
        try:
            with open(prompt_path, "r") as f:
                self.base_prompt = f.read()
        except Exception as e:
            logging.warning(f"Could not load moneypenny_prompt.md: {e}")

        try:
            self.client = genai.Client()
        except Exception as e:
            logging.warning(f"Could not initialize genai client, using mock: {e}")
            self.client = None
            
    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Robustly extracts JSON from a string that might contain markdown fences or filler text."""
        import re
        # Find the first '{' and the last '}'
        match = re.search(r'(\{.*\})', text, re.DOTALL)
        if match:
            json_str = match.group(1)
            try:
                # Handle common escaped character issues if they exist
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
        
        # Fallback to the original text if no {} found or parsing failed
        try:
            return json.loads(text.strip())
        except:
            # If everything fails, return a safe dict with the text
            return {"response": text, "recommendation_markdown": text, "tldr": ""}

    def _map_mcp_to_gemini(self, mcp_tools) -> list[types.Tool]:
        gemini_tools = []
        for t in mcp_tools.tools:
            props = {}
            required = []
            
            if hasattr(t, "inputSchema") and "properties" in t.inputSchema:
                for k, v in t.inputSchema["properties"].items():
                    props[k] = types.Schema(
                        type=types.Type.STRING if v.get("type", "string") == "string" else types.Type.OBJECT,
                        description=v.get("description", "")
                    )
                required = t.inputSchema.get("required", [])
                
            decl = types.FunctionDeclaration(
                name=t.name,
                description=t.description or f"Call MCP tool {t.name}",
                parameters=types.Schema(
                    type=types.Type.OBJECT,
                    properties=props,
                    required=required
                ) if props else None
            )
            gemini_tools.append(types.Tool(function_declarations=[decl]))
        return gemini_tools

    async def synthesize_async(self, user_query: str, ticker: str = "VTI") -> Tuple[str, list]:
        trace = []
        profile = self.db.load_profile()
        profile_str = json.dumps(profile, indent=2)
        
        trace.append({
            "thought": "I need to configure this action to the User's unique profile.",
            "tool": "PortfolioDatabase.load_profile()",
            "observation": f"Loaded Profile: {profile_str}"
        })

        if not self.client:
            trace.append({
                "thought": "Checking Gemini authorization",
                "tool": "genai.Client()",
                "observation": "Error: Missing GEMINI_API_KEY."
            })
            return "Gemini API Key missing.", trace

        pi_url = os.environ.get("PI_MCP_URL")
        
        try:
            from contextlib import asynccontextmanager
            @asynccontextmanager
            async def get_mcp_streams():
                if pi_url:
                    from mcp.client.sse import sse_client
                    async with sse_client(pi_url) as streams:
                        yield streams
                else:
                    server_path = os.path.join(os.path.dirname(__file__), "..", "tools", "yfinance_mcp.py")
                    # Use 'uv run' if available for speed, but fallback to the current sys.executable for stability on the Pi
                    server_params = StdioServerParameters(command=sys.executable, args=[server_path])
                    async with stdio_client(server_params) as streams:
                        yield streams

            async with get_mcp_streams() as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    mcp_tools = await session.list_tools()
                    
                    gemini_tools = self._map_mcp_to_gemini(mcp_tools)
                    
                    # Instead of pre-fetching, we let the LLM do it.
                    system_instruction = f"""
{self.base_prompt}

[IMPORTANT: You have already introduced yourself to the user previously. DO NOT output a greeting or re-introduce yourself. Start directly with your analysis and recommendations.]

User Profile:
{profile_str}

Use your tools to gather market data, sentiment, news, or statements.
The user is likely focusing on the ticker: {ticker}.
Formulate your query using the YFinance MCP tools to evaluate the user's specific concern.
If the custom local server returns no data, explicitly state so, but provide the closest recommendation possible.

CRITICAL INSTRUCTION: Your final output MUST be a valid JSON object. DO NOT include markdown code blocks (```json) or any other text before or after the JSON.
Use this EXACT JSON structure:
{{
    "tldr": "A 5–7 bullet pithy executive summary (plain markdown, no HTML). Include: 🎯 Action, 📊 Allocation Snapshot, 📈 Key Metric, 🧠 Reasoning, ⚠️ Primary Risk, 📅 Horizon.",
    "recommendation_markdown": "Your detailed stock analysis and action plan in plain markdown. The TL;DR section at the top of this field should mirror the tldr field content. DO NOT use any HTML tags like <span>. Do NOT use the dollar sign symbol ($) for currency, use 'USD' instead to avoid triggering accidental math formatting.",
    "portfolio_weights": {{
        "US Equities": {{"weight": 40, "products": {{"VTI": 25, "VOO": 15}}}},
        "Bonds": {{"weight": 30, "products": {{"BND": 15, "BNDX": 10, "TIP": 5}}}},
        "Cash": {{"weight": 10, "products": {{"VMFXX": 10}}}},
        "International": {{"weight": 20, "products": {{"VXUS": 20}}}}
    }},
    "projected_growth_percent": 8.5, 
    "total_investment": {profile.get("Investment Amount", 10000)}
}}
Each top-level category in portfolio_weights MUST have a "weight" (the total % for that category) and a "products" dict mapping specific ticker symbols or fund names to their individual percentage allocations. The sum of all top-level weights must equal 100. The sum of products within each category must equal that category's weight. Always recommend specific, real, investable products (ETFs, mutual funds, etc.).
"""
                    chat = self.client.chats.create(
                        model="gemini-2.5-flash",
                        config=types.GenerateContentConfig(
                            system_instruction=system_instruction,
                            tools=gemini_tools,
                            temperature=0.2
                        )
                    )
                    
                    trace.append({
                        "thought": f"I am connected to the YFinance Local MCP Server. Executing agent loop for {ticker}.",
                        "tool": "gemini-2.5-flash + local-mcp",
                        "observation": "Initiating tool calling loop."
                    })

                    response = chat.send_message(user_query)
                    
                    # Execute tool calls if Gemini requests them
                    while response.function_calls:
                        tool_responses = []
                        for fc in response.function_calls:
                            trace.append({
                                "thought": f"I need to invoke {fc.name} to fetch data.",
                                "tool": f"MCP: {fc.name}",
                                "observation": f"Args: {fc.args}"
                            })
                            
                            try:
                                mcp_result = await session.call_tool(fc.name, fc.args)
                                # MCP returns Result object holding .content
                                result_text = "\n".join([c.text for c in mcp_result.content if c.type == "text"])
                            except Exception as tool_e:
                                result_text = f"Tool failure: {tool_e}"
                            
                            trace[-1]["observation"] = f"Result (truncated): {result_text[:250]}..."
                            
                            tool_responses.append(
                                types.Part.from_function_response(
                                    name=fc.name,
                                    response={"result": result_text}
                                )
                            )
                        
                        # Send all tool responses back to LLM at once
                        response = chat.send_message(tool_responses)
                    
                    raw_text = response.text.strip()
                    try:
                        recommendation = self._extract_json(raw_text)
                    except Exception as e:
                        logging.error(f"Failed to parse JSON from final synthesis. Error: {e}")
                        logging.error(f"Raw text was:\n{raw_text}")
                        recommendation = {
                            "tldr": "",
                            "recommendation_markdown": raw_text,
                            "portfolio_weights": {
                                "Equities": {"weight": 60, "products": {ticker: 60}},
                                "Bonds": {"weight": 25, "products": {"BND": 15, "BNDX": 10}},
                                "Cash": {"weight": 15, "products": {"VMFXX": 15}}
                            },
                            "projected_growth_percent": 0.0,
                            "total_investment": profile.get("Investment Amount", 10000)
                        }
                        
                    trace.append({
                        "thought": "All LLM tool calls complete. Synthesizing final recommendation as JSON.",
                        "tool": "gemini-2.5-flash",
                        "observation": "Action Plan Generated."
                    })
                    
        except Exception as e:
            import traceback
            traceback.print_exception(e)
            logging.error(f"Local MCP Server connection issue: {e}")
            trace.append({
                "thought": f"The Local YFinance MCP Data Link failed: {str(e)[:50]}",
                "tool": "GEMINI FALLBACK",
                "observation": "Proceeding with semantic inference without real-time data."
            })
            
            fallback_prompt = f"""
{self.base_prompt}

The real-time YFinance MCP link is offline.
User Profile: {profile_str}
Query: "{user_query}"
Ticker: {ticker}

Provide your best recommendation based on your internal knowledge and the user's constraints. 
Start the message by stating clearly that real-time market data is currently unavailable.

CRITICAL INSTRUCTION: Your final output MUST be a valid JSON object. Do not include markdown wrappers.
Use this EXACT JSON structure:
{{
    "tldr": "A 5–7 bullet pithy executive summary.",
    "recommendation_markdown": "Your detailed stock analysis and action plan in plain markdown. DO NOT use any HTML tags like <span>. Do NOT use the dollar sign symbol ($) for currency, use 'USD' instead to avoid triggering accidental math formatting.",
    "portfolio_weights": {{
        "US Equities": {{"weight": 40, "products": {{"{ticker}": 25, "VOO": 15}}}},
        "Bonds": {{"weight": 30, "products": {{"BND": 15, "BNDX": 10, "TIP": 5}}}},
        "Cash": {{"weight": 10, "products": {{"VMFXX": 10}}}},
        "International": {{"weight": 20, "products": {{"VXUS": 20}}}}
    }},
    "projected_growth_percent": 8.5, 
    "total_investment": {profile.get("Investment Amount", 10000)}
}}
Each top-level category must have "weight" and "products". Always recommend specific, real, investable products. Weights must sum to 100.
"""
            if self.client:
                try:
                    fallback_res = self.client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=fallback_prompt,
                        config=types.GenerateContentConfig(response_mime_type="application/json")
                    )
                    recommendation = self._extract_json(fallback_res.text)
                except Exception as llm_e:
                    recommendation = {
                        "tldr": "",
                        "recommendation_markdown": f"Error during fallback generation: {llm_e}",
                        "portfolio_weights": {
                            "Equities": {"weight": 60, "products": {ticker: 60}},
                            "Bonds": {"weight": 25, "products": {"BND": 15, "BNDX": 10}},
                            "Cash": {"weight": 15, "products": {"VMFXX": 15}}
                        },
                        "projected_growth_percent": 0.0,
                        "total_investment": profile.get("Investment Amount", 10000)
                    }
            else:
                recommendation = {
                    "tldr": "",
                    "recommendation_markdown": "MCP Server failed, and Gemini API is unconfigured.",
                    "portfolio_weights": {
                        "Equities": {"weight": 60, "products": {ticker: 60}},
                        "Bonds": {"weight": 25, "products": {"BND": 15, "BNDX": 10}},
                        "Cash": {"weight": 15, "products": {"VMFXX": 15}}
                    },
                    "projected_growth_percent": 0.0,
                    "total_investment": profile.get("Investment Amount", 10000)
                }
        
        except BaseException as root_e:
            # Specifically for TaskGroup unhandled exceptions that derive from BaseException
            logging.error(f"MCP TaskGroup Error: {root_e}")
            trace.append({
                "thought": "Critical failure in the Local Data Agent. Retrying once...",
                "tool": "SYSTEM",
                "observation": "Falling back to generic safe-hold guidance."
            })
            # Return a structured dict so the UI can still render visualizations
            recommendation = {
                "tldr": "",
                "recommendation_markdown": f"⚠️ The local data server experienced a connection error. Please try your query again. (Technical: {str(root_e)[:80]})",
                "portfolio_weights": {
                    "Equities": {"weight": 50, "products": {ticker: 50}},
                    "Bonds": {"weight": 30, "products": {"BND": 15, "BNDX": 10, "TIP": 5}},
                    "Cash": {"weight": 20, "products": {"VMFXX": 20}}
                },
                "projected_growth_percent": 0.0,
                "total_investment": profile.get("Investment Amount", 10000)
            }

        self.db.add_recommendation({
            "ticker": ticker,
            "query": user_query,
            "recommendation": recommendation,
        })

        return recommendation, trace
        
    def process_interaction(self, user_input: str, chat_history: list) -> Tuple[str, list, str]:
        """
        Determines whether the user is chatting/updating their profile or asking for a stock analysis.
        Returns: (response_text, trace, current_ticker)
        """
        profile_str = json.dumps(self.db.load_profile())
        prompt = f"""
{self.base_prompt}

[IMPORTANT: You have already introduced yourself in this conversation. DO NOT output a greeting or re-introduce yourself. Respond directly to the user's latest input.]

Your goal in this specific task is to determine the user's intent to route them properly.
The current user profile is: {profile_str}
The user just said: "{user_input}"

Determine the user's intent and your next action.
CRITICAL RULE: Moneypenny MUST NOT perform any stock analysis until the Investor Profile is completely filled. If the user is asking for an analysis, but the profile is missing ANY of these required fields: "Age", "Investment Amount", "Job", "Risk Tolerance", "Retirement Age", or "Literacy" - you MUST set "intent" to "chat", list the missing fields in "missing_profile_info", and your "response" must politely interrogate the user for the missing data. Do NOT block analysis if only "Bias" is missing.

Output Requirements:
- "intent": either "analyze" or "chat".
- "missing_profile_info": A list of missing required fields, or [] if complete.
- "ticker": The stock ticker if intent is 'analyze', default to "VTI".
- "updated_profile_fields": A dictionary of any newly extracted profile data (e.g. {{"Job": "Software Engineer", "Risk Tolerance": 8, "Retirement Age": 60}}). Be highly effective at pulling these from descriptions.
- "response": Your conversational reply. Politely interrogate for missing fields if intent is chat. NEVER perform stock analysis or provide ticker recommendations in this field; that must be handled by the 'analyze' intent.

Respond STRICTLY in JSON format. DO NOT use markdown code blocks (```json). Match this structure:
{{
    "intent": "chat",
    "missing_profile_info": ["Job", "Retirement Age"],
    "ticker": "VTI",
    "updated_profile_fields": {{}},
    "response": "Could you tell me what industry you work in?"
}}
"""
        try:
            if self.client:
                res = self.client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=types.GenerateContentConfig(response_mime_type="application/json")
                )
                raw_text = res.text.strip()
                parsed_res = self._extract_json(raw_text)
                
                if parsed_res.get("intent") == "analyze" and not parsed_res.get("missing_profile_info"):
                    ticker = parsed_res.get("ticker", "VTI") or "VTI"
                    rec, trace = self.synthesize(user_input, ticker)
                    return rec, trace, ticker
                else:
                    # It's a chat OR they asked for analysis but profile is incomplete/missing info!
                    updates = parsed_res.get("updated_profile_fields", {})
                    response_text = parsed_res.get("response", "Understood. Can you tell me more about your investment goals?")
                    
                    if updates:
                        # Merge updates safely
                        current_profile = self.db.load_profile()
                        for k, v in updates.items():
                            if v is not None:
                                current_profile[k] = v
                        self.db.save_profile(current_profile)
                        
                    return response_text, [], None
            else:
                # Mock fallback
                return "Mock chat fallback triggered. Setup GEMINI_API_KEY.", [], None
        except Exception as e:
            logging.error(f"Error in process_interaction: {e}")
            # Fallback to synthesis routine if JSON fails
            rec, trace = self.synthesize(user_input, "VTI")
            return rec, trace, "VTI"

    def synthesize(self, user_query: str, ticker: str = "VTI") -> Tuple[str, list]:
        """Runs synthesize_async on the persistent background event loop."""
        future = asyncio.run_coroutine_threadsafe(
            self.synthesize_async(user_query, ticker),
            self._loop
        )
        return future.result()  # blocks the calling (Streamlit) thread until done

    def adjust_profile(self, feedback: str, current_ticker: str) -> Tuple[str, list]:
        profile = self.db.load_profile()
        constraints = profile.get("Dynamic Constraints", [])
        constraints.append(f"User Feedback: {feedback}")
        profile["Dynamic Constraints"] = constraints
        self.db.save_profile(profile)
        
        return self.synthesize(user_query="Adjust my plan based on the new constraints.", ticker=current_ticker)
