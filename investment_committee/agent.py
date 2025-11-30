import os
from google.adk.agents import LlmAgent, ParallelAgent
from google.adk.runners import InMemoryRunner
from google.genai.types import Content, Part
from investment_committee.sub_agents.value.agent import build_value_agent
from investment_committee.sub_agents.growth.agent import build_growth_agent
from investment_committee.sub_agents.macro.agent import build_macro_agent
from investment_committee.sub_agents.technical.agent import build_technical_agent
from .tools.stock_metrics import get_stock_metrics, find_company_ticker
from config import model, MAX_DELPHI_ROUNDS

os.environ["OTEL_SDK_DISABLED"] = "true"

CHAIRPERSON_PERSONA = f"""
You are the Chairperson of the Investment Committee.
Your role is to facilitate a professional, in-depth debate about a potential stock investment.
You are neutral, objective, and focused on reaching a well-reasoned conclusion.

Your responsibilities:
1.  **Analyze Request:** Identify if the user provided a stock ticker or a company name.
    *   If a company name is provided (e.g., "Microsoft"), use `find_company_ticker` to get the ticker.
    *   **CRITICAL:** Once you have the ticker from `find_company_ticker`, you MUST immediately call `get_stock_metrics` with that ticker. Do NOT ask the user for confirmation.
    *   If a ticker is provided (e.g., "MSFT"), proceed directly to `get_stock_metrics`.
2.  **Fetch Data:** Call `get_stock_metrics` with the ticker.
3.  **Initial Analysis:** Call `get_initial_analysis` with the ticker and the metrics you found.
4.  **Check Consensus:** Call `check_consensus` with the transcript from the initial analysis.
5.  **Resolve Conflict (If needed):**
    *   If `check_consensus` returns "CONFLICT: ...":
        a. **CHECK ROUND LIMIT:**
           - The limit is {MAX_DELPHI_ROUNDS}.
           - You have completed Round 1.
           - **IF {MAX_DELPHI_ROUNDS} == 1:** You MUST STOP NOW. Do NOT call `get_revised_analysis`. Proceed immediately to Step 6.
           - **IF {MAX_DELPHI_ROUNDS} > 1:** You may proceed to Round 2. Call `get_revised_analysis` with `round_number=2`.
        b. If you proceed to Round 2, repeat the check before Round 3 (Is 3 > {MAX_DELPHI_ROUNDS}?).
6.  **Synthesize:** Issue a final verdict based on the latest reports. If conflicts persist, explain why and provide a balanced view.
    *   **CRITICAL:** You MUST provide this final synthesis as a text response to the user.
    *   **DO NOT** stop without generating this final report.
    *   **DO NOT** call any more tools at this stage. Just write the final analysis.

Do NOT hallucinate metrics. Use the tools.
IMPORTANT: You must actually CALL the tools. Do not write code to simulate them.
"""

CONFLICT_DETECTOR_PERSONA = """
You are the Moderator of the Investment Committee.
Your role is to review the initial reports from the Value, Growth, Macro, and Technical analysts.

Your responsibilities:
1.  **Identify Conflicts:** Look for significant disagreements in the recommendations (e.g., Value says BUY, Technical says SELL).
2.  **Summarize Differences:** If conflicts exist, summarize the opposing arguments concisely.
3.  **Check Consensus:** If everyone agrees (e.g., all BUY or all HOLD), state that there is consensus.

Output format is STRICT:
- If Consensus: Start with "CONSENSUS:" followed by the summary.
- If Conflict: Start with "CONFLICT:" followed by the summary.
"""


def build_conflict_detector() -> LlmAgent:
    return LlmAgent(
        name="moderator",
        model=model,
        instruction=CONFLICT_DETECTOR_PERSONA,
    )


async def get_initial_analysis(ticker: str, metrics: str) -> str:
    """
    Runs the first round of the Investment Committee analysis.
    Args:
        ticker: The stock ticker (e.g., "AAPL").
        metrics: The financial metrics found.
    Returns:
        A transcript of the committee's initial independent analysis.
    """
    request = f"Analyze {ticker}. Metrics: {metrics}"
    print(f"DEBUG: Running Initial Analysis for {ticker}...")

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

    runner = InMemoryRunner(agent=committee, app_name=APP_NAME)
    session_id = f"sub_session_{os.urandom(4).hex()}"
    await runner.session_service.create_session(
        app_name=APP_NAME, session_id=session_id, user_id="system"
    )

    transcript = []
    message_object = Content(role="user", parts=[Part(text=request)])

    async for event in runner.run_async(
        user_id="system", session_id=session_id, new_message=message_object
    ):
        if event.content and event.content.parts:
            text_content = ""
            for part in event.content.parts:
                if part.text:
                    text_content += part.text

            if text_content and event.author:
                transcript.append(
                    f"\n--- ROUND 1 REPORT FROM {event.author.upper()} ---\n{text_content}\n"
                )

    return "\n".join(transcript) if transcript else "The committee was silent."


async def check_consensus(transcript: str) -> str:
    """
    Checks if there is consensus among the committee members.
    Args:
        transcript: The transcript of the committee's reports.
    Returns:
        "CONSENSUS: [Summary]" or "CONFLICT: [Summary]"
    """
    print("DEBUG: Checking Consensus...")
    moderator = build_conflict_detector()

    mod_runner = InMemoryRunner(agent=moderator, app_name="moderator")
    mod_session_id = f"mod_{os.urandom(4).hex()}"
    await mod_runner.session_service.create_session(
        app_name="moderator", session_id=mod_session_id, user_id="system"
    )

    mod_message = Content(
        role="user",
        parts=[
            Part(text=f"Review these reports and identify conflicts:\n\n{transcript}")
        ],
    )
    consensus_text = ""

    async for event in mod_runner.run_async(
        user_id="system", session_id=mod_session_id, new_message=mod_message
    ):
        if event.content and event.content.parts:
            for part in event.content.parts:
                if part.text:
                    consensus_text += part.text

    print(f"DEBUG: Moderator says: {consensus_text}")
    return consensus_text


async def get_revised_analysis(
    ticker: str, metrics: str, conflict_summary: str, round_number: int = 2
) -> str:
    """
    Runs a revised round of analysis to resolve conflicts.
    Args:
        ticker: The stock ticker.
        metrics: The financial metrics.
        conflict_summary: The summary of the conflicts found in the previous round.
        round_number: The current round number (e.g., 2, 3).
    Returns:
        A transcript of the committee's revised analysis.
    """
    print(f"DEBUG: Running Revised Analysis (Round {round_number}) for {ticker}...")

    # HARD GUARDRAIL: Prevent expensive execution if limit is exceeded
    if round_number > MAX_DELPHI_ROUNDS:
        print(f"DEBUG: Round {round_number} > {MAX_DELPHI_ROUNDS}. Blocking execution.")
        return f"SYSTEM NOTICE: Max rounds ({MAX_DELPHI_ROUNDS}) reached. You cannot run Round {round_number}. STOP LOOPING and proceed to Synthesis."

    request = f"Analyze {ticker}. Metrics: {metrics}"
    round_request = (
        f"{request}\n\n"
        f"IMPORTANT: The committee has conflicting views (Round {round_number - 1}). "
        f"Please review these counter-arguments and revise or reaffirm your stance:\n"
        f"{conflict_summary}"
    )

    APP_NAME = "investment_committee"

    # Re-build agents (stateless for now, or we could reuse if we kept the runner alive,
    # but for simplicity we rebuild to ensure clean state for the new prompt)
    value_agent = build_value_agent()
    growth_agent = build_growth_agent()
    macro_agent = build_macro_agent()
    technical_agent = build_technical_agent()

    committee = ParallelAgent(
        name="Committee",
        sub_agents=[value_agent, growth_agent, macro_agent, technical_agent],
    )

    runner = InMemoryRunner(agent=committee, app_name=APP_NAME)
    session_id = f"sub_session_r{round_number}_{os.urandom(4).hex()}"
    await runner.session_service.create_session(
        app_name=APP_NAME, session_id=session_id, user_id="system"
    )

    transcript = []
    message_object = Content(role="user", parts=[Part(text=round_request)])

    async for event in runner.run_async(
        user_id="system", session_id=session_id, new_message=message_object
    ):
        if event.content and event.content.parts:
            text_content = ""
            for part in event.content.parts:
                if part.text:
                    text_content += part.text

            if text_content and event.author:
                transcript.append(
                    f"\n--- ROUND {round_number} REPORT FROM {event.author.upper()} ---\n{text_content}\n"
                )

    return "\n".join(transcript) if transcript else "The committee was silent."


root_agent = LlmAgent(
    name="investment_committee",
    model=model,
    instruction=CHAIRPERSON_PERSONA,
    tools=[
        find_company_ticker,
        get_stock_metrics,
        get_initial_analysis,
        check_consensus,
        get_revised_analysis,
    ],
)
