import threading
import time


ev = threading.Event()
def _timer_display():
    try:
        start_time = time.time()
        while True:
            elapsed_time = int(time.time() - start_time)
            print(f"\rElapsed time: {elapsed_time} sec", end="", flush=True)
            time.sleep(1)
            if ev.is_set():
                break
    except KeyboardInterrupt:
        print("\n計測を終了しました。")


t1 = threading.Thread(
    target=_timer_display,
)
t1.start()
try:
    time.sleep(10)
except:
    pass
finally:
    ev.set()

t1.join()
print("")
print("ok")
