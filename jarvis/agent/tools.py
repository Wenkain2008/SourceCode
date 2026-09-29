import os
from datetime import datetime
from pathlib import Path

SANDBOX_DIR = Path("sandbox").resolve()

ALLOWED_APPS = {
    "notepad": "notepad.exe",
    "calculator": "calc.exe",
    "wardogs": "steam://run/1867240",
    "ready or not": "steam://run/1144200",
    "brave": "brave.exe",
    
}

def open_application(app_name):
    if app_name not in ALLOWED_APPS:
        raise ValueError(f"'{app_name}' is not in the list of allowed applications.")

    os.startfile(ALLOWED_APPS[app_name])
    return f"Opened {app_name}."


def read_text_file(path):
    safe_path = resolve_safe_path(path)
    with open(safe_path, "r") as f:
        content = f.read()
    return content


def list_directory(path):
    safe_path = resolve_safe_path(path)
    return "\n".join(os.listdir(safe_path))


def file_info(path):
    safe_path = resolve_safe_path(path)
    stats = os.stat(safe_path)
    size = stats.st_size
    modified = datetime.fromtimestamp(stats.st_mtime)
    return f"Size: {size} bytes, Last modified: {modified}"

def resolve_safe_path(path):
    requested = (SANDBOX_DIR / path).resolve()

    if not requested.is_relative_to(SANDBOX_DIR):
        raise ValueError(f"Access denied: '{path}' is outside the allowed sandbox directory.")

    return requested

tools = [
    {
        "type": "function",
        "function": {
            "name": "read_text_file",
            "description": "Reads and returns the contents of a text file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to read, e.g. 'sandbox/notes.txt'"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "list_directory",
        "description": "Lists the contents of a directory. All paths are relative to the user's private sandbox folder — use '.' for the sandbox root itself, or a subfolder name if one exists. Do not use absolute paths or include 'sandbox' in the path.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path within the sandbox, e.g. '.' for the root, or 'subfolder' for a subfolder. Never an absolute path."
                }
            },
            "required": ["path"]
        }
    }
},
    {
        "type": "function",
        "function": {
            "name": "file_info",
            "description": "Retrieves information about a file at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The file path to get information about, e.g. 'sandbox/notes.txt'"
                    }
                },
                "required": ["path"]
            }
        }
    },
    {
    "type": "function",
    "function": {
        "name": "open_application",
        "description": "Opens an allowed application by its nickname. Only applications in the predefined allowlist can be opened.",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "The nickname of the application to open, e.g. 'notepad' or 'calculator'."
                }
            },
            "required": ["app_name"]
        }
    }
}

]

if __name__ == "__main__":
    print(resolve_safe_path("notes.txt"))
    print(resolve_safe_path("../../../Windows/System32"))