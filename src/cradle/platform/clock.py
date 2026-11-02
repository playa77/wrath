# Version: 0.2.0 | 2026-11-02
"""Presentation pacing only; never receives or accesses engine state."""

import time


def pace(cfg, n_msgs):
    delay = cfg.time_lag * 0.150 * n_msgs
    if delay:
        time.sleep(delay)
