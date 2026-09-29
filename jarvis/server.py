from fastapi import FastAPI
from pydantic import BaseModel
import yaml
import json
import uuid

from agent.llm import chat
from agent.tools import open_application, read_text_file, list_directory, file_info, tools
from agent.memory import save_message, search_similar, extract_memory_chunks, process_memory_chunk, init_db
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()



app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


available_tools = {
    "read_text_file": read_text_file,
    "list_directory": list_directory,
    "file_info": file_info,
    "open_application": open_application
}

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

messages = [{"role": "system", "content": config["system_prompt"]}]
session_id = str(uuid.uuid4())
init_db()

MAX_MESSAGES_BEFORE_SUMMARY = 20


class ChatRequest(BaseModel):
    message: str

MAX_TOOL_ROUNDS = 5

def run_agent_loop(messages, model):
    for _ in range(MAX_TOOL_ROUNDS):
        response = chat(messages, model=model, tools=tools)

        if not response["message"].get("tool_calls"):
            return response

        for tool_call in response["message"]["tool_calls"]:
            name = tool_call["function"]["name"]
            arguments = tool_call["function"]["arguments"]
            print(f"\n [tool call] {name}({arguments}) \n")
            function_to_call = available_tools[name]

            try:
                result = function_to_call(**arguments)
            except Exception as e:
                result = f"Error: the tool call failed — {str(e)}"

            if not isinstance(result, str):
                result = json.dumps(result)

            print(f"DEBUG: tool result for {name} = {result!r}")   # <-- add this

            messages.append({"role": "tool", "content": result})
            save_message(session_id, "tool", result)

    return response

def summarize_and_reset_session():
    global messages, session_id

    chunks = extract_memory_chunks(messages, model=config["memory_model"])
    for chunk in chunks:
        process_memory_chunk(chunk, model=config["memory_model"])

    messages = [{"role": "system", "content": config["system_prompt"]}]
    session_id = str(uuid.uuid4())


@app.post("/chat")
def chat_endpoint(request: ChatRequest):
    user_input = request.message
    messages.append({"role": "user", "content": user_input})

    relevant_raw = search_similar(user_input, "messages", top_n=3)
    relevant_curated = search_similar(user_input, "memories", top_n=3)
    raw_context = [content for score, row_id, content in relevant_raw]
    curated_context = [content for score, row_id, content in relevant_curated]
    memory_context = "\n".join(curated_context + raw_context)

    context_message = {
        "role": "system",
        "content": f"Relevant past context:\n{memory_context}"
    }

    save_message(session_id, "user", user_input)

    response = run_agent_loop([context_message] + messages, model=config["model"])

    print("AI: " + response["message"]["content"])
    messages.append({"role": "assistant", "content": response["message"]["content"]})
    save_message(session_id, "assistant", response["message"]["content"])

    if len(messages) >= MAX_MESSAGES_BEFORE_SUMMARY:
        summarize_and_reset_session()

    return {"reply": response["message"]["content"]}


@app.post("/end_session")
def end_session():
    summarize_and_reset_session()
    return {"message": "Session ended and memory saved."}