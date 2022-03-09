package nl.tudelft.opencraft.yardstick.telemetry;

import lombok.Getter;

import java.util.concurrent.atomic.AtomicLong;

public class Gauge {
    @Getter
    private final String name;
    private final AtomicLong value = new AtomicLong(0);

    public Gauge(String name) {
        this.name = name;
    }

    public void set(long value) {
        this.value.set(value);
        MetricLogger.log(name, value);
    }

    public long value() {
        return value.get();
    }

    public void add(long value) {
        MetricLogger.log(name, this.value.addAndGet(value));
    }

    public void inc() {
        MetricLogger.log(name, value.incrementAndGet());
    }

    public void dec() {
        MetricLogger.log(name, value.decrementAndGet());
    }
}
