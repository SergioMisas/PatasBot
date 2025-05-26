import os


def get_path(relative_path: str) -> str:
    """
    Constructs an absolute path from a relative path.

    Args:
        relative_path (str): The relative path to the file or directory.

    Returns:
        str: The absolute path to the file or directory.
    """
    current_dir: str = os.path.dirname(os.path.abspath(__file__))
    project_root: str = os.path.join(current_dir, "..")
    return os.path.join(project_root, relative_path)


def read_textfile(relative_path: str) -> str:
    """
    Reads the content of a text file.

    Args:
        relative_path (str): The relative path to the text file.

    Returns:
        str: The content of the text file, or an empty string if the file does not exist or cannot be read.
    """
    path: str = get_path(relative_path)

    try:
        with open(path, "r", encoding="utf-8") as file:
            return file.read()
    except OSError:
        return ""


def write_textfile(relative_path: str, new_text: str) -> bool:
    """
    Writes new text to a text file.
    If the file does not exist, it will be created.

    Args:
        relative_path (str): The relative path to the text file.
        new_text (str): The text to write to the file.

    Returns:
        bool: True if the text was successfully written, False otherwise.
    """
    path: str = get_path(relative_path)

    try:
        with open(path, "w", encoding="utf-8") as file:
            file.write(new_text)
        return True
    except OSError:
        return False
