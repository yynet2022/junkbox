import os
import subprocess
import sys

print(os.name)
print(sys.platform)
print(os.environ.get("MSYSTEM"))
print(os.environ.get("SHELL"))
print(os.environ.get("COMSPEC"))

if (
    os.name == "nt"
    and sys.platform == "win32"
    and "MSYSTEM" in os.environ
    and "SHELL" in os.environ
):
    print("on Git bash")
    s = os.environ.get("SHELL")
    try:
        SHELL = subprocess.check_output(["cygpath", "-w", s]).decode().strip()
    except:
        SHELL = s
    print(f"SHELL=${SHELL}")
else:
    SHELL = None

cmd = "dir"
if SHELL:
    print(subprocess.check_output([SHELL, "-c", cmd]).decode("utf-8").strip())
else:
    # print(subprocess.check_output(cmd, shell=True, text=True).strip())
    print(subprocess.check_output(cmd, shell=True).decode("cp932").strip())
