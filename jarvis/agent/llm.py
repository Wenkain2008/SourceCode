# ---------------- imports ----------------
import ollama 

# ---------------- MAIN ----------------

    
def chat(messages, model, tools = None):
    
    response = ollama.chat(model = model, messages = messages, tools = tools)
    return response

def get_embedding(text):
    response = ollama.embed(model="nomic-embed-text", input=text)
    return response["embeddings"][0]