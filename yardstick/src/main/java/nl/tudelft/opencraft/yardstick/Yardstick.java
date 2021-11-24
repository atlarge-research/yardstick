

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
import com.typesafe.config.Config;
import com.typesafe.config.ConfigFactory;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import nl.tudelft.opencraft.yardstick.experiment.Experiment;
import nl.tudelft.opencraft.yardstick.experiment.Experiment10GenerationStressTest;
import nl.tudelft.opencraft.yardstick.experiment.Experiment11Latency;
import nl.tudelft.opencraft.yardstick.experiment.Experiment12LatencyAndWalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment3WalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment4MultiWalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment5SimpleWalk;
import nl.tudelft.opencraft.yardstick.experiment.Experiment6InteractWalk;
import nl.tudelft.opencraft.yardstick.experiment.Experiment8BoxWalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment9Spike;
import nl.tudelft.opencraft.yardstick.experiment.RemoteControlledExperiment;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SimpleTimeFormatter;
import nl.tudelft.opencraft.yardstick.workload.CsvConverter;
import nl.tudelft.opencraft.yardstick.workload.WorkloadDumper;

/**
 * Entry point for the emulator.
 */
public class Yardstick {

    public static final GlobalLogger LOGGER = GlobalLogger.setupGlobalLogger("Yardstick");
    public static final ScheduledExecutorService THREAD_POOL = Executors.newScheduledThreadPool(Runtime.getRuntime().availableProcessors());

    public static void main(String[] args) {
        // Logger
        LOGGER.setupConsoleLogging(new SimpleTimeFormatter());

        // Parse command line options
        Options options = new Options();
        JCommander optParser = new JCommander(options);
        optParser.parse(args);

        if (options.help) {
            optParser.usage();
            return;
        }

        LOGGER.info("Effective Yardstick Configuration:");
        Config config = ConfigFactory.load();
        LOGGER.info(config.toString());

        if (options.csvDump) {
            if (options.inFile == null || options.outFile == null) {
                LOGGER.severe("CSV conversion requires both input and output files to be set.");
                return;
            }

            CsvConverter.convertCsv(options.inFile, options.outFile);
            return;
        }
        int id = options.nodeID;
        String address = options.address;

        Config experimentConfig = config.getConfig("benchmark.player-emulation.arguments");
        String experimentName = experimentConfig.getString("behavior.name");
        Experiment ex;
        switch (experimentName) {
            case "3":
                ex = new Experiment3WalkAround(id, address, experimentConfig);
                break;
            case "4":
                ex = new Experiment4MultiWalkAround(id, address, experimentConfig);
                break;
            case "5":
                ex = new Experiment5SimpleWalk(id, address, experimentConfig);
                break;
            case "6":
                ex = new Experiment6InteractWalk(id, address, experimentConfig);
                break;
            case "7":
                ex = new RemoteControlledExperiment(id, address, experimentConfig);
                break;
            case "8":
                ex = new Experiment8BoxWalkAround(id, address, experimentConfig);
                break;
            case "9":
                ex = new Experiment9Spike(id, address, experimentConfig);
                break;
            case "10":
                ex = new Experiment10GenerationStressTest(id, address, experimentConfig);
                break;
            case "11":
                ex = new Experiment11Latency(id, address, experimentConfig);
                break;
            case "12":
                ex = new Experiment12LatencyAndWalkAround(id, address, experimentConfig);
                break;
            default:
                System.out.println("Invalid experiment: " + experimentName);
                return;
        }

        if (config.getBoolean("benchmark.player-emulation.arguments.packet-trace")) {
            ex.setWorkloadDumper(new WorkloadDumper());
        }

        Thread t = new Thread(ex);
        t.setName("experiment-" + experimentName);

        t.start();
    }

}
