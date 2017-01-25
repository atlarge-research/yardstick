package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.statistic.Statistics;
import nl.tudelft.opencraft.yardstick.util.Scheduler;

public abstract class Experiment implements Runnable {

    public static final long TICK_MS = 50;
    //
    protected final int number;
    protected final String description;
    protected final Options options = Yardstick.OPTIONS;
    protected final SubLogger logger;

    protected long tick = 0;
    private Statistics stats;

    public Experiment(int number, String desc) {
        this.number = number;
        this.description = desc;
        this.logger = GlobalLogger.getLogger().newSubLogger("Experiment " + number);
    }

    @Override
    public void run() {
        logger.info("Running: experiment " + number + " - " + description);

        for (String key : options.experimentParams.keySet()) {
            logger.info("Parameter - " + key + ": " + options.experimentParams.get(key));
        }

        if (stats != null) {
            stats.startPushing();
        }

        Scheduler sched = new Scheduler(TICK_MS);
        sched.start();

        before();

        do {
            tick();
            sched.sleepTick();
        } while (!isDone());

        after();

        logger.info("Experiment complete, exiting");
        if (stats != null) {
            stats.stopPushing();
        }
    }

    protected abstract void before();

    protected abstract void tick();

    protected abstract boolean isDone();

    protected abstract void after();

    public Statistics getStats() {
        return stats;
    }

    public void setStats(Statistics stats) {
        this.stats = stats;
    }
}
