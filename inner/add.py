import shutil

from os.path import abspath, relpath

from pathlib import Path

from typing import Tuple


import common.paths as paths


def get_abs_path(user_input_path: str) -> Path:  # TODO: pathlib.Path has something just for that
    """Returns the absolute path of the user's input path, whether if the user gave an absolute path from the beginning,
    or a path relative to his/her current working directory. 
    Returns the path only if it exists.
    """
    abs_path = Path(abspath(user_input_path))
    if abs_path.exists():
        return abs_path
    raise FileNotFoundError(
        f"The path '{abs_path}' does not exist. Please make sure you're set to the correct working directory."
    )


def add_file(original_filepath, path_from_repo: Path) -> None:
    """Creates the file's empty parent dirs until the repository, starting from staging_area. 
    The file will then be copied. or something.
    """
    dir_hierarchy = paths.staging_area / path_from_repo
    if not dir_hierarchy.exists():
        dir_hierarchy.mkdir(parents=True)
    shutil.copy2(original_filepath, dir_hierarchy)


def add_dir(
    backup_path: Path, rel_from_repo_to_backup: Path
) -> None:  # TODO: Maybe unitable now?
    dir_hierarchy_from_staging_area = paths.staging_area / rel_from_repo_to_backup
    if not dir_hierarchy_from_staging_area.exists():
        dir_hierarchy_from_staging_area.mkdir(parents=True)
    shutil.copytree(backup_path, dir_hierarchy_from_staging_area, dirs_exist_ok=True)


def update_changes_to_be_committed(rel_from_repo_to_backup) -> None:
    with open(paths.changes_to_be_committed, "a") as f:
        f.write(f"{rel_from_repo_to_backup}\n")


def inner_add(backup_path: Path) -> None:
    """Uses the relative path from repository to the backup dir/file, and creates the same hierarchy of empty dirs until the backup.
    All files and folders inside the backup will be created in their original hierarchy.
    Finally, adds the filepath to 'changes_to_be_committed.txt'."""
    rel_from_repo_to_backup = backup_path.relative_to(paths.repo)
    if backup_path.is_file():
        rel_from_repo_to_dir = rel_from_repo_to_backup.parent
        add_file(backup_path, rel_from_repo_to_dir)
    elif backup_path.is_dir():
        add_dir(backup_path, rel_from_repo_to_backup)

    update_changes_to_be_committed(rel_from_repo_to_backup)
