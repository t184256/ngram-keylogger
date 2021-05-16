# Copyright (c) 2021, see AUTHORS. Licensed under GPLv3+, see LICENSE.

import time

import psutil


last_process_scan_time, last_process_scan_result = 0, False


def cached_process_scan(func, no_more_often_than=1):
    # assumes that func never changes
    global last_process_scan_time, last_process_scan_result
    now = time.time()
    if now - last_process_scan_time < no_more_often_than:
        return last_process_scan_result
    last_process_scan_time = now
    last_process_scan_result = process_scan(func)
    return last_process_scan_result


def process_scan(func):
    for proc in psutil.process_iter():
        try:
            if func(proc):
                return proc.name()
        except (psutil.NoSuchProcess,
                psutil.AccessDenied,
                psutil.ZombieProcess):
            pass
