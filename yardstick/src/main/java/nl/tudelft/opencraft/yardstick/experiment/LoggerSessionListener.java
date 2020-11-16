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
