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

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;
import nl.tudelft.opencraft.yardstick.model.BotModel;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

public abstract class AbstractModelExperiment extends Experiment {

    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());
    private final BotModel model;

    private long startMillis;
    private final Duration experimentDuration;

    public AbstractModelExperiment(int experimentID, int nodeID, GameArchitecture game,
            Duration experimentDuration, String description,
            BotModel model) {
        super(experimentID, nodeID, game, description);
        this.model = model;
        this.experimentDuration = experimentDuration;
    }

    @Override
    protected void before() {
        this.startMillis = System.currentTimeMillis();
    }

    @Override
    protected void tick() {
        synchronized (botList) {
            List<Bot> disconnectedBots = botList.stream()
                    .filter(Bot::hasBeenDisconnected)
                    .collect(Collectors.toList());
            disconnectedBots.forEach(bot -> bot.disconnect("Bot is not connected"));
            if (disconnectedBots.size() > 0) {
                logger.warn("Bots disconnected: {}", disconnectedBots.stream().map(Bot::getName).reduce("", (a, b) -> a + ", " + b));
                botList.removeAll(disconnectedBots);
            }
        }

        synchronized (botList) {
            for (Bot bot : botList) {
                botTick(bot);
            }
        }
    }

    private void botTick(Bot bot) {
        if (!bot.isJoined()) {
            return;
        }

        TaskExecutor t = bot.getTaskExecutor();
        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            try {
                bot.setTaskExecutor(model.newTask(bot));
            } catch (ChunkNotLoadedException e) {
                logger.warn("could not set new task for bot {}: {}", bot.getName(), e.getMessage());
            }
        }
    }

    private Runnable newBotConnector(Bot bot) {
        return () -> {
            long start = System.currentTimeMillis();
            bot.connect();

            int sleep = 2000;
            int tries = 3;
            while (tries-- > 0 && (bot.getPlayer() == null || !bot.isJoined())) {
                try {
                    Thread.sleep(sleep);
                } catch (InterruptedException e) {
                    e.printStackTrace();
                    break;
                }
            }

            if (!bot.isJoined()) {
                String host = bot.getClient().getHost();
                int port = bot.getClient().getPort();
                logger.warn("Could not connect bot {}:{}.", host, port);
                bot.disconnect("Make sure to close all connections.");
                if (number == 10) {
                    Experiment10WalkStraight.currBotId -= Experiment10WalkStraight.clientCount;
                }
            }
        };
    }

    @Override
    protected Bot createBot() {
        return newBot(UUID.randomUUID().toString().substring(0, 6));
    }

    @Override
    protected boolean isDone() {
        boolean timeUp = System.currentTimeMillis() - this.startMillis > this.experimentDuration.toMillis();
        if (timeUp) {
            return true;
        } else if (botList.size() > 0) {
            boolean allBotsDisconnected;
            synchronized (botList) {
                allBotsDisconnected = botList.stream().allMatch(Bot::hasBeenDisconnected);
            }
            if (allBotsDisconnected) {
                return true;
            }
        }
        return false;
    }

    @Override
    protected void after() {
        for (Bot bot : botList) {
            bot.disconnect("disconnect");
        }
    }

    public BotModel getModel() {
        return model;
    }
}
