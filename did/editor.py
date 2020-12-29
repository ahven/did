import os
import shlex
import shutil
import subprocess


def _run(editor_command: str, file: str):
    executable_path = shutil.which(editor_command)
    if executable_path is not None:
        subprocess.call([editor_command, file])
    else:
        subprocess.call(f"{editor_command} {shlex.quote(file)}", shell=True)


def _try_open_editor_from_environment(file: str) -> bool:
    for var in 'VISUAL', 'EDITOR':
        if var in os.environ and os.environ[var] != '':
            _run(os.environ[var], file)
            return True
    return False


def _try_open_popular_editors(file: str) -> bool:
    popular_editors = ["vim", "nano", "pico", "emacs", "vi", "mcedit"]
    for editor in popular_editors:
        if shutil.which(editor) is not None:
            _run(editor, file)
            return True
    return False


def open_editor(file: str) -> bool:
    """Return True if opened, return False if failed"""
    if _try_open_editor_from_environment(file):
        return True

    return _try_open_popular_editors(file)
