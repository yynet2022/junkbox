import subprocess
import threading

def read_stream(stream, buffer, prefix):
    for line in iter(stream.readline, ''):
        if line:
            print(f"[{prefix}] {line}", end="")
            buffer.append(line)
    stream.close()

def run_dual_stream(cmd):
    proc = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors="replace",
    )

    stdout_buf, stderr_buf = [], []

    # 各ストリーム用にスレッドを作成
    t1 = threading.Thread(target=read_stream, args=(proc.stdout, stdout_buf, "OUT"))
    t2 = threading.Thread(target=read_stream, args=(proc.stderr, stderr_buf, "ERR"))

    t1.start()
    t2.start()

    t1.join()
    t2.join()
    proc.wait()

    return "".join(stdout_buf), "".join(stderr_buf)

# 実行例
out, err = run_dual_stream(["sh", "-c", "ls -l; ls -l /foo; ls -l"])
print(f"OUT: {out}")
print(f"ERR: {err}")
