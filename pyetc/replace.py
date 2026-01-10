"""
File replacement tool implementation.

This module provides functionality to replace exact string occurrences in a file,
strictly adhering to safety mechanisms to prevent accidental overwrites.
"""

import argparse
import sys
from pathlib import Path


def replace_string_in_file(
    file_path: str,
    old_string: str,
    new_string: str,
    expected_replacements: int = 1
) -> None:
    """Replaces occurrences of old_string with new_string in the specified file.

    ファイル修正において「横着」や「手抜きはしない」こと。
    このツールを使う時は以下の手順を必ず守ること。

    1. まずは `read_file`: いきなり書き換えることはしない。必ず先に read_file
       でファイルの中身を読んで、前後の行やインデントを確認すること。
    2. 正確な `old_string` の作成:
       読んだ内容をコピーして、前後の文脈を含めた正確な old_string を作ること。
    3. 確認:
       意図しない場所まで変わってしまわないか、慎重に確認してから実行すること。

    手堅く、確実に作業を進めるための大事なツールである。

    Args:
        file_path: Path to the target file.
        old_string: The exact string to look for (including whitespace/newlines).
          * 置き換えられる前の、元の文字列。
          * (一番大事なポイント) ファイルに書かれてある通り、一言一句、
            スペースや改行、インデントまで完全に一致してないと動かない。
          * 間違いを防ぐために、書き換えたい行の前後3行ほどを含めて指定する
            必要があります。「ここを変えたい」という場所をピンポイントで
            特定するためです。
          * もしこの文字列がファイルの中に複数見つかったり、逆に見つからなかっ
            たりしたら、エラーになる（expected_replacements を指定した場合を
            除く）。
        new_string: The string to replace with.
          * 新しく置き換える文字列。
          * old_string の部分が、この new_string にそっくりそのまま入れ替
            わる。これもエスケープとかせず、書き込みたい内容をそのまま渡す。
        expected_replacements: The expected number of occurrences to replace.
            Defaults to 1.
          * もしファイルの中に同じ old_string がいくつもあって、それを全部
            まとめて変えたい時に使います。変えたい箇所の数を指定します。
            デフォルトは「1」なので、指定しなかったら1箇所だけ変えます。
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the occurrence count does not match expected_replacements.
        OSError: If reading or writing fails.
    """
    target_path = Path(file_path)

    if not target_path.exists():
        raise FileNotFoundError(f"The file '{file_path}' does not exist.")

    # Read the file content
    # Using utf-8 as default.
    try:
        content = target_path.read_text(encoding='utf-8')
    except UnicodeDecodeError as e:
        raise ValueError(f"Failed to read '{file_path}' as UTF-8: {e}")

    # Validate occurrences
    count = content.count(old_string)

    if count == 0:
        raise ValueError(
            f"Could not find exact match for 'old_string' in '{file_path}'.\n"
            "Please verify whitespace, indentation, and newlines match exactly."
        )

    if count != expected_replacements:
        raise ValueError(
            f"Found {count} occurrence(s) of 'old_string', "
            f"but expected exactly {expected_replacements}."
        )

    # Perform replacement
    new_content = content.replace(old_string, new_string)

    # Write back to file
    target_path.write_text(new_content, encoding='utf-8')
    print(f"Successfully replaced {count} occurrence(s) in '{file_path}'.")


def main() -> None:
    """Main execution entry point for CLI usage."""
    parser = argparse.ArgumentParser(
        description="Replace exact string in a file with validation."
    )
    parser.add_argument("file_path", help="Path to the file to modify")
    # Note: Passing multi-line strings via simple CLI args can be tricky.
    # In a real scenario, we might read 'old' and 'new' from files or stdin.
    parser.add_argument("--old", required=True, help="String to replace")
    parser.add_argument("--new", required=True, help="New string")
    parser.add_argument(
        "--expected",
        type=int,
        default=1,
        help="Expected number of replacements (default: 1)"
    )

    args = parser.parse_args()

    try:
        replace_string_in_file(
            args.file_path,
            args.old,
            args.new,
            args.expected
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
