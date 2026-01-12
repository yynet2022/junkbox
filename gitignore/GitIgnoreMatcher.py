import glob
import logging
import os
import pathspec

logger = logging.getLogger(__name__)


class GitIgnoreMatcher:
    def __init__(self, root_path: str = "."):
        self.root_path = os.path.abspath(root_path)
        # Always ignore .git directory
        ignore_lines = [".git/"]

        # Find all .gitignore files
        gitignore_files = glob.glob(
            os.path.join(root_path, "**/.gitignore"), recursive=True
        )

        # Sort by depth so that deeper .gitignore files (processed later)
        # can override (or add to) previous rules.
        # Actually with pathspec, we are building a single list of patterns.
        # The order in the list matters. Later patterns override earlier ones.
        # So we want Root patterns first, then Subdirectory patterns.
        gitignore_files.sort(key=lambda p: len(os.path.normpath(p).split(os.sep)))

        for file_path in gitignore_files:
            # Skip .git directory content
            if ".git" + os.sep in file_path or ".git\\" in file_path:
                continue

            abs_dir = os.path.dirname(os.path.abspath(file_path))
            rel_dir = os.path.relpath(abs_dir, self.root_path)
            if rel_dir == ".":
                rel_dir = ""
            
            # Convert rel_dir to forward slashes for consistency
            rel_dir = rel_dir.replace(os.sep, "/")

            logger.debug(f"Processing '{file_path}' (rel_dir: {rel_dir})")

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as fd:
                    for line in fd:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        
                        # Handle negation
                        is_neg = line.startswith("!")
                        if is_neg:
                            line = line[1:]
                        
                        # Determine if anchored or recursive
                        # Git logic:
                        # - If starts with /, it's anchored to the .gitignore dir.
                        # - If contains / (not at end), it's anchored.
                        # - Otherwise, it's recursive (**/).
                        
                        # Handle trailing slash (directory indicator)
                        is_dir_only = line.endswith("/")
                        stripped_line = line.rstrip("/")
                        
                        has_slash = "/" in stripped_line
                        
                        final_pattern = ""
                        
                        if line.startswith("/"):
                            # Anchored: /foo -> rel_dir/foo
                            if rel_dir:
                                final_pattern = f"{rel_dir}/{line.lstrip('/')}"
                            else:
                                final_pattern = line
                        elif has_slash:
                             # Anchored (implicit): foo/bar -> rel_dir/foo/bar
                            if rel_dir:
                                final_pattern = f"{rel_dir}/{line}"
                            else:
                                final_pattern = line
                        else:
                            # Recursive: *.log -> rel_dir/**/*.log
                            # But be careful: foo -> rel_dir/**/foo
                            if rel_dir:
                                final_pattern = f"{rel_dir}/**/{line}"
                            else:
                                # Root unanchored -> just the line (matches globally)
                                final_pattern = line
                        
                        if is_neg:
                            final_pattern = "!" + final_pattern
                            
                        ignore_lines.append(final_pattern)
                        logger.debug(f"Added pattern: {final_pattern}")

            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")

        self.spec = pathspec.PathSpec.from_lines("gitwildmatch", ignore_lines)

    def _normalize_path(self, path):
        # Convert to relative path from root if absolute
        if os.path.isabs(path):
            path = os.path.relpath(path, self.root_path)
        # Convert to forward slashes
        return path.replace(os.sep, "/")

    def is_match_file(self, file_path):
        rel_path = self._normalize_path(file_path)
        return self.spec.match_file(rel_path)

    def is_match_dir(self, dir_path):
        rel_path = self._normalize_path(dir_path)
        # Append slash to ensure it matches directory patterns (e.g. "tmp/")
        return self.spec.match_file(rel_path.rstrip("/") + "/")


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    # Create a dummy file structure or use current dir
    g = GitIgnoreMatcher()
    for root, dirs, files in os.walk("."):
        # Prune ignored directories
        # Must pass full path relative to root (or absolute)
        # Note: modifying dirs in-place to skip recursion
        dirs[:] = [d for d in dirs if not g.is_match_dir(os.path.join(root, d))]
        
        for file in files:
            f = os.path.join(root, file)
            ignored = g.is_match_file(f)
            print(f"{f} -> Ignored: {ignored}")
