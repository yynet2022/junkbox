"""File replacement tool implementation.

This module provides functionality to replace exact string occurrences
in a file, strictly adhering to safety mechanisms to prevent
accidental overwrites.
"""

import logging
import os
import sys
from pathlib import Path

from config import Config

logger = logging.getLogger(__name__)


class AccessDenied(Exception):
    """プロジェクトのベースディレクトリ外のパスが指定された場合に送出される例外。"""

    pass


class ReplaceStringInFile:
    def __init__(self, config: Config):
        """FileGlobTool を初期化します。

        Args:
            config (Config): プロジェクト設定を保持するオブジェクト。
        """
        self.config = config

    def validate(self, target_file: str) -> None:
        """指定されたパスが安全であることを検証します。

        プロジェクトのベースディレクトリ外にあるファイルを指定しようとした場合、
        AccessDenied 例外を発生させます。

        Args:
            target_file (str): ファイル名

        Raises:
            AccessDenied: 指定されたファイルパスがプロジェクトのベースディレクトリ外にある場合、またはパスが無効な場合に発生します。
        """
        if not os.path.exists(target_file):
            raise FileNotFoundError(f"'{target_file}' does not exist.")

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

    def execute(
        self,
        file_path: str,
        old_string: str,
        new_string: str,
        expected_replacements: int = 1,
    ) -> None:
        """指定されたファイル内の old_string を new_string に置き換える。

        ファイル修正において「横着」や「手抜き」は一切しないこと。
        このツールを使う時は以下の手順を必ず守ること。

        1. まずは `read_file`: いきなり書き換えることはしない。
           必ず先に read_file でファイルの中身を読んで、前後の行やインデントを
           確認すること。
        2. 正確な `old_string` の作成: 読んだ内容をコピーして、前後の文脈を
           含めた正確な old_string を作ること。
        3. 確認: 意図しない場所まで変わってしまわないか、慎重に確認してから
           実行すること。

        手堅く、確実に作業を進めるための大事なツールである。

        Args:
            file_path: Path to the target file.
            old_string: 元の文字列
              * 置き換えられる前の、元の文字列。
              * (一番大事なポイント) ファイルに書かれてある通り、一言一句、
                スペースや改行、インデントまで完全に一致してないと動かない。
              * 間違いを防ぐために、書き換えたい行の前後3行ほどを含めて指定する
                必要があります。「ここを変えたい」という場所をピンポイントで
                特定するためです。
              * もしこの文字列がファイルの中に複数見つかったり、逆に見つから
                なかったりしたら、エラーになる（expected_replacements を指定
                した場合を除く）。
            new_string: 新しく置き換える文字列。
              * old_string の部分が、この new_string にそっくりそのまま入れ替
                わる。これもエスケープとかせず、書き込みたい内容をそのまま渡す。
            expected_replacements: 書き換えたい箇所の数。デフォルトは1。
              * もしファイルの中に同じ old_string がいくつもあって、それを全部
                まとめて変えたい時に使います。変えたい箇所の数を指定します。
                デフォルトは「1」なので、指定しなかったら1箇所だけ変えます。
        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the occurrence count does not match expected_replacements.
            OSError: If reading or writing fails.
        """
        self.validate(file_path)

        # Read the file content
        # Using utf-8 as default.
        target_path = Path(file_path)
        try:
            content = target_path.read_text(encoding="utf-8")
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to read '{file_path}' as UTF-8: {e}")

        # Validate occurrences
        count = content.count(old_string)

        if count == 0:
            raise ValueError(
                f"{file_path}: "
                "Could not find exact match for 'old_string'."
                " Please verify whitespace, indentation,"
                " and newlines match exactly."
            )

        if count != expected_replacements:
            raise ValueError(
                f"Found {count} occurrence(s) of 'old_string', "
                f"but expected exactly {expected_replacements}."
            )

        # Perform replacement
        new_content = content.replace(old_string, new_string)

        # Write back to file
        target_path.write_text(new_content, encoding="utf-8")
        print(f"Successfully replaced {count} occurrence(s) in '{file_path}'.")


if __name__ == "__main__":
    import tempfile

    with tempfile.NamedTemporaryFile(
        "w", dir=".", delete=False, encoding="utf-8"
    ) as fp:
        fp.write("おはよう\n")
        fp.write("こんにちわ\n")
        fp.write("こんばんわ\n")
        fp.write("こんにちわ\n")
        fp.write("こんばんわ\n")
        fp.close()
        try:
            ReplaceStringInFile(Config()).execute(
                fp.name,
                "こんにちわ",
                "こんにちは",
            )
        except Exception as e:
            print(f"Error: {e.__class__.__name__}: {e}", file=sys.stderr)
        try:
            ReplaceStringInFile(Config()).execute(
                fp.name,
                "こんにちわ",
                "こんにちは",
                2,
            )
        except Exception as e:
            print(f"Error: {e.__class__.__name__}: {e}", file=sys.stderr)
