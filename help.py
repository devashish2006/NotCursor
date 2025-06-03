import json
import os
import re
import requests
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables from .env file (make sure GOOGLE_API_KEY is defined)
load_dotenv()

# Configure Gemini LLM with your API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash-001")
chat = model.start_chat(history=[])

# ---------------------------
# Tool Functions
# ---------------------------

def get_weather(city: str):
    """Fetch weather information from wttr.in for a given city."""
    print("🔨 Tool Called: get_weather", city)
    url = f"https://wttr.in/{city}?format=%C+%t"
    response = requests.get(url)
    if response.status_code == 200:
        return f"The weather in {city} is {response.text.strip()}."
    return "Something went wrong while fetching the weather."

def run_command(command: str):
    """Run a shell command and return its output."""
    print("🔨 Tool Called: run_command", command)
    return os.popen(command).read()

def write_file(filename: str, content: str):
    """Write content to a file with the given filename."""
    print(f"🔨 Tool Called: write_file for {filename}")
    with open(filename, "w") as f:
        f.write(content)
    return f"File {filename} updated successfully."

def edit_file_with_gemini(filename: str, error_message: str):
    """Use Gemini LLM to revise file content based on an error message.
       Reads the current file content, provides it and the error to Gemini,
       and writes the returned updated code into the file."""
    print(f"🔨 Tool Called: edit_file_with_gemini for {filename}")
    try:
        with open(filename, "r") as f:
            current_code = f.read()
    except FileNotFoundError:
        current_code = ""

    prompt = f"""You are an AI assistant that revises Python code.
The file name is: {filename}
Current Code:
{current_code}
The file produced an error when executed:
{error_message}
Please provide a corrected version of the code.
Return only the updated code."""
    response = model.generate_content(prompt)
    updated_code = response.text.strip()
    write_file(filename, updated_code)
    return f"File {filename} has been updated based on the error message."

# A common handler for all tools available to the assistant.
def handle_task(tool_name: str, tool_input: str):
    """Dispatch the task to the appropriate tool based on tool_name."""
    available_tools = {
        "get_weather": {
            "fn": get_weather,
            "description": "Takes a city name and returns current weather info."
        },
        "run_command": {
            "fn": run_command,
            "description": "Executes a shell command and returns its output."
        },
        "write_file": {
            "fn": write_file,
            "description": "Writes code to a file. Input format: filename||content."
        },
        "edit_file": {
            "fn": edit_file_with_gemini,
            "description": "Edits the file based on an error message. Input format: filename||error_message."
        }
    }
    if tool_name in available_tools:
        tool_fn = available_tools[tool_name]["fn"]
        # For write_file and edit_file, we expect the input to be split by a special delimiter "||"
        if tool_name in ["write_file", "edit_file"]:
            try:
                filename, param = tool_input.split("||", 1)
            except ValueError:
                return f"Invalid input format for {tool_name}. Expected 'filename||content/error message'."
            return tool_fn(filename.strip(), param.strip())
        else:
            return tool_fn(tool_input)
    else:
        return f"Tool '{tool_name}' not available."

# ---------------------------
# System Prompt for Gemini
# ---------------------------
system_prompt = """
You are an AI Assistant specialized in making code changes.
You operate in the following sequence: start → plan → action → observe → output.
For a given user query and available tools, you must:
1. Start by planning your next step.
2. When ready, output an "action" step specifying a tool to call and its input.
3. Always output your message in strict JSON (one JSON object per message) with the following keys:
    - "step": either "plan", "action", "observe", or "output"
    - "content": a textual explanation (only for plan/observe/output steps)
    - "function": (only for action steps) the name of the tool to invoke.
    - "input": (only for action steps) the input parameter for the function.
Use one step per message and stop only when your output step is generated.
"""

# Send system prompt so Gemini understands the protocol.
chat.send_message(system_prompt)

# ---------------------------
# Utility Function: JSON Extraction
# ---------------------------
def extract_json_objects(text):
    """Extract JSON objects from a text string using regex."""
    json_pattern = r'\{[^{}]+\}'
    try:
        return [json.loads(match) for match in re.findall(json_pattern, text)]
    except json.JSONDecodeError as e:
        print("❌ JSON parsing failed:", e)
        return []

# ---------------------------
# Main Interactive Loop
# ---------------------------
print("Welcome to the AI Coding Assistant. Type your command (e.g., 'build weather app') or 'exit' to quit.")
while True:
    # Get user input from terminal.
    user_query = input("\n> ")
    if user_query.lower().strip() == "exit":
        break

    # Send the user query to Gemini to initiate a plan.
    response = chat.send_message(user_query)

    # Process steps iteratively until an output step is reached.
    while True:
        steps = extract_json_objects(response.text)
        if not steps:
            print("⚠️ No valid JSON step found. Raw response:")
            print(response.text)
            break

        for step in steps:
            step_type = step.get("step")
            print(f"\n🧠 Step: {step_type}")

            if step_type == "plan":
                # For 'plan' steps, simply display the plan.
                print(f"📌 Plan: {step.get('content')}")
                continue

            elif step_type == "action":
                # For an action step, extract the tool name and input.
                tool_name = step.get("function")
                tool_input = step.get("input")
                print(f"⚙️ Action: Calling tool '{tool_name}' with input: {tool_input}")

                # Handle the action using the common task handler.
                tool_output = handle_task(tool_name, tool_input)
                print(f"🔍 Tool Output: {tool_output}")

                # Send the observation back to Gemini.
                observe_msg = {
                    "step": "observe",
                    "content": f"Tool '{tool_name}' returned: {tool_output}"
                }
                response = chat.send_message(json.dumps(observe_msg))
                break  # Wait for the next step from Gemini.

            elif step_type == "observe":
                # For 'observe' steps, display the observation.
                print(f"👁️ Observation: {step.get('content')}")
                continue

            elif step_type == "output":
                # For the final output step, display the final content.
                print(f"🤖 Final Output: {step.get('content')}")
                break

        # If the final step is reached, exit this inner loop.
        if any(s.get("step") == "output" for s in steps):
            break

print("Session ended.")
