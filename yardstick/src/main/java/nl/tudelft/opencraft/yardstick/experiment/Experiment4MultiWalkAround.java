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

import com.typesafe.config.Config;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.world.ConnectException;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;
import nl.tudelft.opencraft.yardstick.model.SimpleMovementModel;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Future;
import java.util.stream.Collectors;

public class Experiment4MultiWalkAround extends Experiment {

    private final Logger logger = LoggerFactory.getLogger(Experiment4MultiWalkAround.class);
    private final Config behaviorConfig;
    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());
    private final List<Future<Bot>> connectingBots = new ArrayList<>();
    private SimpleMovementModel movement;

    private int botsTotal = 0;
    private long startMillis;
    private Duration experimentDuration;
    private Duration timeBetweenJoins;
    private int numberOfBotsPerJoin;
    private final Map<Bot, Vector3d> botSpawnLocations = new HashMap<>();
    private long lastJoin = System.currentTimeMillis();

    public Experiment4MultiWalkAround(int nodeID, GameArchitecture game, Config behaviorConfig) {
        super(4, nodeID, game, "Bots walking around based on a movement model for Second Life.");
        this.behaviorConfig = behaviorConfig;
    }

    public Experiment4MultiWalkAround(int experimentID, int nodeID, GameArchitecture game,
            Config behaviorConfig, String desc) {
        super(experimentID, nodeID, game, desc);
        this.behaviorConfig = behaviorConfig;
    }

    @Override
    protected void before() {
        this.botsTotal = behaviorConfig.getInt("bots");
        this.experimentDuration = behaviorConfig.getDuration("duration");
        this.timeBetweenJoins = behaviorConfig.getDuration("joininterval");
        this.numberOfBotsPerJoin = behaviorConfig.getInt("numbotsperjoin");
        this.movement = new SimpleMovementModel(
                behaviorConfig.getInt("boxDiameter"),
                behaviorConfig.getBoolean("spawnAnchor")
        );
        this.startMillis = System.currentTimeMillis();
    }

    @Override
    protected void tick() {
        synchronized (botList) {
            // Remove all bots that are not connected.
            List<Bot> disconnectedBots = botList.stream()
                    .filter(bot -> !bot.isJoined())
                    .collect(Collectors.toList());
            disconnectedBots.forEach(bot -> bot.disconnect("Bot is not connected"));
            botList.removeAll(disconnectedBots);

            // Add all new bots that are connected.
            List<Future<Bot>> newlyConnectedBots = connectingBots.stream()
                    .filter(Future::isDone)
                    .collect(Collectors.toList());
            newlyConnectedBots.forEach(fb -> {
                connectingBots.remove(fb);
                try {
                    botList.add(fb.get());
                } catch (InterruptedException | ExecutionException e) {
                    // ignore
                }
            });
        }
        if (System.currentTimeMillis() - this.lastJoin > timeBetweenJoins.toMillis() * 1000
                && botList.size() <= this.botsTotal) {
            int botsToConnect = Math.min(this.numberOfBotsPerJoin, this.botsTotal - currentNumberOfBots());
            for (int i = 0; i < botsToConnect; i++) {
                connectNewBot();
            }
        }
        synchronized (botList) {
            for (Bot bot : botList) {
                botTick(bot);
            }
        }
    }

    void connectNewBot() {
        connectingBots.add(CompletableFuture.supplyAsync(() -> {
            long startTime = System.currentTimeMillis();
            try {
                Bot bot = createBot();
                botSpawnLocations.put(bot, bot.getPlayer().getLocation());
                return bot;
            } catch (ConnectException | InterruptedException e) {
                logger.warn("Could not connect bot after {} ms.",
                        System.currentTimeMillis() - startTime);
            }
            return null;
        }));
        lastJoin = System.currentTimeMillis();
    }

    private void botTick(Bot bot) {
        TaskExecutor t = bot.getTaskExecutor();
        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            Vector3i newLocation = movement.newTargetLocation(bot);
            logger.info("Setting task for bot to walk to {}", newLocation);
            bot.setTaskExecutor(new WalkTaskExecutor(bot, newLocation));
        }
    }

    @Override
    protected boolean isDone() {

        boolean timeUp = System.currentTimeMillis() - this.startMillis > this.experimentDuration.toMillis();
        if (timeUp) {
            return true;
        } else if (botList.size() > 0) {
            boolean allBotsDisconnected;
            synchronized (botList) {
                allBotsDisconnected = botList.stream().noneMatch(Bot::isJoined);
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

    public long getStartMillis() {
        return startMillis;
    }

    public int getBotsTotal() {
        return botsTotal;
    }

    public int currentNumberOfBots() {
        return botList.size() + connectingBots.size();
    }

    public long getLastJoined() {
        return lastJoin;
    }

    public int joinIntervalInSeconds() {
        return (int) timeBetweenJoins.getSeconds();
    }

    public int getBotsPerJoin() {
        return numberOfBotsPerJoin;
    }

    public void disconnectBots(int num, String reason) {
        for (int i = 0; i < Math.min(num, botList.size()); i++) {
            botList.get(i).disconnect(reason);
        }
    }
}
