package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.JCommander;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.chrono.ChronoLocalDate;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.time.temporal.TemporalUnit;
import java.util.concurrent.TimeUnit;
import java.util.logging.Level;
import java.util.logging.Logger;
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

        if (opts.start != null) {
            LOGGER.info("Starting at: " + opts.start.format(DateTimeFormatter.ISO_LOCAL_TIME));

            LocalTime now = LocalTime.now();

            if (opts.start.isBefore(now)) {
                LOGGER.warning("Indicated time is in the past.");
            } else {
                long ms = now.until(opts.start, ChronoUnit.MILLIS);
                LOGGER.info("-> Sleeping " + ms + " milliseconds");
                try {
                    Thread.sleep(ms);
                } catch (InterruptedException ex) {
                    LOGGER.log(Level.WARNING, "Sleeping interrupted", ex);
                }
            }
        }

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
