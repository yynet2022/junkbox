import glob
import logging
import os

logger = logging.getLogger(__name__)


def get_gitignore(root_path: str = "."):
    ignore_glob = set()
    for file in glob.glob(
        os.path.join(root_path, "**/.gitignore"), recursive=True
    ):
        logger.debug(f"'{file}' found.")
        d = os.path.dirname(file)
        with open(file, "r", encoding="utf-8", errors="ignore") as fd:
            for line in fd:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # ディレクトリ指定 (/) で終わる場合は末尾を /* に変換
                if line.endswith("/"):
                    line += "*"

                # パスを結合してから正規化
                norm_path = os.path.normpath(os.path.join(d, line))
                logger.debug(f"norm; {norm_path}")
                ignore_glob.add(norm_path)

                norm_path = os.path.normpath(os.path.join(d, "*", line))
                logger.debug(f"norm; {norm_path}")
                ignore_glob.add(norm_path)

    return list(ignore_glob)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print(get_gitignore())
