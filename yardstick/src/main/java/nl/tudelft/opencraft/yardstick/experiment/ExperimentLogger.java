package nl.tudelft.opencraft.yardstick.experiment;

import java.util.logging.Level;
import java.util.logging.Logger;
import com.github.steveice10.packetlib.event.session.ConnectedEvent;
import com.github.steveice10.packetlib.event.session.DisconnectedEvent;
import com.github.steveice10.packetlib.event.session.DisconnectingEvent;
import com.github.steveice10.packetlib.event.session.SessionAdapter;

public class ExperimentLogger extends SessionAdapter {

    private final Logger logger;

    public ExperimentLogger(Logger logger) {
        this.logger = logger;
    }

    @Override
    public void connected(ConnectedEvent ce) {
        logger.info("Connected!");
    }

    @Override
    public void disconnecting(DisconnectingEvent de) {
        logger.info("Disconnecting");
    }

    @Override
    public void disconnected(DisconnectedEvent de) {
        if (de.getCause() != null) {
            logger.log(Level.SEVERE, "Connection closed unexpectedly!", de.getCause());
        }
    }

}
