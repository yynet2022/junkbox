import re

# p = re.compile(r'^git\b(\s+(status|diff|log)\b(\s+.*)?)?$')
p = re.compile("^git\\b(\\s+(-v|--version|-h|--help|help|status|diff|log|show|grep)\\b(\\s+.*)?)?$")

for x in ["git", "gittt",
          "git status", "git statusaa", "git status -a",
          "git diff", "git diffa", "git diff -w",
          "git log", "git log1g", "git log -n 3",
          "git --version", "git -h"]:
    print(f"'{x}'", p.match(x) is not None)
