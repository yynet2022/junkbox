import os
import subprocess
import sys
import threading


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


def read_stream(stream, buffer, prefix):
    for line in iter(stream.readline, ""):
        if line:
            print(f"[{prefix}] {line}", end="")
            buffer.append(line)
    stream.close()


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

    kargs = {
        "args": ([SHELL, "-c", ncmd] if SHELL else ncmd),
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "text": True,
        "encoding": ("utf-8" if SHELL or not is_windows() else "cp932"),
        "errors": "replace",
        "shell": (False if SHELL else True),
    }
    proc = subprocess.Popen(**kargs)

    stdout_buf, stderr_buf = [], []

    # 各ストリーム用にスレッドを作成
    t1 = threading.Thread(
        target=read_stream, args=(proc.stdout, stdout_buf, "OUT")
    )
    t2 = threading.Thread(
        target=read_stream, args=(proc.stderr, stderr_buf, "ERR")
    )

    t1.start()
    t2.start()

    err = ""
    try:
        t1.join()
        t2.join()
        proc.wait()
    except (KeyboardInterrupt, Exception) as e:
        proc.terminate()
        proc.wait()
        t1.join()
        t2.join()
        err = f"{e.__class__.__name__}: {e}"

    stat = "ok"
    if proc.returncode != 0:
        stat = "called process failed"
    if err:
        stat = err

    return {
        "status": stat,
        "original_command": cmd,
        "stdout": "".join(stdout_buf).strip(),
        "stderr": "".join(stderr_buf).strip(),
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

    # 実行例
    _run("/bin/sh -c 'ls -l; ls -l /foo; sleep 10; ls -l'")
