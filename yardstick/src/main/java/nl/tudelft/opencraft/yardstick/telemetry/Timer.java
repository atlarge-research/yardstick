package nl.tudelft.opencraft.yardstick.telemetry;

import lombok.Getter;

public class Timer {
    @Getter
    private final String name;
    private long start;
    private boolean started;

    public Timer(String name) {
        this.name = name;
    }

    public void start() {
        start = System.currentTimeMillis();
        started = true;
    }

    public long stop() {
        if (!started) {
            throw new IllegalStateException("timer stopped before start");
        }
        long duration = System.currentTimeMillis() - start;
        reset();
        MetricLogger.log(name, duration);
        return duration;
    }

    public void reset() {
        started = false;
    }
}
