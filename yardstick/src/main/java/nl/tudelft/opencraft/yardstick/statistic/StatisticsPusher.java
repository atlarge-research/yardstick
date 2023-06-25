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

package nl.tudelft.opencraft.yardstick.statistic;

import io.prometheus.client.CollectorRegistry;
import io.prometheus.client.exporter.PushGateway;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.concurrent.atomic.AtomicBoolean;

/**
 * Represents a runnable pusher which pushes a {@link CollectorRegistry} to a
 * Prometheus push gateway. This pusher pushes data every 10 seconds.
 */
public class StatisticsPusher implements Runnable {

    private final Logger logger = LoggerFactory.getLogger(StatisticsPusher.class);
    private CollectorRegistry registry;
    private PushGateway gateway;
    private final AtomicBoolean run = new AtomicBoolean(true);

    /**
     * Initializes details for the push gateway.
     *
     * @param host the push gateway host.
     * @param port the push gateway port.
     */
    public void setup(String host, int port) {
        registry = new CollectorRegistry();
        gateway = new PushGateway(host + ":" + port);
    }

    /**
     * Returns the CollectorRegistry of this StatisticsPusher.
     *
     * @return the registry.
     */
    public CollectorRegistry getRegistry() {
        return registry;
    }

    /**
     * Stops pushing data to the push gateway, if this pusher was running as a
     * runnable.
     */
    public void stop() {
        run.set(false);
    }

    @Override
    public void run() {
        while (run.get()) {

            try {
                gateway.pushAdd(registry, "yardstick", PushGateway.instanceIPGroupingKey());
            } catch (IOException ex) {
                logger.error("Could not push statistics", ex);
            }

            try {
                Thread.sleep(10_000);
            } catch (InterruptedException ex) {
                logger.error("Statistics thread interrupted!", ex);
                return;
            }
        }
    }

}
