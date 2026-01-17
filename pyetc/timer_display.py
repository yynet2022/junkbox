import threading
import time


class _TimerDisplay(threading.Thread):
    def __init__(self):
        super().__init__()
        self.thread_event = threading.Event()

    def run(self):
        try:
            start_time = time.time()
            while True:
                elapsed_time = int(time.time() - start_time)
                print(f"\rElapsed time: {elapsed_time} sec", end="", flush=True)
                time.sleep(1)
                if self.thread_event.is_set():
                    break
        except KeyboardInterrupt as e:
            print(f"\n==={e.__class__.__name__}: {e}")


def main():
    t = _TimerDisplay()
    t.start()
    try:
        time.sleep(10)
    except (KeyboardInterrupt, Exception) as e:
        print(f"\n---{e.__class__.__name__}: {e}")
        return
    finally:
        t.thread_event.set()
        t.join()

    print("")
    print("ok")


if __name__ == "__main__":
    main()
