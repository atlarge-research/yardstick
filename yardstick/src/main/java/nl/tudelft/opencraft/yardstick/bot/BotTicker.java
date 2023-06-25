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

package nl.tudelft.opencraft.yardstick.bot;

import java.util.concurrent.atomic.AtomicBoolean;
import java.util.logging.Level;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.util.Scheduler;

/**
 * A runnable ticker for executing bot tasks for bots. The BotTicker
 * automatically executes the bot's current task.
 */
public class BotTicker implements Runnable {

    private final SubLogger logger;
    private final Bot bot;
    private final AtomicBoolean running = new AtomicBoolean(false);

    /**
     * Creates a new BotTicker.
     *
     * @param bot the bot.
     */
    public BotTicker(Bot bot) {
        this.bot = bot;
        this.logger = bot.getLogger().newSubLogger("BotTicker");
    }

    /**
     * Starts the BotTicker. The ticker starts in a new thread, which can be
     * stopped with {@link #stop()}.
     */
    public void start() {
        if (!running.compareAndSet(false, true)) {
            throw new IllegalStateException("Already ticking");
        }

        Thread t = new Thread(this);
        t.setName("YSBot Ticker " + bot.getName());
        t.start();
    }

    /**
     * Stops the BotTicker.
     */
    public void stop() {
        running.set(false);
    }

    @Override
    public void run() {
        Scheduler sched = new Scheduler(50); // 50ms per tick
        sched.start();

        while (running.get()) {
            if (bot.getTaskExecutor() != null
                    && bot.getTaskExecutor().getStatus().getType() == TaskStatus.StatusType.IN_PROGRESS) {
                TaskStatus status = bot.getTaskExecutor().tick();
                if (status.getType() == TaskStatus.StatusType.FAILURE) {

                    if (status.getThrowable() != null) {
                        logger.log(Level.FINE, "Task Failure: " + status.getMessage(), status.getThrowable());
                    } else {
                        logger.warning("Task Failure: " + status.getMessage());
                    }

                    bot.setTaskExecutor(null);
                }
            }
            sched.sleepTick();
        }
    }

}
