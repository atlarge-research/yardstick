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

package nl.tudelft.opencraft.yardstick.experiment;

import java.util.logging.Level;
import java.util.logging.Logger;
import science.atlarge.opencraft.packetlib.event.session.ConnectedEvent;
import science.atlarge.opencraft.packetlib.event.session.DisconnectedEvent;
import science.atlarge.opencraft.packetlib.event.session.DisconnectingEvent;
import science.atlarge.opencraft.packetlib.event.session.SessionAdapter;

/**
 * A {@link SessionAdapter} for logging bot events to a {@link Logger}.
 */
public class LoggerSessionListener extends SessionAdapter {

    private final Logger logger;

    /**
     * Creates a new LoggerSessionListener with the specified logger.
     *
     * @param logger the logger.
     */
    public LoggerSessionListener(Logger logger) {
        this.logger = logger;
    }

    @Override
    public void connected(ConnectedEvent ce) {
        logger.info("Connected");
    }

    @Override
    public void disconnecting(DisconnectingEvent de) {
    }

    @Override
    public void disconnected(DisconnectedEvent de) {
        if (de.getCause() != null) {
            logger.log(Level.SEVERE, "Connection closed unexpectedly!", de.getCause());
        }
    }

}
