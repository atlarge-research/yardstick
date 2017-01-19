package nl.tudelft.opencraft.yardstick.statistic;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Level;
import io.prometheus.client.CollectorRegistry;
import io.prometheus.client.exporter.PushGateway;
import nl.tudelft.opencraft.yardstick.Yardstick;

public class StatisticsPusher implements Runnable {

    private CollectorRegistry registry;
    private PushGateway gateway;
    private final AtomicBoolean run = new AtomicBoolean(true);

    public void setup(String host, int port) {
        registry = new CollectorRegistry();
        gateway = new PushGateway(host + ":" + port);
    }

    public CollectorRegistry getRegistry() {
        return registry;
    }

    public void stop() {
        run.set(false);
    }

    @Override
    public void run() {
        while (run.get()) {

            try {
                gateway.pushAdd(registry, "yardstick");
            } catch (IOException ex) {
                Yardstick.LOGGER.log(Level.SEVERE, "Could not push statistics", ex);
            }

            try {
                Thread.sleep(10000);
            } catch (InterruptedException ex) {
                Yardstick.LOGGER.log(Level.SEVERE, "Statistics thread interrupted!", ex);
                return;
            }
        }
    }

}
