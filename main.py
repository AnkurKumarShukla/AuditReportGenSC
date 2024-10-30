import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate

# Load environment variables from a .env file
load_dotenv()

# Define the prompt for the AI model
prompt_text = """
Do not show steps, no salutation—strictly generate the report directly. You are a smart contract auditor. Generate a markdown report explaining every vulnerability in detail and in very simple language.
I have added the audit keyword in this Solidity file to indicate that the following lines of code are vulnerable and need to be fixed. Just make an audit report documentation in the following form: (like a smart contract auditor with an in-depth and detailed explanation of the vulnerability).
I explain the format and what each heading will contain in the report wherever required. Do not write the prompt in the report strictly.
- TITLE: Contain Root Cause + Impact
- Proof of Concept: Contain a function using Foundry that will exploit the specified vulnerability. Provide the Foundry command to run this function once I copy and execute it in Foundry. Provide end-to-end complete code for that exploit with no syntax errors. Add comments to explain the code.
- [[S]-#] means we have to determine the severity of the vulnerability based on Codehawks - How to evaluate a finding severity docs. Replace [S] with High, Medium, or Low based on the severity. For the Proof of Concept, add step-by-step code/commands in Foundry on how to test and prove the finding. Include exact lines of code and Foundry-based commands in(in sub-section under proof of concept) the Proof of Concept section.
- Whenever you reference a variable name or function name, use the format `SmartContractName::variableName`.

Format:
[[S]-#] TITLE
Description:
Impact:
Proof of Concept:
Recommended Mitigation:
"""

def llm_action(solidity_code: str, prompt_text: str) -> str:
    """
    Generates an audit report using the provided Solidity code and prompt text.

    Args:
        solidity_code (str): The Solidity code to be analyzed.
        prompt_text (str): The prompt text for guiding the report generation.

    Returns:
        str: The generated audit report in Markdown format.
    """
    llm = ChatOpenAI(
        model="gpt-4o",  # Ensure this model name is correct
        temperature=0.1,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=os.getenv("Auth"),
    )

    final_input = f"{prompt_text} {solidity_code}"

    # Create a prompt template and format it with the final input
    prompt_template = PromptTemplate.from_template("{final_input}")
    formatted_prompt = prompt_template.format(final_input=final_input)

    # Create a chain with the prompt template and the LLM
    chain = prompt_template | llm

    # Invoke the chain to get the response
    response = chain.invoke({"final_input": final_input})

    return response.content

def report_generator(solidity_code: str) -> str:
    """
    Generates a report based on the provided Solidity code.

    Args:
        solidity_code (str): The Solidity code to be analyzed.

    Returns:
        str: The generated audit report in Markdown format.
    """
    return llm_action(solidity_code, prompt_text)
