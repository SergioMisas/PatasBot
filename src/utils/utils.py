import os

def get_path(relative_path:str) -> str:
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    project_root: str = os.path.join(current_dir, "..")
    return os.path.join(project_root, relative_path)

def read_textfile(relative_path: str) -> str:
    path: str = get_path(relative_path)
    
    with open(path, 'r', encoding="utf-8") as file:
        try:
            return file.read()
        except (FileNotFoundError, IOError):
            return ""

def write_textfile(relative_path: str, new_text: str) -> bool:
    path: str = get_path(relative_path)
    
    with open(path, 'w', encoding="utf-8") as file:
        try:
            file.write(new_text)
            return True
        except (FileNotFoundError, IOError):
            return False
