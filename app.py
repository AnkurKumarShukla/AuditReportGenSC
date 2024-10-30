import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
from main import report_generator
from pydantic import EmailStr
import requests
from starlette.middleware.cors import CORSMiddleware
# Load environment variables from a .env file
load_dotenv()

app = FastAPI(title="SC report Synthesizer", debug=False, version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Function to read the contents of the uploaded file
def read_sol_file(file: UploadFile) -> str:
    try:
        # Read the contents of the file
        file_content = file.file.read()
        return file_content.decode('utf-8')
    except Exception as e:
        # Handle errors during file reading
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")

# Function to generate the Markdown report
def markdown_report_res(file_content: str) -> str:
    """
    Generates a Markdown report based on the provided file content.

    Args:
        file_content (str): The content of the Solidity file.

    Returns:
        str: The formatted Markdown report.
    """
    llm = ChatOpenAI(
        model="gpt-4o",  # Ensure this model name is correct
        temperature=0.1,
        max_tokens=None,
        timeout=None,
        max_retries=2,
        api_key=os.getenv("Auth"),
    )

    report_markdown = report_generator(file_content)

    # Define the prompt template
    prompt_template = PromptTemplate.from_template(
        """Format this to audit report documentation . Make heading larger and bold & code block has black background
        {report_markdown}"""
    )

    # Format the prompt with the report markdown
    # formatted_prompt = prompt_template.format(report_markdown=report_markdown)
    print(prompt_template)
    # Create a chain with the prompt and the LLM
    chain = prompt_template | llm

    # Invoke the chain to get the response
    ai_msg = chain.invoke({"report_markdown": report_markdown})

    return ai_msg.content

def check_user_credits(email: str) -> bool:
    url = "https://s3fgwxrjsh.execute-api.eu-central-1.amazonaws.com/production/api/v1/user/credits"
    payload = {"email": email}
    
    try:
        response = requests.post(url, json=payload)
        
        # Check for successful response
        if response.status_code == 200:
            data = response.json()
            # Debugging information
            print(f"API response: {data}")
            return data.get("eligible", False) and data.get("credits", 0) > 0
        
        # Debugging information for unsuccessful responses
        print(f"Unexpected status code: {response.status_code}")
        print(f"Response content: {response.text}")
        raise HTTPException(status_code=500, detail="Error checking user credits")
    
    except requests.RequestException as e:
        # Handle request errors
        print(f"Request error: {e}")
        raise HTTPException(status_code=500, detail="Error checking user credits")

@app.post("/hello")
def hello(email: EmailStr):
    is_eligible = check_user_credits(email)
    print(is_eligible)
    return {"hello server": is_eligible}




@app.post("/generate_markdown")
def generate_markdown(email: EmailStr, file: UploadFile = File(...)):
    try:
        # Check if the user is eligible and has sufficient credits
        is_eligible = check_user_credits(email)
        print(is_eligible)
        if not is_eligible:
            raise HTTPException(status_code=403, detail="User is not eligible or has insufficient credits")
        
        # Read the contents of the uploaded file
        file_content =  read_sol_file(file)

        # Generate the Markdown report
        markdown_content = markdown_report_res(file_content)

        # Print the Markdown content for debugging (optional)
        print(markdown_content)

        # Return the Markdown content as a JSON response
        return {"markdown_report": markdown_content}

    except HTTPException as e:
        raise e
    except Exception as e:
        # Handle any other exceptions and return a 500 error response
        raise HTTPException(status_code=500, detail=str(e))


# To run the FastAPI app, save the script as `app.py` and run:
# uvicorn app:app --reload
