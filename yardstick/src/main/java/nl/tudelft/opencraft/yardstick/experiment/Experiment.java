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

package nl.tudelft.opencraft.yardstick.experiment;

import science.atlarge.opencraft.mcprotocollib.MinecraftProtocol;
import science.atlarge.opencraft.packetlib.Client;
import science.atlarge.opencraft.packetlib.Session;
import science.atlarge.opencraft.packetlib.tcp.TcpSessionFactory;
import java.util.UUID;
import nl.tudelft.opencraft.yardstick.Options;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ConnectException;
import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.statistic.Statistics;
import nl.tudelft.opencraft.yardstick.util.Scheduler;
import nl.tudelft.opencraft.yardstick.workload.WorkloadDumper;
import nl.tudelft.opencraft.yardstick.workload.WorkloadSessionListener;

/**
 * A runnable Yardstick experiment.
 */
public abstract class Experiment implements Runnable {

    public static final long TICK_MS = 50;
    //
    protected final int number;
    protected final String description;
    protected final Options options = Yardstick.OPTIONS;
    protected final SubLogger logger;

    protected long tick = 0;
    private Statistics stats;
    private WorkloadDumper dumper;

    /**
     * Creates a new experiment.
     *
     * @param number The experiment number. Must be unique globally.
     * @param desc   A human-friendly description of the experiment.
     */
    public Experiment(int number, String desc) {
        this.number = number;
        this.description = desc;
        this.logger = GlobalLogger.getLogger().newSubLogger("Experiment " + number);
    }

    /**
     * Runs the experiment. The experiment will use the {@link WorkLoadDumper}
     * and {@link Statistics} if they have been set. A new scheduler will be
     * created to handle tick tasks for this experiment, such as model
     * interaction.
     */
    @Override
    public void run() {
        logger.info("Running: experiment " + number + " - " + description);

        for (String key : options.experimentParams.keySet()) {
            logger.info("Parameter - " + key + ": " + options.experimentParams.get(key));
        }

        if (dumper != null) {
            dumper.start();
        }

        if (stats != null) {
            stats.start();
        }

        try {
            Scheduler sched = new Scheduler(TICK_MS);
            sched.start();
            before();
            do {
                long beforeTick = System.nanoTime();
                tick();
                sched.sleepTick();
                long afterTick = System.nanoTime();

                if (afterTick - beforeTick > 51_000_000) { // 51 ms response time
                    break;
                }
                
            } while (!isDone());
            after();
            logger.info("Experiment complete, exiting");
        } finally {
            if (dumper != null) {
                dumper.stop();
            }

            if (stats != null) {
                stats.stop();
            }
        }
        System.out.println("Goodbye.");
        System.exit(0);
    }

    /**
     * Returns statistics for this experiment.
     */
    public Statistics getStats() {
        return stats;
    }

    /**
     * Sets the statistics for this experiment.
     *
     * @param stats the statics.
     */
    public void setStats(Statistics stats) {
        this.stats = stats;
    }

    /**
     * Returns the workload dumper for this experiment.
     *
     * @return the dumper.
     */
    public WorkloadDumper getWorkloadDumper() {
        return dumper;
    }

    /**
     * Sets the workload dumper for this experiment.
     *
     * @param dumper the workload dumper.
     */
    public void setWorkloadDumper(WorkloadDumper dumper) {
        this.dumper = dumper;
    }

    /**
     * Creates a new {@link Client} in this experiment. If a {@link Statistics}
     * has been set, the statistics will listen to client events. If a
     * {@link WorkloadDumper} has been set, the dumper will dump client
     * messages.
     *
     * @param name the client name.
     * @return the client.
     */
    protected Client newClient(String name) {
        Client client = new Client(options.host, options.port, new MinecraftProtocol(name), new TcpSessionFactory(true));
        setupClient(client, name);
        return client;
    }

    /**
     * Creates a new {@link Bot} in this experiment. If a {@link Statistics} has
     * been set, the statistics will listen to bot events. If a
     * {@link WorkloadDumper} has been set, the dumper will dump bot messages.
     *
     * @param name the client name.
     * @return the client.
     */
    protected Bot newBot(String name) {
        Bot bot = new Bot(new MinecraftProtocol(name), options.host, options.port);
        setupClient(bot.getClient(), name);
        return bot;
    }

    private void setupClient(Client client, String name) {
        Session s = client.getSession();

        // Logger
        s.addListener(new LoggerSessionListener(logger.newSubLogger(name)));

        // Statistics
        if (stats != null) {
            s.addListener(stats);
        }

        // Workload session listener
        if (dumper != null) {
            s.addListener(new WorkloadSessionListener(dumper, name));
        }
    }

    /**
     * Called before the experiment starts.
     */
    protected abstract void before();

    /**
     * Called during a bot tick.
     */
    protected abstract void tick();

    protected Bot createBot() throws ConnectException {
        Bot bot = newBot(UUID.randomUUID().toString().substring(0, 6));
        bot.connect();
        int sleep = 1000;
        int tries = 10;
        while (tries-- > 0 && !bot.isJoined()) {
            try {
                Thread.sleep(sleep);
            } catch (InterruptedException e) {
                e.printStackTrace();
                break;
            }
        }
        if (!bot.isJoined()) {
            bot.disconnect("Make sure to close all connections.");
            throw new ConnectException();
        }
        return bot;
    }

    /**
     * Should return true when the experiment is complete.
     *
     * @return true if complete.
     */
    protected abstract boolean isDone();

    /**
     * Called after the experiment has completed.
     */
    protected abstract void after();

}
