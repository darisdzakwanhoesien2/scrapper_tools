# utils/timer.py
import time


def timeit(fn):
    def wrapper(*args, **kwargs):
        t0 = time.time()
        r = fn(*args, **kwargs)
        t1 = time.time()
        print(f"{fn.__name__} took {t1-t0:.3f}s")
        return r
    return wrapper