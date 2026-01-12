import glob
import logging
import os
from fnmatch import fnmatch

from get_gitignore import get_gitignore

logger = logging.getLogger(__name__)


def file_glob(pattern: str, root_path: str = "."):
    ignore_pattern = get_gitignore(root_path)
    logger.debug(f"ignore_pattern is {sorted(ignore_pattern)}")

    files = []
    for file in glob.glob(os.path.join(root_path, pattern), recursive=True):
        file = os.path.relpath(file, root_path)  # 相対パス
        if not file or os.path.isdir(file):
            continue
        if any(fnmatch(file, p) for p in ignore_pattern):
            logger.debug(f"ignore {file}")
            continue
        files.append(file)
    return files


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("get_gitignore").setLevel(logging.INFO)
    print(file_glob("**/*.py"))
