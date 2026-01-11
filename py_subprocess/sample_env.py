import os
import subprocess
import sys

DEBUG = True
if DEBUG:
    print(f"os.name: {os.name}")
    print(f"sys.platform: {sys.platform}")
    print(f'MSYSTEM: {os.environ.get("MSYSTEM")}')
    print(f'SHELL: {os.environ.get("SHELL")}')
    print(f'COMSPEC: {os.environ.get("COMSPEC")}')


def is_windows():
    return "nt" in sys.builtin_module_names


def is_posix():
    return "posix" in sys.builtin_module_names


def is_msys():
    return "MSYSTEM" in os.environ


def has_SHELL():
    return "SHELL" in os.environ


SHELL = None
if is_windows() and is_msys() and has_SHELL():
    SHELL = os.environ.get("SHELL")
    try:
        if not os.path.exists(SHELL):
            s = (
                subprocess.check_output(["cygpath", "-w", SHELL])
                .decode()
                .strip()
            )
            SHELL = s if s and os.path.exists(s) else None
            print(f"SHELL={SHELL}")
    except Exception as e:
        print(f"{e.__class__.__name__}: {e}")
        SHELL = None

if is_windows() and not SHELL:
    try:
        import mslex

        USE_MSLEX = True
    except ImportError:
        print("Not import mslex")
        import shlex

        USE_MSLEX = False
else:
    import shlex

    USE_MSLEX = False


def run_shell_command(cmd: str):
    ncmd = cmd
    if not USE_MSLEX:
        ncmd = shlex.join(shlex.split(cmd))
    else:
        ncmd = " ".join(mslex.quote(x) for x in mslex.split(cmd))

    if cmd != ncmd:
        return {
            "status": "error",
            "error_type": "security_sandbox_modification",
            "original_command": cmd,
            "interpreted_command": ncmd,
            "message": "The command was modified for security (escaping shell expansion or operators). Execution was aborted because the literal interpretation may differ from your intent. If the 'interpreted_command' is what you want, resubmit it exactly. If not, rewrite the command without complex shell syntax.",  # noqa: E501
        }

    if SHELL:
        proc = subprocess.run(
            [SHELL, "-c", ncmd],
            capture_output=True,
            encoding="utf-8",
            errors="replace",
        )
    elif is_windows():
        proc = subprocess.run(
            ncmd,
            capture_output=True,
            encoding="cp932",
            errors="replace",
            shell=True,
        )
    else:
        proc = subprocess.run(
            ncmd,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            shell=True,
        )

    return {
        "status": ("ok" if proc.returncode == 0 else "called process failed"),
        "original_command": cmd,
        "stdout": proc.stdout.strip(),
        "stderr": proc.stderr.strip(),
        "returncode": proc.returncode,
    }


if __name__ == "__main__":
    import json

    def _run(cmd):
        try:
            print(
                json.dumps(
                    run_shell_command(cmd), indent=2, ensure_ascii=False
                )
            )
        except Exception as e:
            print(f"{e.__class__.__name__}: {e}")

    _run("ls -C")
    _run('echo "foo `A` bar"')
    _run("echo 'A'")
    _run("ls /foo")
    _run("/bin/sh -cx 'echo A && echo B'")
