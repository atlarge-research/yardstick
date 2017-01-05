package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.JCommander;
import nl.tudelft.opencraft.yardstick.experiment.Experiment;
import nl.tudelft.opencraft.yardstick.experiment.Experiment1SimpleJoin;
import nl.tudelft.opencraft.yardstick.experiment.Experiment2ScheduledJoin;
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
        switch (opts.experiment) {
            case 1:
                ex = new Experiment1SimpleJoin(opts);
                break;
            case 2:
                ex = new Experiment2ScheduledJoin(opts);
                break;
            default:
                System.out.println("Invalid experiment: " + opts.experiment);
                return;
        }

        Thread t = new Thread(ex);
        t.setName("experiment-" + opts.experiment);

        t.start();
    }

}
