

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
import nl.tudelft.opencraft.yardstick.experiment.Experiment;
import nl.tudelft.opencraft.yardstick.experiment.Experiment10GenerationStressTest;
import nl.tudelft.opencraft.yardstick.experiment.Experiment10WalkStraight;
import nl.tudelft.opencraft.yardstick.experiment.Experiment11Latency;
import nl.tudelft.opencraft.yardstick.experiment.Experiment11Random;
import nl.tudelft.opencraft.yardstick.experiment.Experiment12LatencyAndWalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment12RandomE2E;
import nl.tudelft.opencraft.yardstick.experiment.Experiment3WalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment4MultiWalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment5SimpleWalk;
import nl.tudelft.opencraft.yardstick.experiment.Experiment6InteractWalk;
import nl.tudelft.opencraft.yardstick.experiment.Experiment8BoxWalkAround;
import nl.tudelft.opencraft.yardstick.experiment.Experiment9GenerationStressTest;
import nl.tudelft.opencraft.yardstick.experiment.Experiment9Spike;
import nl.tudelft.opencraft.yardstick.experiment.RemoteControlledExperiment;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;
import nl.tudelft.opencraft.yardstick.game.GameFactory;
import nl.tudelft.opencraft.yardstick.workload.CsvConverter;
import nl.tudelft.opencraft.yardstick.workload.WorkloadDumper;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;

/**
 * Entry point for the emulator.
 */
public class Yardstick {

    public static final ScheduledExecutorService THREAD_POOL = Executors.newScheduledThreadPool(Runtime.getRuntime().availableProcessors());

    private final static Logger LOGGER = LoggerFactory.getLogger(Yardstick.class);

    public static void main(String[] args) {
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
        LOGGER.info(options.toString());

        if (options.csvDump) {
            if (options.inFile == null || options.outFile == null) {
                LOGGER.error("CSV conversion requires both input and output files to be set.");
                return;
            }

            CsvConverter.convertCsv(options.inFile, options.outFile);
            return;
        }
        int id = options.nodeID;
        String address = options.address;

        Config experimentConfig = config.getConfig("yardstick.player-emulation.arguments");
        GameArchitecture game = new GameFactory().getGame(address, experimentConfig);

        String behaviorName = experimentConfig.getString("behavior.name");
        Config behaviorConfig = experimentConfig.getConfig("behavior." + behaviorName);
        Duration experimentDuration = experimentConfig.getDuration("duration");

        Experiment ex;
        switch (behaviorName) {
            case "3":
                ex = new Experiment3WalkAround(id, game);
                break;
            case "4":
                ex = new Experiment4MultiWalkAround(id, game, behaviorConfig);
                break;
            case "5":
                ex = new Experiment5SimpleWalk(id, game, experimentDuration);
                break;
            case "6":
                ex = new Experiment6InteractWalk(id, game, experimentDuration);
                break;
            case "7":
                ex = new RemoteControlledExperiment(id, game);
                break;
            case "8":
                ex = new Experiment8BoxWalkAround(id, game, behaviorConfig);
                break;
            case "9":
                ex = new Experiment9Spike(id, game, behaviorConfig);
                break;
            case "10":
                ex = new Experiment10GenerationStressTest(id, game, behaviorConfig);
                break;
            case "11":
                ex = new Experiment11Latency(id, game, behaviorConfig);
                break;
            case "12":
                ex = new Experiment12LatencyAndWalkAround(id, game, behaviorConfig);
                break;
            case "13":
                ex = new Experiment9GenerationStressTest();
                break;
            case "14":
                ex = new Experiment10WalkStraight();
                break;
            case "15":
                ex = new Experiment11Random();
                break;
            case "16":
                ex = new Experiment12RandomE2E();
                break;
            default:
                System.out.println("Invalid experiment: " + behaviorName);
                return;
        }

        if (config.getBoolean("yardstick.player-emulation.arguments.packet-trace")) {
            ex.setWorkloadDumper(new WorkloadDumper());
        }

        Thread t = new Thread(ex);
        t.setName("experiment-" + behaviorName);

        t.start();
    }

}
