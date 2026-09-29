# --------------- IMPORTS ---------------

import json

import yaml
import uuid
from agent.llm import chat
from agent.tools import read_text_file, list_directory, file_info, tools
from agent.memory import process_memory_chunk, extract_memory_chunks, save_message, search_similar, init_db




available_tools = {
    "read_text_file": read_text_file,
    "list_directory": list_directory,
    "file_info": file_info
}

# --------------- LOAD CONFIG ---------------
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

# generate a unique session ID for this chat session
session_id = str(uuid.uuid4())

# update the model in the chat function based on the config file
messages = [ {"role": "system", "content": config["system_prompt"]} ]

while True:
    user_input = input("User: ")
    if user_input.lower() in ["/bye", "bye", "exit"]:
        print("AI: Goodbye! Chat about to close!")
        chunks = extract_memory_chunks(messages, model=config["memory_model"])
        for chunk in chunks:
            process_memory_chunk(chunk, model=config["memory_model"])
        break
    messages.append({"role": "user", "content": user_input})
    relevant_raw = search_similar(user_input, "messages", top_n=3)
    relevant_curated = search_similar(user_input, "memories", top_n=3)

    raw_context = [content for score, row_id, content in relevant_raw]
    curated_context = [content for score, row_id, content in relevant_curated]

    memory_context = "\n".join(curated_context + raw_context)
    save_message(session_id, "user", user_input)

    context_message = {
        "role": "system",
        "content": f"Relevant past context:\n{memory_context}"
    }

    response = chat([context_message] + messages, model=config["model"], tools=tools)


    if response["message"].get("tool_calls"):
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

            messages.append({"role": "tool", "content": result})
            save_message(session_id, "tool", result)

        response = chat(messages, model=config["model"], tools=tools)

    print("AI: " + response["message"]["content"])
    messages.append({"role": "assistant", "content": response["message"]["content"]})
    save_message(session_id, "assistant", response["message"]["content"])


        
   
