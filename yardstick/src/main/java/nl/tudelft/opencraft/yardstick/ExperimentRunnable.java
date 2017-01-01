package nl.tudelft.opencraft.yardstick;

import java.util.logging.Logger;
import nl.tudelft.opencraft.yardstick.experiment.Experiment;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;

public class ExperimentRunnable implements Runnable {

    public static final long TICK_MS = 50;
    //
    private final Logger logger;
    private final Experiment experiment;
    private long tick = 0;

    public ExperimentRunnable(Experiment probe) {
        this.logger = GlobalLogger.getLogger();
        this.experiment = probe;
    }

    @Override
    public void run() {
        logger.info("Running: " + experiment.getDescription());
        
        experiment.before();

        do {
            experiment.tick(tick);

            // TODO: Proper scheduler
            try {
                Thread.sleep(TICK_MS);
            } catch (InterruptedException ex) {
                throw new RuntimeException(ex);
            }
            tick += TICK_MS;

        } while (!experiment.isDone());

        logger.info("Experiment complete, generating report");

        Report r = experiment.after();

        logger.info(r.toString());
    }

}
