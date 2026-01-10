import glob
import os


def get_gitignore(root_path: str = "."):
    ignore_glob = set()
    for file in glob.glob(
        os.path.join(root_path, "**/.gitignore"), recursive=True
    ):
        d = os.path.dirname(file)
        with open(file, "r", encoding="utf-8") as fd:
            for line in fd:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue

                # ディレクトリ指定 (/) で終わる場合は末尾を /* に変換
                if line.endswith("/"):
                    line += "*"

                # パスを結合してから正規化
                norm_path = os.path.normpath(os.path.join(d, line))
                ignore_glob.add(norm_path)
                norm_path = os.path.normpath(os.path.join(d, "*", line))
                ignore_glob.add(norm_path)

    return list(ignore_glob)


if __name__ == "__main__":
    print(get_gitignore())
