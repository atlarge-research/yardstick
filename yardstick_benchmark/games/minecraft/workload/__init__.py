"""Minecraft workload classes.

Each workload lives in its own subfolder (see walkaround/ for the template);
this module re-exports them so callers can write::

    from yardstick_benchmark.games.minecraft.workload import WalkAround
"""

from yardstick_benchmark.games.minecraft.workload.walkaround import WalkAround

__all__ = ["WalkAround"]
