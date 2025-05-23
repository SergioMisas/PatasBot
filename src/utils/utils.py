import os


def read_textfile(relative_path: str) -> str:
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    project_root: str = os.path.join(current_dir, "..")
    path: str = os.path.join(project_root, relative_path)
    
    with open(path, 'r', encoding="utf-8") as file:
        try:
            return file.read()
        except (FileNotFoundError, IOError):
            return ""
