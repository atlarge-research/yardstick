package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.JCommander;
import nl.tudelft.opencraft.yardstick.experiment.Experiment;
import nl.tudelft.opencraft.yardstick.experiment.Experiment1SimpleJoin;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SimpleTimeFormatter;

public class Yardstick {

    public static final String VERSION = "0.1";
    public static final GlobalLogger LOGGER = GlobalLogger.setupGlobalLogger("Yardstick");

    public static void main(String[] args) {
        // Logger
        LOGGER.setupConsoleLogging(new SimpleTimeFormatter());

        // Parse options
        Options opts = new Options();
        JCommander optParser = new JCommander(opts);
        optParser.parse(args);

        // Let's go!
        LOGGER.info("Yardstick v" + VERSION);

        Experiment ex;
        if (opts.experiment == 1) {
            ex = new Experiment1SimpleJoin(opts);
        } else {
            System.out.println("Invalid experiment: " + opts.experiment);
            return;
        }

        Thread t = new Thread(new ExperimentRunnable(ex));
        t.setName("experiment-" + opts.experiment);

        t.start();
    }

}
