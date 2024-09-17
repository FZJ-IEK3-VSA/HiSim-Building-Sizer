""" For calling a model with profiler and creating a log file. """

# clean
import cProfile
import pstats
import os
from start_building_sizer_no_utsp import main


def maincall() -> None:
    """For calling the Hisim main."""
    # change call here as needed
    main()


if __name__ == "__main__":

    profiler = cProfile.Profile()
    profiler.enable()
    maincall()
    profiler.disable()

    results_path = os.getcwd()

    with open(
        os.path.join(results_path, "profilingStatsAsTextSortedCumulative.txt"),
        "w",
        encoding="utf-8",
    ) as f:
        stats = pstats.Stats(profiler, stream=f).sort_stats("cumulative")
        stats.print_stats()
    with open(
        os.path.join(results_path, "profilingStatsAsTextSortedcalls.txt"),
        "w",
        encoding="utf-8",
    ) as f:
        stats = pstats.Stats(profiler, stream=f).sort_stats("ncalls")
        stats.print_stats()
    with open(
        os.path.join(results_path, "profilingStatsAsTextSortedTotalTime.txt"),
        "w",
        encoding="utf-8",
    ) as f:
        stats = pstats.Stats(profiler, stream=f).sort_stats("tottime")
        stats.print_stats()
    stats.dump_stats(os.path.join(results_path, "profile-export-data.prof"))
