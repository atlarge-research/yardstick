package nl.tudelft.opencraft.yardstick.util;

import java.util.concurrent.TimeUnit;

/**
 * Represents an accurate repeating timer (i.e., a scheduler) for repeating
 * tasks at a fixed frequency.
 */
public class Scheduler {

    public static final long YIELD_AT_NANOS = 2_000_000; // 2 ms
    //
    private final long tickNanos;
    private long startNanos = 0;
    private long tickNumber = 0;

    /**
     * Creates a new Scheduler for executing tasks.
     *
     * @param tickMs the desired fixed delay between task executions, in
     * milliseconds.
     */
    public Scheduler(long tickMs) {
        this.tickNanos = TimeUnit.MILLISECONDS.toNanos(tickMs);
    }

    /**
     * Returns the current iteration of the scheduler. The first iteration
     * starts at zero.
     *
     * @return The iteration.
     */
    public long getTick() {
        return tickNumber;
    }

    /**
     * Starts the scheduler. Note that this only sets the clock. In order to
     * operate the scheduler, execute the tasks and call {@link #sleepTick()}
     * after each iteration.
     */
    public void start() {
        if (startNanos != 0) {
            throw new IllegalStateException("Scheduler already started");
        }
        startNanos = System.nanoTime();
    }

    /**
     * Sleeps until the next tick should occur. Should be called after a tick
     * has completely processed.
     *
     * @return true if sleeping has occurred; false if this method was called
     * too late, and thus a delay was experienced.
     */
    public boolean sleepTick() {
        tickNumber++;

        long nowNanos = System.nanoTime();
        long nextTickNanos = startNanos + (tickNumber * tickNanos);
        long toSleepNanos = nextTickNanos - nowNanos;

        if (toSleepNanos < 0) {
            return false; // Skip a tick
        }

        if (toSleepNanos > YIELD_AT_NANOS) {
            try {
                Thread.sleep(TimeUnit.NANOSECONDS.toMillis(toSleepNanos - YIELD_AT_NANOS));
            } catch (InterruptedException ex) {
            }
        }

        while (nextTickNanos - System.nanoTime() > 0) {
            Thread.yield();
        }
        return true;
    }

}
