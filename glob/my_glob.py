import re
import fnmatch
from pathlib import Path
from typing import List

def glob(pattern: str, case_sensitive: bool = True) -> List[Path]:
    """
    pathlibを用いたglob関数。大文字小文字の区別を制御可能。
    
    Args:
        pattern: globパターン (例: "*.py", "src/**/*.py")
        case_sensitive: Trueなら大文字小文字を区別する。Falseなら区別しない。
                        (Windowsなどの区別しないファイルシステムでTrueにした場合、
                         厳密にフィルタリングして返す)
    
    Returns:
        Pathオブジェクトのリスト
    """
    # 検索の基点となるディレクトリと、相対的なパターンを分離する簡易ロジック
    # "src/**/*.py" -> root="src", pat="**/*.py"
    # 単純な "*.py" -> root=".", pat="*.py"
    # 絶対パスが含まれる場合は未対応（仕様の範囲内で簡易化）
    
    p = Path(pattern)
    
    # パターンにワイルドカードが含まれているか確認し、
    # 検索開始ディレクトリ（アンカー）を決定する
    if p.is_absolute():
        # 絶対パスの場合はサポート外とするか、簡易的にルートからとする
        # 今回はカレントディレクトリ相対を主眼に置く
        root = Path(p.anchor)
        parts = p.relative_to(root).parts
    else:
        root = Path(".")
        parts = p.parts

    # ワイルドカードが登場する前の固定パス部分を root に進める
    # 例: pattern="src/lib/*.py" -> root="src/lib", search_pattern="*.py"
    search_parts = []
    fixed_path_found = True
    
    current_root = root
    
    for part in parts:
        if fixed_path_found and not any(c in part for c in "*?[]"):
            current_root = current_root / part
        else:
            fixed_path_found = False
            search_parts.append(part)
            
    if not search_parts:
        # パターンにワイルドカードがない場合 (例: "src/main.py")
        # 存在確認だけでなく、実際のファイル名（大文字小文字）を取得するために
        # 親ディレクトリからglobするアプローチに変えるか、resolveするか。
        # resolveは絶対パスになるので、ここでは親ディレクトリから探す。
        
        if not current_root.exists():
            return []
            
        # ルート直下("main.py")の場合と、サブディレクトリ("src/main.py")の場合
        if current_root.name == '' or current_root.name == '.':
            # "." などの場合
            return [current_root]

        parent = current_root.parent
        target_name = current_root.name
        
        # 親ディレクトリが存在しないならNG
        if not parent.exists():
            return []
            
        # 親から候補を探す (case_sensitive制御のため、globのロジックを再利用したいが再帰になるので自前で)
        # ここで親ディレクトリの中身をリストアップして探す
        try:
            # target_nameが大文字小文字違っても見つけるため
            found = []
            for item in parent.iterdir():
                if case_sensitive:
                    if item.name == target_name:
                        found.append(item)
                else:
                    if item.name.lower() == target_name.lower():
                        found.append(item)
            return found
        except OSError:
            return []

    # 検索用パターンを再構築
    search_pattern = "/".join(search_parts)
    
    if not case_sensitive:
        # Linux等のCase Sensitiveなファイルシステムでも
        # 大文字小文字を無視して検索できるように、パターンを変換する。
        # 例: "*.py" -> "*.[pP][yY]"
        search_pattern = _make_case_insensitive(search_pattern)

    # pathlib.Path.glob を実行
    candidates = list(current_root.glob(search_pattern))
    
    # 隠しファイル除外ロジック (Python標準globに合わせる)
    # パターンの各コンポーネントの先頭が '.' でないのに、
    # マッチしたパスの対応する部分が '.' で始まっている場合は除外。
    # ただし単純化のため、"ファイル名が.で始まり、かつパターンが.で始まっていない" ものを除外する。
    
    # search_parts の最後の要素が "." で始まっているか？
    last_part_pattern = search_parts[-1]
    should_include_hidden = last_part_pattern.startswith('.')
    
    final_candidates = []
    for c in candidates:
        if not should_include_hidden and c.name.startswith('.') and not last_part_pattern.startswith('.'):
             continue
        final_candidates.append(c)
    candidates = final_candidates
    
    if not case_sensitive:
        # パターン側で [pP][yY] のように対処したので、
        # WindowsでもLinuxでも、この時点で目的のファイルが取れているはず。
        return candidates

    # case_sensitive = True の場合
    # 候補の中からパターンに厳密に一致するものだけをフィルタリング
    
    # fnmatch.translate はシェル形式のパターンを正規表現に変換する
    # search_pattern は "**/*.py" のような形
    
    # 注意: globの "**" はディレクトリ再帰だが、fnmatchの "*" はセパレータをまたがない、など微妙に違う。
    # ここでは、候補パスの「相対パス部分」がパターンにマッチするか正規表現でチェックする。
    
    # 厳密な判定のために、検索パターンを正規表現に変換
    # globの "**" を正規表現で正しく扱うのは難しいので、
    # シンプルに「候補のパス名(文字列)」が「指定されたパターン」にマッチするか確認するアプローチをとる。
    
    # パターン全体を正規表現化（大文字小文字区別あり）
    # fnmatch.translateは常に大文字小文字区別なしフラグを含まない正規表現を返す（?s: ...）
    # ただし、Windowsでは fnmatch.fnmatch は区別しない。fnmatch.fnmatchcase は区別する。
    
    # フィルタリングロジック:
    # 取得できた candidate (Path) が、本来の pattern (str) に合致するか。
    filtered = []
    
    # search_pattern に基づいて regex を作るのが確実だが、globの "**" の正規表現化は複雑。
    # しかし、candidates は既に glob によって構造的には正しいものが選ばれている。
    # 違いは「ファイル名の大文字小文字」だけ。
    # なので、各 candidate のパスの各要素が、パターンの各要素と（ワイルドカード以外で）一致しているか、
    # あるいは fnmatchcase で一致するかを確認すればよい。
    
    # ここではシンプルに fnmatch.translate を使うが、
    # globの "**" は fnmatch ではサポートされていない（"*"と同じ扱いになることが多い）。
    # なので、** を含む場合は fnmatch での判定が難しい。
    
    # アプローチ変更:
    # globの結果得られたパスを文字列にして、正規表現でチェックする。
    # globの "**" を ".*" に置換し、"*" を "[^/]*" に置換するような簡易変換器を作るか、
    # あるいは pathlib が返した時点でパス構造は正しいので、
    # 「ファイル名（やディレクトリ名）の大文字小文字が、実際にディスク上のものと合っているか」
    # を確認するのではなく、
    # 「ユーザーが指定したパターン（小文字）に対して、取得したパス（大文字かもしれない）がマッチするか」
    # を確認する。
    
    # 例: pattern="*.py", 取得="TEST.PY" -> マッチしないはず。
    
    for candidate in candidates:
        # 検索基点からの相対パスを取得
        try:
            rel_path = candidate.relative_to(current_root)
        except ValueError:
            continue
            
        rel_path_str = str(rel_path).replace("\\", "/") # POSIXスタイルに統一
        
        # search_pattern も "/" 区切り
        # ここで "**" 対応の自前マッチングは大変なので、
        # fnmatchcase を使うが、これは "**" を再帰として扱わない。
        
        # しかし、Pythonの glob モジュールのドキュメントによると
        # "**" はディレクトリツリーを再帰的にマッチさせる。
        # 単純な fnmatchcase(rel_path_str, search_pattern) では "**" が機能しない。
        
        # 妥協案:
        # glob パターンを正規表現に変換する簡易関数
        # (Python 3.10+ の glob._ishidden などを参考にしつつ)
        regex = _glob_to_regex(search_pattern)
        
        if re.fullmatch(regex, rel_path_str):
            filtered.append(candidate)
            
    return filtered

def _glob_to_regex(pattern: str) -> str:
    """
    再帰的なglobパターン(**)を含む文字列を正規表現に変換する。
    """
    # エスケープ処理
    i, n = 0, len(pattern)
    res = ''
    while i < n:
        c = pattern[i]
        i += 1
        if c == '*':
            # ** か * か
            if i < n and pattern[i] == '*':
                i += 1
                # "**"
                # "/**/" -> 任意のディレクトリ階層 (0個以上)
                # "**" -> 任意の文字 (パス区切り含む)
                if i < n and pattern[i] == '/':
                    i += 1
                    res += '.*' # 単純化: / を含む任意
                else:
                    res += '.*'
            else:
                # "*" -> パス区切り以外
                res += '[^/]*'
        elif c == '?':
            res += '[^/]'
        elif c == '[':
            # 文字クラスの処理は fnmatch.translate に任せたいが自前でやる
            j = i
            if j < n and pattern[j] == '!':
                j += 1
            if j < n and pattern[j] == ']':
                j += 1
            while j < n and pattern[j] != ']':
                j += 1
            if j >= n:
                res += '\\['
            else:
                stuff = pattern[i:j].replace('\\', '\\\\')
                i = j + 1
                if stuff[0] == '!':
                    stuff = '^' + stuff[1:]
                elif stuff[0] == '^':
                    stuff = '\\' + stuff
                
                # 文字クラス内でのエスケープ: [ や ] をエスケープする
                # stuffは既に中身だが、regexの文字クラス内で意味を持つ文字をエスケープすべき
                # しかし fnmatch の仕様に合わせるのは複雑。
                # ここでは簡易的に、stuffをそのまま使うが、警告が出ないようにする。
                # replace('[', '\\[') は文字クラス内では不要なことが多いが、
                # [[] というパターンが来た場合、stuffは "[" になる。
                # regexで "[" は意味を持つのでエスケープが必要。
                
                # シンプルに re.escape する手もあるが、範囲指定 a-z とか壊れる。
                # 今回の warning は "Possible nested set" なので、[[...]] の形。
                # ユーザー入力が [[]brackets] の場合、stuffは [brackets ではなく
                # globの仕様では [ は文字クラス開始。次の ] まで。
                # pattern: [[]brackets] -> i matches first [.
                # j looks for ]. 
                # [[] -> matches literal [
                # brackets] -> literal brackets]
                
                # Warningが出ているのは _make_case_insensitive の出力結果かもしれない。
                # とりあえず現状維持で、余計なエスケープを避ける。
                
                res += '[' + stuff + ']'
        else:
            res += re.escape(c)
    return res

def _make_case_insensitive(pattern: str) -> str:
    """
    globパターン内のアルファベットを [aA] 形式に変換し、
    Case SensitiveなFSでも大文字小文字を無視してマッチするようにする。
    """
    ret = []
    i = 0
    n = len(pattern)
    while i < n:
        c = pattern[i]
        if c == '[':
            # 文字クラスの開始
            j = i + 1
            if j < n and pattern[j] == '!':
                j += 1
            if j < n and pattern[j] == ']': # []...] のケース
                j += 1
            while j < n and pattern[j] != ']':
                j += 1
            
            if j < n:
                # カッコ内の文字を取得
                content = pattern[i+1:j]
                # 小文字版と大文字版を結合（a-z -> a-zA-Z となる）
                # 重複は実害ないが、isalphaなものだけ追加
                lower_content = content.lower()
                upper_content = content.upper()
                
                if lower_content == upper_content:
                    new_content = content
                else:
                    # 単純に結合する。a-z は a-zA-Z になる。
                    # !a-z のような否定は先頭の ! を維持する必要がある。
                    if content.startswith('!'):
                        new_content = '!' + content[1:].lower() + content[1:].upper()
                    else:
                        new_content = content.lower() + content.upper()
                
                ret.append(f'[{new_content}]')
                i = j + 1
            else:
                ret.append('[')
                i += 1
        elif c in '*?':
            ret.append(c)
            i += 1
        elif c.isalpha():
            ret.append(f'[{c.lower()}{c.upper()}]')
            i += 1
        else:
            ret.append(c)
            i += 1
    return "".join(ret)
