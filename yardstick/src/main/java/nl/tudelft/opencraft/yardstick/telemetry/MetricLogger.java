package nl.tudelft.opencraft.yardstick.telemetry;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class MetricLogger {

    private final static Logger LOGGER = LoggerFactory.getLogger(MetricLogger.class);

    public static void log(Gauge metric) {
        LOGGER.info("{}\t{}\t{}", System.currentTimeMillis(), metric.getName(), metric.value());
    }

    public static void log(String key, Object value) {
        LOGGER.info("{}\t{}\t{}", System.currentTimeMillis(), key, value);
    }
}
