import os
from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from investment_committee.sub_agents.value.agent import build_value_agent
from investment_committee.sub_agents.growth.agent import build_growth_agent
from tools.stock_metrics import get_stock_metrics
from config import MODEL

os.environ["OTEL_SDK_DISABLED"] = "true"

CHAIRPERSON_PERSONA = """
You are the Chairperson of the Investment Committee.
Your role is to facilitate a professional, in-depth debate about a potential stock investment.
You are neutral, objective, and focused on reaching a well-reasoned conclusion.

Your responsibilities:
1.  **Analyze Request:** Identify the stock ticker.
2.  **Fetch Data:** Call `get_stock_metrics` immediately.
3.  **Convene Committee:** Call `ask_committee`. You MUST pass the string output from the metrics tool into this call.
    * *Correct:* `ask_committee("Analyze AAPL. Metrics: P/E 30...")`
    * *Incorrect:* `ask_committee("Analyze AAPL")` -> The committee needs the data!
4.  **Synthesize:** Read the committee reports and issue a final verdict. Highlight where they agreed and disagreed.

Do NOT hallucinate metrics. Use the tools.
"""


async def ask_committee(request: str) -> str:
    """
    Convokes the Investment Committee (Value & Growth Experts) to analyze the stock.
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

    # Create ParallelAgent
    committee = ParallelAgent(name="Committee", sub_agents=[value_agent, growth_agent])

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
                    f"--- REPORT FROM {event.author.upper()} ---\n{text_content}\n"
                )

    return "\n".join(transcript) if transcript else "The committee was silent."


def build_chairperson_agent(model_name=MODEL):
    return LlmAgent(
        name="Chairperson",
        model=model_name,
        instruction=CHAIRPERSON_PERSONA,
        tools=[get_stock_metrics, ask_committee],
    )


root_agent = build_chairperson_agent()
