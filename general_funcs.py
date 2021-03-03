from pathlib import Path

from typing import List, Set

import paths

import random

import os

import shutil

import re

from filecmp import cmp


from exceptions import CommitIdError



# Paths:

def get_image_dir(commit_id: str) -> Path:
    return paths.images / commit_id


def get_all_filepaths(p: Path) -> Set[Path]:
    """Get the relative path of all files, starting from the repository.
    The relative path should be identical within the repo, staging_area, and the committed folder.
    """
    all_files = []
    for root, _, files in os.walk(p):
        rel_path = os.path.relpath(root, p)
        if not rel_path.startswith(".wit"):  # Probably not the best way
            for f in files:
                all_files.append(Path(rel_path) / f)
    return set(all_files)


def get_image_data(user_input: str):
    """Returns the path to the image dir based on the user input (branch or commit id).
    If the dir does not exist, it means that the user's input is problematic, and a CommitIdError is thrown.
    """
    commit_id = resolve_commit_id(user_input)
    dir_path = get_image_dir(commit_id)

    if not dir_path.exists():
        raise CommitIdError(f"'{commit_id}' is not a branch name, nor a commit id.")

    return commit_id, dir_path



# Commit Id:

def generate_commit_id(id_length=40) -> str:
    """Creates a random string using 0-9a-f, of a certain length."""
    chars = "1234567890abcdef"
    return "".join(random.choice(chars) for _ in range(id_length))


def resolve_commit_id(user_input: str) -> str:
    """Returns a commit id, whether if the param passed to checkout() was a branch name or the commit id itself."""
    branch_commit_id = get_commit_id_of_branch(user_input)
    return branch_commit_id if branch_commit_id else user_input


def get_head_id() -> str:
    """Gets the wanted info, by index. HEAD=0, master=1, branch names will start from 2."""
    with open(paths.references, "r") as f:
        lines = f.readlines()
    return lines[0].split("=")[1].strip()


def get_parent():  # Type annotations?
    return get_head_id() if paths.references.exists() else None



# Files:

def copy_changed_files(
    path_from: Path, path_to: Path, changed_files: list, replace=False
) -> None:
    """Given paths to two dirs and a list of files who've been changed, replaces the files from dir1 with their version from dir2.
    When called from `checkout()`, replaces all of the committed files in the repository with their version in the specified commit id (untracked files remain unchanged).
    When called from `merge()`, replaces or adds files in staging_area with files that were either changed or added since the common base dir until the user input dir.
    Doesn't support moving, renaming or deleting files, yet."""
    for relpath_to_file in changed_files:
        abs_path_to_be_replaced = path_to / relpath_to_file
        abs_path_to_be_copied = path_from / relpath_to_file
        # Getting the relative path first is important, to not get any `.wit` files. I think.
        if replace:
            abs_path_to_be_replaced.unlink()  # originally os.remove
        shutil.copy2(abs_path_to_be_copied, abs_path_to_be_replaced)


def get_files_with_different_content(
    path_to_dir1: Path, path_to_dir2: Path, mutual_files: Set[Path]
) -> list:
    """Joins the relative path of each file and compares its content. Returns a list of filepaths with different content.
    Mutual files must be mutual to both dirs.
    When called through `status()`, gets all relative paths to files from the repository and from staging area, thus returning changes not staged for commit.
    When called through `merge()`, gets all relative paths to files from the branch or commit id the user has entered, and the first mutual parent of the latter and of HEAD."""
    files_with_different_content = []
    for relpath in mutual_files:
        relpath = re.sub(r"^\.\\", "", str(relpath))
        # this is bad, m'kay? but I don't remember what we said about it
        first_dir_path = path_to_dir1 / relpath
        second_dir_path = path_to_dir2 / relpath
        if not cmp(first_dir_path, second_dir_path):
            files_with_different_content.append(relpath)
    return files_with_different_content



# Branches:

def get_active_branch_name() -> str:
    """Returns the content of `activated.txt`."""
    with open(paths.active_branch, "r") as f:
        active_branch_name = f.read()
    return active_branch_name


def get_branch_index(references_content: List[str], branch_name="") -> int:
    """This function is pretty weird, but it unites two actions, in order to not open the file and go through the list twice.
    Given a branch name (taken from `activated.txt`), returns it's line index on references.txt, and wether it has the same commit_id as HEAD.
    """
    branch_name = branch_name if branch_name else get_active_branch_name()
    # Originally, `get_active_branch_name()` was the default parameter.
    # However, it raised an error during the `init()` method:
    # When a func is given as a default param, an error is raised if it may not work.
    # The `paths` module does not generate the active_branch attr for the init command,
    # And therefore the function crashed and an error was raised.

    if not branch_name:
        return -1

    for i, line in enumerate(references_content):
        name = line.strip().split("=")[0]
        if name == branch_name:
            return i


def is_branch_id_equal_to_head_id(
    references_content: List[str], branch_index: int
) -> bool:
    if branch_index == -1:
        return False

    branch_id = references_content[branch_index].split("=")[1].strip()
    head_id = references_content[0].split("=")[1].strip()  # is there a better way?
    return head_id == branch_id


def get_commit_id_of_branch(user_input: str) -> str:
    """Tries to find the branch name in references.txt.
    If the branch is found, returns the commit_id of the branch;
    else, returns an empty string (may happen if the user used a commit_id as a parameter).
    """
    with open(paths.references, "r") as f:
        lines = f.readlines()

    for line in lines:
        branch_name, _, commit_id = line.partition("=")
        if branch_name == user_input:
            return commit_id.strip()
    return ""



# Update References File:

def handle_references_file(commit_id: str) -> None:
    """Checks is the id of HEAD and the active branch are the same.
    If they aren't, only HEAD's id changes. If they are, they both change.
    """
    if not paths.references.exists():
        lines = f"HEAD={commit_id}\nmaster={commit_id}\n"

    else:
        with open(paths.references, "r") as f:
            lines = f.readlines()

        branch_index = get_branch_index(lines)
        is_branch_equal_to_head = is_branch_id_equal_to_head_id(lines, branch_index)
        lines[0] = f"HEAD={commit_id}\n"  # Change HEAD's value to commit_id

        if is_branch_equal_to_head:
            branch_name = lines[branch_index].split("=")[0]
            lines[branch_index] = f"{branch_name}={commit_id}\n"

    with open(paths.references, "w") as f:
        f.write("".join(lines))

def add_branch_name_to_references(branch_name: str) -> None:
    head = get_head_id()
    with open(paths.references, "a") as f:
        f.write(f"{branch_name}={head}\n")
