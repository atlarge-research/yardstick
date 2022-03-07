

/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

package nl.tudelft.opencraft.yardstick;

import com.beust.jcommander.JCommander;
import java.io.File;
import java.io.FileReader;
import java.io.IOException;
import java.time.LocalTime;
import java.time.format.DateTimeFormatter;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Properties;
import java.util.Scanner;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.experiment.Experiment;
import nl.tudelft.opencraft.yardstick.experiment.Experiment10WalkStraight;
import nl.tudelft.opencraft.yardstick.experiment.Experiment11Random;
import nl.tudelft.opencraft.yardstick.experiment.Experiment12RandomE2E;
import nl.tudelft.opencraft.yardstick.experiment.Experiment1SimpleJoin;
import nl.tudelft.opencraft.yardstick.experiment.Experiment2ScheduledJoin;
import nl.tudelft.opencraft.yardstick.experiment.Experiment3WalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment4MultiWalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment5SimpleWalk;
import nl.tudelft.opencraft.yardstick.experiment.Experiment6InteractWalk;
import nl.tudelft.opencraft.yardstick.experiment.Experiment8BoxWalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment9GenerationStressTest;
import nl.tudelft.opencraft.yardstick.experiment.RemoteControlledExperiment;
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

    public static final GlobalLogger LOGGER = GlobalLogger.setupGlobalLogger("Yardstick");
    public static final Options OPTIONS = new Options();
    public static final StatisticsPusher PROMETHEUS = new StatisticsPusher();

    public static void main(String[] args) {
        // Logger
        LOGGER.setupConsoleLogging(new SimpleTimeFormatter());

        // Let's go!
        String version = null;
        final Properties properties = new Properties();
        try {
            properties.load(Yardstick.class.getClassLoader().getResourceAsStream("project.properties"));
            version = properties.getProperty("version");
        } catch (IOException e) {
            LOGGER.log(Level.SEVERE, "Could not load project.properties. This JAR was not packaged correctly!");
            System.exit(1);
        }
        LOGGER.info("Yardstick v" + version);

        List<String> allArgs = new ArrayList<>();
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
        if (args.length > 0) {
            LOGGER.warning("Yardstick configured using command-line options. Please use the config file.");
            LOGGER.warning("Command-line options: " + Arrays.toString(args));
        }
        LOGGER.info("Effective Yardstick Configuration:");
        LOGGER.info(OPTIONS.toString());

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
                ex = new Experiment8BoxWalkAround();
                break;
            case 9:
                ex = new Experiment9GenerationStressTest();
                break;
            case 10:
                ex = new Experiment10WalkStraight();
                break;
            case 11:
                ex = new Experiment11Random();
                break;
            case 12:
                ex = new Experiment12RandomE2E();
                break;
            default:
                System.out.println("Invalid experiment: " + OPTIONS.experiment);
                return;
        }

        if (OPTIONS.prometheusHost != null) {
            ex.setStats(new Statistics(OPTIONS.prometheusHost, OPTIONS.prometheusPort));
        }

        if (OPTIONS.dumpWorkload) {
            ex.setWorkloadDumper(new WorkloadDumper());
        }

        Thread t = new Thread(ex);
        t.setName("experiment-" + OPTIONS.experiment);

        t.start();
    }

}
