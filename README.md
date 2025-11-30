# investment-committee
An AI tool that simulates an investment committee meeting using Delphi method, which allows you to see the decisions of the comittee, including the risks and rewards in real-time.  
Implementation via with Google ADK.

# Setup
From the project root:
For working with python venv:
```
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

# Usage
```
adk web
```
Write a company name (or a stock ticker) in the prompt box (e.g. "Apple" or "AAPL") and press enter.  
The "chairman" will pass the company analysis to several "analysts" with different perspectives and focus (macro, growth, value, technicals, etc.).   
In the end, the "chairman" will provide a final recommendation based on the analysis of all agents.

Example of the final output of a "discussion" about the "Kinsale Group":
![final_output](/investment_committee/docs/final_output.png)