from yardstick_benchmark.model import Node, RemoteAction
from pathlib import Path
import os
import tarfile
from pathlib import Path

def unarchive(src: Path, dest: Path = None):
    """
    Extract all .tar.gz archives in the specified source directory.

    Parameters:
    - src (Path): The path to the directory containing .tar.gz files.
    - dest (Path, optional): The destination directory for extraction.
      Defaults to the current working directory.
    """
    src = Path(src)
    dest = Path(dest) if dest else Path.cwd()

    if not src.is_dir():
        raise FileNotFoundError(f"Source directory {src} does not exist.")

    dest.mkdir(parents=True, exist_ok=True)
    tar_files = src.glob("*.tar.gz")

    for tar_file in tar_files:
        try:
            with tarfile.open(tar_file, "r:gz") as tar:
                if tar_file.suffixes[-2:] == [".tar", ".gz"]:
                    extract_name = tar_file.name.removesuffix(".tar.gz")
                else:
                    extract_name = tar_file.stem
                extract_path = dest / extract_name
                extract_path.mkdir(parents=True, exist_ok=True)
                tar.extractall(path=extract_path)
                print(f"Extracted {tar_file} to {extract_path}")
        except tarfile.TarError as e:
            print(f"Failed to extract {tar_file}: {e}")

def fetch(dest: Path, nodes: list[Node]):
    dest.mkdir(parents=True, exist_ok=True)
    return RemoteAction(
        "fetch",
        nodes,
        Path(__file__).parent / "fetch.yml",
        extravars={"dest": str(dest)},
    ).run()

def clean(nodes: list[Node]):
    return RemoteAction(
        "clean",
        nodes,
        Path(__file__).parent / "clean.yml",
    ).run()
