import os
import pytest
from GitIgnoreMatcher import GitIgnoreMatcher

@pytest.fixture
def setup_fs(tmp_path):
    root = tmp_path
    
    gitignore_content = """
*.log
tmp/
!keep.log
/root_only.txt
sub/**/*.secret
tmp_wild*/
"""
    (root / ".gitignore").write_text(gitignore_content, encoding="utf-8")
    
    (root / "a.log").touch()
    (root / "keep.log").touch()
    (root / "root_only.txt").touch()
    
    (root / "sub").mkdir()
    (root / "sub" / "deep").mkdir()
    (root / "sub" / "deep" / "test.secret").touch()
    (root / "sub" / "foo.secret").touch()
    
    (root / "tmp").mkdir()
    (root / "tmp_wild_1").mkdir()

    (root / "nested").mkdir()
    (root / "nested" / "root_only.txt").touch()
    
    return root

def test_gitignore_matcher(setup_fs):
    root = setup_fs
    cwd = os.getcwd()
    try:
        os.chdir(root)
        matcher = GitIgnoreMatcher(root_path=".")
        
        # 1. 基本的な拡張子マッチ (*.log)
        assert matcher.is_match_file("a.log") is True, "*.log should be ignored"
        
        # 2. 否定パターン (!keep.log)
        assert matcher.is_match_file("keep.log") is False, "!keep.log should not be ignored"
        
        # 3. ディレクトリ完全一致 (tmp/)
        # 現在の実装では、.gitignoreに "tmp/" があると ignore_dirs に "tmp" が入る
        assert matcher.is_match_dir("tmp") is True, "tmp/ directory should be ignored"
        
        # 4. ディレクトリのワイルドカード (tmp_wild*/)
        # "tmp_wild*/" -> ignore_dirs に "tmp_wild*" が入る
        # "tmp_wild_1" in ["tmp_wild*"] は False になるはず
        # これが仕様不備の確認ポイント
        assert matcher.is_match_dir("tmp_wild_1") is True, "tmp_wild*/ should match tmp_wild_1 directory"
        
        # 5. アンカー付きパス (/root_only.txt)
        assert matcher.is_match_file("root_only.txt") is True, "/root_only.txt should match root file"
        # ネストしたファイルはマッチしてはいけない
        assert matcher.is_match_file(os.path.join("nested", "root_only.txt")) is False, "/root_only.txt should NOT match nested/root_only.txt"
        
        # 6. ダブルアスタリスク (sub/**/*.secret)
        # fnmatch は ** をサポートしていないため、失敗する可能性が高い
        assert matcher.is_match_file(os.path.join("sub", "deep", "test.secret")) is True, "sub/**/*.secret should match deep file"
        assert matcher.is_match_file(os.path.join("sub", "foo.secret")) is True, "sub/**/*.secret should match direct sub file"

        # 7. .git directory itself (implicit ignore)
        assert matcher.is_match_dir(".git") is True, ".git directory should be ignored by default"
        assert matcher.is_match_file(os.path.join(".git", "HEAD")) is True, ".git contents should be ignored"

    finally:
        os.chdir(cwd)
