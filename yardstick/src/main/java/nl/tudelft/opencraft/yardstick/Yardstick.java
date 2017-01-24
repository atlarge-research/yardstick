package nl.tudelft.opencraft.yardstick;

import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.logging.Level;
import com.beust.jcommander.JCommander;
import nl.tudelft.opencraft.yardstick.experiment.Experiment;
import nl.tudelft.opencraft.yardstick.experiment.Experiment1SimpleJoin;
import nl.tudelft.opencraft.yardstick.experiment.Experiment2ScheduledJoin;
import nl.tudelft.opencraft.yardstick.experiment.Experiment3WalkAround;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SimpleTimeFormatter;
import nl.tudelft.opencraft.yardstick.statistic.Statistics;
import nl.tudelft.opencraft.yardstick.statistic.StatisticsPusher;

public class Yardstick {

    public static final String VERSION = "0.1";
    public static final GlobalLogger LOGGER = GlobalLogger.setupGlobalLogger("Yardstick");
    public static final Options OPTIONS = new Options();
    public static final StatisticsPusher PROMETHEUS = new StatisticsPusher();

    public static void main(String[] args) {
        // Logger
        LOGGER.setupConsoleLogging(new SimpleTimeFormatter());

        // Parse options
        JCommander optParser = new JCommander(OPTIONS);
        optParser.parse(args);

        // Let's go!
        LOGGER.info("Yardstick v" + VERSION);

        if (OPTIONS.help) {
            optParser.usage();
            return;
        }

        if (OPTIONS.start != null) {
            LOGGER.info("Starting at: " + OPTIONS.start.format(DateTimeFormatter.ISO_LOCAL_TIME));

            LocalTime now = LocalTime.now();

            if (OPTIONS.start.isBefore(now)) {
                LOGGER.warning("Indicated time is in the past.");
            } else {
                long ms = now.until(OPTIONS.start, ChronoUnit.MILLIS);
                LOGGER.info("-> Sleeping " + ms + " milliseconds");
                try {
                    Thread.sleep(ms);
                } catch (InterruptedException ex) {
                    LOGGER.log(Level.WARNING, "Sleeping interrupted", ex);
                }
            }
        }

        Experiment ex;
        switch (OPTIONS.experiment) {
            case 1:
                ex = new Experiment1SimpleJoin();
                break;
            case 2:
                ex = new Experiment2ScheduledJoin();
                break;
            case 3:
                ex = new Experiment3WalkAround();
                break;
            default:
                System.out.println("Invalid experiment: " + OPTIONS.experiment);
                return;
        }

        if (OPTIONS.prometheusHost != null) {
            ex.setStats(new Statistics(OPTIONS.prometheusHost, OPTIONS.prometheusPort));
        }

        Thread t = new Thread(ex);
        t.setName("experiment-" + OPTIONS.experiment);

        t.start();
    }

}
