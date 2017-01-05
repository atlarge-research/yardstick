package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Report;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;

public abstract class Experiment implements Runnable {

    public static final long TICK_MS = 50;
    //
    protected final int number;
    protected final String description;
    protected final Options options;
    protected final SubLogger logger;
    //
    protected long tick = 0;

    public Experiment(int number, String desc, Options opts) {
        this.number = number;
        this.description = desc;
        this.options = opts;
        this.logger = GlobalLogger.getLogger().newSubLogger("Experiment " + number);
    }

    @Override
    public void run() {
        logger.info("Running: experiment " + number + " - " + description);

        for (String key : options.experimentParams.keySet()) {
            logger.info("Parameter - " + key + ": " + options.experimentParams.get(key));
        }

        before();

        do {
            tick();

            // TODO: Proper scheduler
            try {
                Thread.sleep(TICK_MS);
            } catch (InterruptedException ex) {
                throw new RuntimeException(ex);
            }
            tick += TICK_MS;

        } while (!isDone());

        after();

        logger.info("Experiment complete, generating report");

        Report r = report();

        logger.info(r.toString());
    }

    protected abstract void before();

    protected abstract void tick();

    protected abstract boolean isDone();

    protected abstract void after();

    public abstract Report report();

}
