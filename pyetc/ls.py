import fnmatch
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# --- 簡易的な .gitignore パーサー ---
class GitIgnoreMatcher:
    def __init__(self, root_dir: str):
        self.root_dir = os.path.abspath(root_dir)
        self.patterns = []
        self._load_gitignore()

    def _load_gitignore(self):
        gitignore_path = os.path.join(self.root_dir, ".gitignore")
        if not os.path.exists(gitignore_path):
            return

        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    self.patterns.append(line)
        except Exception:
            pass

    def should_ignore(self, file_path: str) -> bool:
        """
        パスが .gitignore のパターンにマッチするか判定する簡易実装。
        完全な gitignore 仕様（!での否定など）は複雑なので、
        ここでは一般的な glob パターンのみをサポートします。
        """
        # 相対パスを取得
        try:
            rel_path = os.path.relpath(file_path, self.root_dir)
        except ValueError:
            return False  # パスが異なるドライブにある場合などは無視しない

        path_parts = rel_path.split(os.sep)
        name = os.path.basename(file_path)

        for pattern in self.patterns:
            # ディレクトリ指定の場合（末尾が /）
            if pattern.endswith("/"):
                dir_pattern = pattern.rstrip("/")
                if dir_pattern in path_parts:
                    return True

            # 一般的な glob マッチ
            # パターンに / が含まれる場合はパス全体でマッチ、そうでなければファイル名でマッチ
            if "/" in pattern:
                if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(
                    rel_path, pattern.lstrip("/")
                ):
                    return True
            else:
                if fnmatch.fnmatch(name, pattern):
                    return True
        return False


# --- LS ツール本体 ---


@dataclass
class FileEntry:
    name: str
    is_directory: bool
    size: int
    modified_time: datetime


class LsTool:
    def __init__(self, target_dir: str):
        self.target_dir = os.path.abspath(target_dir)
        # 簡易的な gitignore マッチャーを初期化
        # 本来はカレントディレクトリだけでなく、親ディレクトリの .gitignore も探すべきですが、
        # ここでは target_dir 直下の .gitignore のみを対象とします。
        self.gitignore = GitIgnoreMatcher(self.target_dir)

    def execute(
        self,
        dir_path: str,
        ignore_patterns: Optional[List[str]] = None,
        respect_gitignore: bool = True,
    ) -> Dict:

        # 1. パスの解決とセキュリティチェック
        resolved_path = os.path.abspath(
            os.path.join(self.target_dir, dir_path)
        )

        try:
            if (
                os.path.commonpath([self.target_dir, resolved_path])
                != self.target_dir
            ):
                return {
                    "error": f"Access denied: {dir_path} is outside the target directory."
                }
        except ValueError:
            return {"error": f"Access denied: {dir_path} is invalid."}

        if not os.path.exists(resolved_path):
            return {"error": f"Directory not found: {resolved_path}"}

        if not os.path.isdir(resolved_path):
            return {"error": f"Path is not a directory: {resolved_path}"}

        # 2. ディレクトリ読み込み
        try:
            all_files = os.listdir(resolved_path)
        except Exception as e:
            return {"error": f"Failed to list directory: {e}"}

        entries: List[FileEntry] = []
        ignored_count = 0

        for name in all_files:
            full_path = os.path.join(resolved_path, name)

            # 3. フィルタリング処理
            should_skip = False

            # (A) ユーザー指定の ignore パターン
            if ignore_patterns:
                for pat in ignore_patterns:
                    if fnmatch.fnmatch(name, pat):
                        should_skip = True
                        break

            # (B) .gitignore
            if not should_skip and respect_gitignore:
                if self.gitignore.should_ignore(full_path):
                    should_skip = True

            if should_skip:
                ignored_count += 1
                continue

            # 4. エントリ情報の取得
            try:
                stats = os.stat(full_path)
                is_dir = os.path.isdir(full_path)
                entries.append(
                    FileEntry(
                        name=name,
                        is_directory=is_dir,
                        size=0 if is_dir else stats.st_size,
                        modified_time=datetime.fromtimestamp(stats.st_mtime),
                    )
                )
            except Exception:
                # アクセス権限などで stat に失敗した場合は無視
                continue

        # 5. ソート (ディレクトリ優先、名前順)
        entries.sort(key=lambda x: (not x.is_directory, x.name.lower()))

        # 6. 結果の整形
        lines = []
        for e in entries:
            prefix = "[DIR] " if e.is_directory else ""
            lines.append(f"{prefix}{e.name}")

        result_text = f"Directory listing for {resolved_path}:\n" + "\n".join(
            lines
        )
        if ignored_count > 0:
            result_text += f"\n\n({ignored_count} ignored)"

        return {
            "content": result_text,
            "count": len(entries),
            "ignored": ignored_count,
        }


# --- 動作確認用 ---
if __name__ == "__main__":
    # プロジェクトルート（現在のディレクトリ）をターゲットにする
    tool = LsTool(os.getcwd())

    print("--- Listing current directory (respecting .gitignore) ---")
    result = tool.execute(".", ignore_patterns=["*.pyc", "__pycache__"])

    if "error" in result:
        print("Error:", result["error"])
    else:
        print(result["content"])

    print("\n--- Listing 'py' directory ---")
    result_py = tool.execute("py")
    if "error" in result_py:
        print("Error:", result_py["error"])
    else:
        print(result_py["content"])
