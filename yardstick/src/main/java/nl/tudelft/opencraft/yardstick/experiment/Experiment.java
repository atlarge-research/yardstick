package nl.tudelft.opencraft.yardstick.experiment;

import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.statistic.Statistics;

public abstract class Experiment implements Runnable {

    public static final long TICK_MS = 50;
    //
    protected final int number;
    protected final String description;
    protected final Options options = Yardstick.OPTIONS;
    protected final SubLogger logger;
    protected final Statistics stats;
    //
    protected long tick = 0;

    public Experiment(int number, String desc) {
        this.number = number;
        this.description = desc;
        this.logger = GlobalLogger.getLogger().newSubLogger("Experiment " + number);
        this.stats = new Statistics(options.prometheusHost, options.prometheusPort);
    }

    @Override
    public void run() {
        logger.info("Running: experiment " + number + " - " + description);

        for (String key : options.experimentParams.keySet()) {
            logger.info("Parameter - " + key + ": " + options.experimentParams.get(key));
        }

        stats.startPushing();

        before();

        do {
            tick();

            // TODO: Proper scheduler
            try {
                Thread.sleep(TICK_MS);
            } catch (InterruptedException ex) {
                logger.log(Level.SEVERE, "Ticker interrupted", ex);
            }
            tick += TICK_MS;

        } while (!isDone());

        after();

        logger.info("Experiment complete, exiting");
        stats.stopPushing();
    }

    protected abstract void before();

    protected abstract void tick();

    protected abstract boolean isDone();

    protected abstract void after();

}
