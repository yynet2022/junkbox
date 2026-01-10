import glob
import os
from get_gitignore import get_gitignore
from fnmatch import fnmatch

def file_glob(pattern: str, root_path: str = "."):
    ignore_pattern = get_gitignore(root_path)
    print("ignore_pattern is", sorted(list(ignore_pattern)))
    for file in glob.glob(os.path.join(root_path, pattern), recursive=True):
        file = os.path.relpath(file, root_path)
        if not file or os.path.isdir(file):
            continue
        a = any(fnmatch(file, p) for p in ignore_pattern)
        print(file, a)

if __name__ == "__main__":
    file_glob("**/*.py", ".")
