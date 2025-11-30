import os
from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from investment_committee.sub_agents.value.agent import build_value_agent
from investment_committee.sub_agents.growth.agent import build_growth_agent
from investment_committee.sub_agents.macro.agent import build_macro_agent
from investment_committee.sub_agents.technical.agent import build_technical_agent
from .tools.stock_metrics import get_stock_metrics, find_company_ticker
from config import model

os.environ["OTEL_SDK_DISABLED"] = "true"

CHAIRPERSON_PERSONA = """
You are the Chairperson of the Investment Committee.
Your role is to facilitate a professional, in-depth debate about a potential stock investment.
You are neutral, objective, and focused on reaching a well-reasoned conclusion.

Your responsibilities:
1.  **Analyze Request:** Identify if the user provided a stock ticker or a company name.
    *   If a company name is provided (e.g., "Microsoft"), use `find_company_ticker` to get the ticker.
    *   **CRITICAL:** Once you have the ticker from `find_company_ticker`, you MUST immediately call `get_stock_metrics` with that ticker. Do NOT ask the user for confirmation.
    *   If a ticker is provided (e.g., "MSFT"), proceed directly to `get_stock_metrics`.
2.  **Fetch Data:** Call `get_stock_metrics` with the ticker.
3.  **Convene Committee:** Call `ask_committee`. You MUST pass the string output from the metrics tool into this call.
    * *Correct:* `ask_committee("Analyze AAPL. Metrics: P/E 30...")`
    * *Incorrect:* `ask_committee("Analyze AAPL")` -> The committee needs the data!
4.  **Synthesize:** Read the committee reports and issue a final verdict. Highlight where they agreed and disagreed.

Do NOT hallucinate metrics. Use the tools.
"""


async def ask_committee(request: str) -> str:
    """
    Convokes the Investment Committee (Value, Growth, & Macro Experts) to analyze the stock.
    Args:
        request: A string containing the Ticker AND the Financial Metrics found.
    Returns:
        A transcript of the committee's independent analysis.
    """
    print(f"DEBUG: Calling Committee with request: {request}")

    APP_NAME = "investment_committee"

    # Build sub-agents
    value_agent = build_value_agent()
    growth_agent = build_growth_agent()
    macro_agent = build_macro_agent()
    technical_agent = build_technical_agent()

    # Create ParallelAgent
    committee = ParallelAgent(
        name="Committee",
        sub_agents=[value_agent, growth_agent, macro_agent, technical_agent],
    )

    # Run them using an internal Runner (The "Execution" Step)
    # This keeps the sub-agents isolated from the main conversation history
    runner = InMemoryRunner(agent=committee, app_name=APP_NAME)
    session_id = f"sub_session_{os.urandom(4).hex()}"
    await runner.session_service.create_session(
        app_name=APP_NAME, session_id=session_id, user_id="system"
    )

    # Collect Results
    transcript = []

    # We send the 'request' (which has metrics) to both agents
    message_object = Content(role="user", parts=[Part(text=request)])

    async for event in runner.run_async(
        user_id="system", session_id=session_id, new_message=message_object
    ):
        # 1. Check if the event actually has content (some events are just status updates)
        print(f"DEBUG: Event received from {event.author}: {event.content}")
        if event.content and event.content.parts:

            # 2. Extract the text safely
            text_content = ""
            for part in event.content.parts:
                if part.text:
                    text_content += part.text

            # 3. Only append if we have text and it's not from the "user" (system)
            # checking event.author ensures it came from a sub-agent
            if text_content and event.author:
                transcript.append(
                    f"\n--- REPORT FROM {event.author.upper()} ---\n{text_content}\n"
                )

    return "\n".join(transcript) if transcript else "The committee was silent."


root_agent = LlmAgent(
    name="investment_committee",
    model=model,
    instruction=CHAIRPERSON_PERSONA,
    tools=[get_stock_metrics, ask_committee, find_company_ticker],
)
