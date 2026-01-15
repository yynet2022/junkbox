
buffer = "012/abc/345/DEF/**/*.py"
s = "".join(f"[{x.lower()}{x.upper()}]" if x.isalpha() else x for x in buffer)
print(s)
