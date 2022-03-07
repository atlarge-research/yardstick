/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

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
     *               milliseconds.
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
