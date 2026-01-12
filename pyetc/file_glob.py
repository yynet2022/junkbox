"""指定されたパターンに一致するファイルを検索するモジュール。

このモジュールは、プロジェクトのベースディレクトリ外へのアクセスを制限する
セキュリティチェックを行いながら、glob パターンを使用してファイルを検索します。
また、.gitignore に記述されたパターンを考慮して、検索結果から除外します。
"""

import glob
import logging
import os
from fnmatch import fnmatch

from config import Config
from get_gitignore import get_gitignore

logger = logging.getLogger(__name__)


class AccessDenied(Exception):
    """プロジェクトのベースディレクトリ外のパスが指定された場合に送出される例外。"""

    pass


class FileGlobTool:
    """glob パターンを使用してファイルを検索するツールクラス。

    Attributes:
        config (Config): プロジェクト設定を保持するオブジェクト。
    """

    def __init__(self, config: Config):
        """FileGlobTool を初期化します。

        Args:
            config (Config): プロジェクト設定を保持するオブジェクト。
        """
        self.config = config

    def validate(self, root_path: str, pattern: str) -> None:
        """指定されたパスとパターンが安全であることを検証します。

        プロジェクトのベースディレクトリ外にあるファイルを指定しようとした場合、
        AccessDenied 例外を発生させます。

        Args:
            root_path (str): 検索を開始するルートディレクトリ。
            pattern (str): 検索に使用する glob パターン。

        Raises:
            AccessDenied: 指定されたパスがプロジェクトのベースディレクトリ外にある場合、
                またはパスが無効な場合に発生します。
        """
        target_file = os.path.join(root_path, pattern)
        resolved_path = os.path.abspath(target_file)
        project_dir = self.config.project_dir
        try:
            # commonpath は共通の親ディレクトリを返します
            if os.path.commonpath([project_dir, resolved_path]) != project_dir:
                msg = f"{target_file} is outside the project."
                logger.error(msg)
                raise AccessDenied(msg)
        except ValueError:
            # ドライブ文字が異なる場合など
            msg = f"{target_file} is invalid."
            logger.error(msg)
            raise AccessDenied(msg)

    def execute(self, pattern: str, root_path: str = "."):
        """指定されたルートディレクトリ以下で、パターンに一致するファイルを検索します。

        検索結果からは、.gitignore に一致するファイルやディレクトリが除外されます。
        すべてのパスは root_path からの相対パスとして返されます。

        Args:
            pattern (str): 検索に使用する glob パターン（例: "*.py", "src/**/*.ts"）。
            root_path (str): 検索を開始するベースディレクトリ。デフォルトはカレントディレクトリ。

        Returns:
            list[str]: 見つかったファイルパス（相対パス）のリスト。
        """
        self.validate(root_path, pattern)

        ignore_pattern = get_gitignore(root_path)
        logger.debug(f"ignore_pattern is {sorted(ignore_pattern)}")

        files = []
        for file in glob.glob(
            os.path.join(root_path, "**", pattern), recursive=True
        ):
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
    print(FileGlobTool(Config()).execute("*.py", "a/b/c/../../.."))
