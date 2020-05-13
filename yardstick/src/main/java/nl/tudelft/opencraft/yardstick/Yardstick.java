package nl.tudelft.opencraft.yardstick;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Scanner;
import java.util.logging.Level;
import com.beust.jcommander.JCommander;
import com.moandjiezana.toml.Toml;
import nl.tudelft.opencraft.yardstick.experiment.*;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SimpleTimeFormatter;
import nl.tudelft.opencraft.yardstick.statistic.Statistics;
import nl.tudelft.opencraft.yardstick.statistic.StatisticsPusher;
import nl.tudelft.opencraft.yardstick.workload.CsvConverter;
import nl.tudelft.opencraft.yardstick.workload.WorkloadDumper;

/**
 * Entry point for the emulator.
 */
public class Yardstick {

    public static final String VERSION = "0.1";
    public static final GlobalLogger LOGGER = GlobalLogger.setupGlobalLogger("Yardstick");
    public static final Options OPTIONS = new Options();
    public static final StatisticsPusher PROMETHEUS = new StatisticsPusher();

    public static void main(String[] args) {
        // Logger
        LOGGER.setupConsoleLogging(new SimpleTimeFormatter());
        File logs = new File("logs.txt");
        LOGGER.setupFileLogging(new SimpleTimeFormatter(), logs);
        List<String> allArgs = new ArrayList<String>();
        // Parse options from config file
        try (FileReader reader = new FileReader("yardstick.properties"); Scanner scanner = new Scanner(reader);) {
            while (scanner.hasNext()) {
                allArgs.add(scanner.next());
            }
        } catch (IOException e) {
            // Never mind
        }
        Collections.addAll(allArgs, args);

        File config = new File("yardstick.toml");
        // Parse config options
        OPTIONS.readTOML(config);
        // Parse command line options
        JCommander optParser = new JCommander(OPTIONS);
        optParser.parse(allArgs.toArray(new String[0]));

        // Let's go!
        LOGGER.info("Yardstick v" + VERSION);

        if (OPTIONS.help) {
            optParser.usage();
            return;
        }

        if (OPTIONS.csvDump) {
            if (OPTIONS.inFile == null || OPTIONS.outFile == null) {
                LOGGER.severe("CSV conversion requires both input and output files to be set.");
                return;
            }

            CsvConverter.convertCsv(OPTIONS.inFile, OPTIONS.outFile);
            return;
        }

        if (OPTIONS.experiment < 1) {
            LOGGER.severe("You must specify the experiment ID.");
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
            case 4:
                ex = new Experiment4MultiWalkAround();
                break;
            case 5:
                ex = new Experiment5SimpleWalk();
                break;
            case 6:
                ex = new Experiment6InteractWalk();
                break;
            case 7:
                ex = new RemoteControlledExperiment();
                break;
            case 8:
                ex = new Experiment8();
                break;
            default:
                System.out.println("Invalid experiment: " + OPTIONS.experiment);
                return;
        }

        if (OPTIONS.prometheusHost != null) {
            ex.setStats(new Statistics(OPTIONS.prometheusHost, OPTIONS.prometheusPort));
        }

        if (OPTIONS.dumpWorkload) {
            ex.setWorkloadDumper(new WorkloadDumper(OPTIONS.dumpMessageContents));
        }

        Thread t = new Thread(ex);
        t.setName("experiment-" + OPTIONS.experiment);

        t.start();
    }

}
