package nl.tudelft.opencraft.yardstick.util;

import java.util.concurrent.TimeUnit;

public class Scheduler {

    public static final long YIELD_AT_NANOS = 2_000_000; // 2 ms
    //
    private final long tickNanos;
    private long startNanos = 0;
    private long tickNumber = 0;

    public Scheduler(long tickMs) {
        this.tickNanos = TimeUnit.MILLISECONDS.toNanos(tickMs);
    }

    public long getTick() {
        return tickNumber;
    }

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
     * @return True if sleeping has occurred. False if this method was called to
     * late, and thus a delay was experienced.
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
