import os
import sys
import argparse
import zipfile
import tarfile
import gzip
import bz2
import lzma
import tempfile
from typing import Dict, List, Optional

READ_COMPRESSED_FILES: bool = True
LARGE_SIZE_FILE: int | float = 10  # MB
MAX_LINES_FOR_LARGE_FILE = 1000    # If None, it returns the entire file.
                                   # If it is a number, it returns the same number of lines.
                                   # If 0, large files are skipped.

BLUE = "\033[94m"
YELLOW = "\033[0;33m"
LIGHT_WHITE = "\033[1;37m"
GREEN = "\033[0;32m"
RED = "\033[0;31m"
RESET = "\033[0m"


def inspect_archive(path: str) -> Optional[Dict[str, str]]:
    if zipfile.is_zipfile(path):
        return {"type": "zip"}
    elif tarfile.is_tarfile(path):
        return {"type": "tar"}
    elif path.endswith(".gz"):
        return {"type": "gz"}
    elif path.endswith(".bz2"):
        return {"type": "bz2"}
    elif path.endswith(".xz"):
        return {"type": "xz"}
    else:
        return None


def read_archive(path: str) -> str:
    info = inspect_archive(path)
    if not info:
        return "## Unsupported archive format\n"

    t = info["type"]
    text_parts: List[str] = [f"## Archive content of {path} ({t})"]

    try:
        if t == "zip":
            with zipfile.ZipFile(path, "r") as z:
                for name in z.namelist():
                    try:
                        with z.open(name) as f:
                            content = f.read().decode(errors="ignore")
                        with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
                            tmp.write(content)
                            tmp.flush()
                            label = f"{path} → {name}"
                            text_parts.append(f"\n## {label}\n{read_file(tmp.name)}\n")
                    except Exception:
                        text_parts.append(f"\n## {path} → {name}\n[Unreadable file]\n")

        elif t == "tar":
            with tarfile.open(path, "r:*") as tfile:
                for member in tfile.getmembers():
                    if member.isfile():
                        f = tfile.extractfile(member)
                        if f:
                            content = f.read().decode(errors="ignore")
                            with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
                                tmp.write(content)
                                tmp.flush()
                                label = f"{path} → {member.name}"
                                text_parts.append(
                                    f"\n## {label}\n{read_file(tmp.name)}\n"
                                )

        elif t in ("gz", "bz2", "xz"):
            opener = {"gz": gzip.open, "bz2": bz2.open, "xz": lzma.open}[t]
            with opener(path, "rt", errors="ignore") as f:
                content = f.read()
            with tempfile.NamedTemporaryFile("w+", delete=False) as tmp:
                tmp.write(content)
                tmp.flush()
                label = f"{path} (decompressed)"
                text_parts.append(f"\n## {label}\n{read_file(tmp.name)}\n")

    except Exception as e:
        text_parts.append(f"[Error reading archive: {e}]")

    return "\n".join(text_parts)


def count_lines_in_file(file_path: str) -> int:
    try:
        with open(file_path, "r") as file:
            return sum(1 for _ in file)
    except UnicodeDecodeError:
        return 0


def paths_as_tree(paths: List[str]) -> str:
    tree: Dict[str, Dict] = {}
    for path in paths:
        parts = path.strip("/").split("/")
        current = tree
        for part in parts:
            current = current.setdefault(part, {})

    dirs_count = 0
    files_count = 0
    output_lines: List[str] = []

    def _print_tree(d: Dict[str, Dict], prefix: str = "") -> List[str]:
        nonlocal dirs_count, files_count
        lines: List[str] = []
        items = sorted(d.items(), key=lambda kv: kv[0])
        for i, (name, subtree) in enumerate(items):
            connector = "└── " if i == len(items) - 1 else "├── "
            is_dir = bool(subtree)
            if is_dir:
                lines.append(prefix + connector + name + "/")
                dirs_count += 1
            else:
                lines.append(prefix + connector + name)
                files_count += 1
            extension = "    " if i == len(items) - 1 else "│   "
            lines.extend(_print_tree(subtree, prefix + extension))
        return lines

    output_lines.append(". Files that were selected:\n|")
    output_lines.extend(_print_tree(tree))
    output_lines.append(f"\n{dirs_count} directories, {files_count} files")

    return "\n".join(output_lines)


def file_is_large(file_path: str, threshold_mb: int | float = 1) -> bool:
    if os.path.exists(file_path):
        file_size = os.path.getsize(file_path)
        if file_size > threshold_mb * 1024 * 1024:
            return True
    return False


def read_file(file_path: str, line_by_line: bool = False) -> str:
    lines: List[str] = []

    def read_line_by_line() -> str:
        with open(file_path, "r") as file:
            for line in file:
                lines.append(line.strip())
            return "\n".join(lines)

    def read_all() -> str:
        with open(file_path, "r") as file:
            return file.read()

    def read_n_lines_from_file(n: int) -> str:
        with open(file_path, "r") as file:
            for _ in range(n):
                line = file.readline()
                if not line:
                    break
                lines.append(line.strip())
        return "\n".join(lines) + f"\n...\nThere are only {n} lines of the file."

    if file_is_large(file_path, LARGE_SIZE_FILE):
        if MAX_LINES_FOR_LARGE_FILE == 0:
            return "The file could not be read.\n"
        elif isinstance(MAX_LINES_FOR_LARGE_FILE, int) and MAX_LINES_FOR_LARGE_FILE > 0:
            return read_n_lines_from_file(MAX_LINES_FOR_LARGE_FILE)
        elif MAX_LINES_FOR_LARGE_FILE is None:
            return read_line_by_line()
        else:
            return f"The file was skipped. The file was larger than {LARGE_SIZE_FILE}MB and it was not specified how many lines to read from it."

    try:
        if line_by_line:
            return read_line_by_line()
        else:
            return read_all()
    except UnicodeDecodeError:
        return "Not a text file"


def make_text_from_files(files: List[str], description: Optional[str] = None) -> str:
    text = ""
    tree = paths_as_tree(files)
    text += "Project structure\n\n" + tree + "\n\n---\n\n"

    for file in files:
        content_raw = read_file(file)

        # If it's not a text file, try handling as an archive (if enabled)
        if content_raw == "Not a text file":
            archive_info = inspect_archive(file)
            if archive_info:
                if READ_COMPRESSED_FILES:
                    file_content = f"\n```\n{read_archive(file)}\n```\n"
                else:
                    file_content = "`Archive skipped`\n"
            else:
                file_content = "\n```\nNot a text file\n```\n"
        else:
            file_content = f"\n```\n{content_raw}\n```\n"

        text += f"{file}\n{file_content}---\n\n"

    if description:
        text += f"Description\n\n{description}\n"

    return text


def ignores_apply(ignores: List[str], targets: List[str]) -> List[str]:
    return [t for t in targets if not any(ex in t for ex in ignores)]


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge all files into .txt")
    parser.add_argument("dirname", help="Input directory")
    parser.add_argument("file", help="Output file.")
    parser.add_argument("-i", "--ignore", help="Files and directories that are ignored..")
    parser.add_argument("-d", "--description", help="Description at the end of the file")
    args = parser.parse_args()

    file_list: List[str] = []
    script_name = os.path.basename(str(sys.argv[0]))

    for root, dirs, files in os.walk(args.dirname):
        for file in files:
            if script_name != file:
                file_list.append(os.path.join(root, file))

    if args.ignore:
        filtered_files = ignores_apply(args.ignore.split(","), file_list)
    else:
        filtered_files = file_list.copy()

    text = make_text_from_files(
        filtered_files, args.description if args.description else None
    )

    with open(args.file, "w") as f:
        f.write(text)
    print(f"{GREEN}+{RESET} It was written on {LIGHT_WHITE}{args.file}{RESET}.")

    print(paths_as_tree(filtered_files))


if __name__ == "__main__":
    main()