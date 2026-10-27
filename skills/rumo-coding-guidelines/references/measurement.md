# Measurement

Read this before you report or act on a performance number you measured: a before-and-after for a change, a claimed regression, a comparison between libraries or settings, or the harness for a metric you will improve step by step. Answer each question from a run, not from reading the code.

For a rough figure the user asked for, one run is enough: still check questions 4 and 7, and say it was one run. A choice between options is never a rough figure.

## Before Running

- Write the sentence you expect to report, with its unit, percentile, and data set, such as "the export takes 30% less time at p50 on the 60k-row file". The questions below test that sentence.
- Read the measurement script: what it times, what it counts, and what it leaves out.
- Check whether the machine is busy (load average, core count, running builds). When you cannot quiet it, alternate the two sides so both meet the same noise, and say so.

## Questions

1. **What limits it?** Name the resource that stops the number from being twice as good: one CPU core, disk, network, a lock, the database, or the load generator itself. Find it with a profiler or per-process counters in a separate run, because profiling slows the work. When a change did not move the number, the limit usually explains why.
2. **Were both sides set up the way they run for real?** Same build mode, flags, connection pools, batch sizes, cache state, versions, and data. A side left on defaults compares configurations, not implementations; tune it and measure again before you name a winner.
3. **Is it physically possible?** Compare the result with what the hardware can do and with the share of time the changed part took. Removing a step that took 10% of the run cannot make the run more than about 11% faster. A result past a limit measured something else, such as a cache hit or skipped work.
4. **Did anything fail?** Count errors, rejections, timeouts, and retries, and check that the outputs are correct, not just present. Failures are often fast. When the script does not count them, add the count.
5. **Does it repeat?** Run each side at least five times, alternating A and B so warm-up and drift favor neither, and report the median and the range. A difference smaller than the spread between runs is no measurable difference.
6. **Does it matter end to end?** Next to a micro-benchmark, measure the path a user actually waits on, with realistic sizes and concurrency, and give the micro result as a share of the whole.
7. **Did the work happen?** Confirm the timed region did the work: the request reached the server, the rows were written, the result was used. Lazy evaluation, unawaited promises, and discarded results produce fast numbers for work that never ran.

## Report

- Lead with the verdict: faster, slower, no measurable difference, or inconclusive.
- Then the number with its unit, the run count, the range, and the limit, for example "p50 41 ms → 33 ms, median of 7 runs per side, range 32–35 ms after; limited by JSON parsing on one core".
- Call the verdict inconclusive when you cannot name the limit, when one side ran untuned, or when questions 4 or 7 could not be checked, and name the gap.
