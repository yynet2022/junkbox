import os
import subprocess
import sys
import re
import fnmatch
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass

# --- 1. 除外パターン管理クラス (共通部品のイメージ) --- 
class FileExclusions:
    """
    ファイルやディレクトリの除外パターンを管理します。
    本来は .gitignore を解析したり、設定ファイルから読み込んだりします。
    """
    def __init__(self):
        # デフォルトで無視したいディレクトリ
        self.ignore_dirs = {
            '.git', 'node_modules', '__pycache__', '.venv', 'dist', 'build', 'coverage'
        }
        # デフォルトで無視したいファイルパターン（glob形式）
        self.ignore_files = {
            '*.pyc', '*.o', '*.exe', '*.dll', '*.so', '*.dylib',
            '.DS_Store', 'Thumbs.db'
        }
        # バイナリっぽい拡張子（grep -I 相当のフィルタ用）
        self.binary_extensions = {
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.webp',
            '.mp3', '.wav', '.mp4', '.mov', '.avi',
            '.pdf', '.zip', '.tar', '.gz'
        }

    def is_ignored(self, file_path: str, base_dir: str) -> bool:
        """ファイルが除外対象かどうか判定します（Python Fallback用）"""
        filename = os.path.basename(file_path)
        
        # 拡張子チェック
        _, ext = os.path.splitext(filename)
        if ext.lower() in self.binary_extensions:
            return True

        # ファイルパターンチェック
        for pattern in self.ignore_files:
            if fnmatch.fnmatch(filename, pattern):
                return True
        
        return False

    def should_skip_dir(self, dir_name: str) -> bool:
        """ディレクトリ探索をスキップすべきか判定します"""
        return dir_name in self.ignore_dirs

    def get_grep_exclude_dir_args(self) -> List[str]:
        """システム grep コマンドに渡す --exclude-dir 引数を生成します"""
        args = []
        for d in self.ignore_dirs:
            args.append(f"--exclude-dir={d}")
        return args

# --- 2. 結果格納用クラス --- 
@dataclass
class GrepMatch:
    file_path: str
    line_number: int
    line_content: str

# --- 3. Grep ツール本体 --- 
class GrepTool:
    def __init__(self, target_dir: str):
        self.target_dir = os.path.abspath(target_dir)
        self.exclusions = FileExclusions()

    def execute(self, pattern: str, include: Optional[str] = None) -> List[GrepMatch]:
        """
        3つの戦略を順に試して検索を行います。
        1. git grep (Gitリポジトリの場合)
        2. system grep (grepコマンドがある場合)
        3. python fallback (最終手段)
        """
        print(f"Searching for pattern: '{pattern}' in {self.target_dir} ...")

        # 戦略1: git grep
        # .gitignore を勝手に考慮してくれるので最強かつ最速です。
        if self._is_git_repo() and self._is_command_available("git"):
            print("[Strategy 1] Using 'git grep'")
            try:
                return self._strategy_git_grep(pattern, include)
            except Exception as e:
                print(f"Warning: git grep failed ({e}), falling back...")

        # 戦略2: system grep
        # OS標準のgrepを使います。高速ですが、.gitignore は考慮しないので
        # 手動で除外オプション(--exclude-dirなど)を渡す必要があります。
        if self._is_command_available("grep"):
            print("[Strategy 2] Using 'system grep'")
            try:
                return self._strategy_system_grep(pattern, include)
            except Exception as e:
                print(f"Warning: system grep failed ({e}), falling back...")

        # 戦略3: Python Fallback
        # 外部コマンドに頼らず、Pythonだけで検索します。
        # 速度は劣りますが、環境依存がありません。
        print("[Strategy 3] Using 'Python fallback'")
        return self._strategy_python_fallback(pattern, include)

    # --- Helper Methods --- 
    def _is_git_repo(self) -> bool:
        return os.path.isdir(os.path.join(self.target_dir, ".git"))

    def _is_command_available(self, cmd: str) -> bool:
        """コマンドが使えるかチェック (Windows/Linux両対応)"""
        check_cmd = ["where" if os.name == "nt" else "which", cmd]
        try:
            subprocess.run(check_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except subprocess.CalledProcessError:
            return False

    def _parse_grep_output(self, output: str) -> List[GrepMatch]:
        """
        grep形式の出力 (FilePath:LineNum:Content) をパースします。
        例: src/main.py:10:print("hello")
        """
        results = []
        for line in output.splitlines():
            if not line.strip(): continue
            
            # 最初の2つのコロンを探す
            parts = line.split(":", 2)
            if len(parts) < 3: continue
            
            file_path, line_num_str, content = parts
            try:
                results.append(GrepMatch(
                    file_path=file_path,
                    line_number=int(line_num_str),
                    line_content=content
                ))
            except ValueError:
                continue
        return results

    # --- Strategy Implementations --- 

    def _strategy_git_grep(self, pattern: str, include: Optional[str]) -> List[GrepMatch]:
        # git grep コマンドの組み立て
        # --untracked: Git管理下でないファイルも検索対象にする
        # -n: 行番号を表示
        # -E: 拡張正規表現を使用
        # --ignore-case: 大文字小文字を区別しない
        # -I: バイナリファイルを無視 (git grep はデフォルトで無視するが念のため)
        cmd = ["git", "grep", "--untracked", "-n", "-E", "--ignore-case", "-I", pattern]
        
        if include:
            # git grep で特定のファイルのみ対象にする場合: -- "*.py" のように指定
            cmd += ["--", include]
            
        # subprocess で実行
        result = subprocess.run(
            cmd,
            cwd=self.target_dir,
            capture_output=True,
            text=True,
            encoding='utf-8', # Windowsでは cp932 になることもあるので注意
            errors='replace'
        )
        
        if result.returncode not in (0, 1): # 0=見つかった, 1=見つからない, 2+=エラー
            raise RuntimeError(f"Exit code {result.returncode}: {result.stderr}")
            
        return self._parse_grep_output(result.stdout)

    def _strategy_system_grep(self, pattern: str, include: Optional[str]) -> List[GrepMatch]:
        # system grep コマンドの組み立て
        # -r: 再帰的にディレクトリを探索
        # -n: 行番号を表示
        # -H: ファイル名を表示 (ファイルが1つの場合でも強制表示)
        # -E: 拡張正規表現
        # -I: バイナリファイルを無視
        cmd = ["grep", "-r", "-n", "-H", "-E", "-I"]
        
        # 除外ディレクトリの指定 (--exclude-dir)
        cmd += self.exclusions.get_grep_exclude_dir_args()
        
        if include:
            # --include=*.py
            cmd.append(f"--include={include}")
            
        cmd += [pattern, "."] # "." はカレントディレクトリ 
        
        result = subprocess.run(
            cmd,
            cwd=self.target_dir,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        if result.returncode not in (0, 1):
            raise RuntimeError(f"Exit code {result.returncode}: {result.stderr}")
            
        return self._parse_grep_output(result.stdout)

    def _strategy_python_fallback(self, pattern: str, include: Optional[str]) -> List[GrepMatch]:
        results = []
        regex = re.compile(pattern, re.IGNORECASE)
        
        # os.walk で再帰探索
        for root, dirs, files in os.walk(self.target_dir):
            # 1. ディレクトリの除外設定を適用
            # dirs[:] = ... とすることで、os.walk の探索対象からその場で削除できる
            dirs[:] = [d for d in dirs if not self.exclusions.should_skip_dir(d)]
            
            for file in files:
                file_path = os.path.join(root, file)
                
                # 2. include パターンがある場合のフィルタ
                if include and not fnmatch.fnmatch(file, include):
                    continue
                    
                # 3. ファイル除外設定（バイナリ等）の適用
                if self.exclusions.is_ignored(file_path, self.target_dir):
                    continue
                
                # 4. ファイルを開いて検索
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for i, line in enumerate(f):
                            if regex.search(line):
                                # 相対パスに変換して格納
                                rel_path = os.path.relpath(file_path, self.target_dir)
                                results.append(GrepMatch(
                                    file_path=rel_path,
                                    line_number=i + 1,
                                    line_content=line.strip()
                                ))
                except Exception:
                    # 読み込みエラーは無視
                    continue
                    
        return results

# --- 動作確認用 --- 
if __name__ == "__main__":
    # カレントディレクトリで検索テスト
    tool = GrepTool(os.getcwd())
    
    # 検索したいパターン (正規表現)
    search_pattern = "class .*Tool"  # "class" で始まって "Tool" で終わる文字列
    
    # 実行
    matches = tool.execute(search_pattern, include="*.py")
    
    print(f"\nFound {len(matches)} matches:")
    for m in matches:
        print(f"{m.file_path}:{m.line_number}: {m.line_content}")
