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

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.world.ConnectException;
import nl.tudelft.opencraft.yardstick.model.BoundingBoxMovementModel;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

// TODO remove this class once we have a good BotModel interface.
public class Experiment9PlayerScalability extends Experiment {

    private final List<Bot> botList = Collections.synchronizedList(new ArrayList<>());
    private BoundingBoxMovementModel movement;

    private int botsTotal = 0;
    private long startMillis;
    private int durationInSeconds;
    private int secondsBetweenJoin;
    private int numberOfBotsPerJoin;
    private final Map<Bot, Vector3d> botSpawnLocations = new HashMap<>();
    private long lastJoin = System.currentTimeMillis();

    public Experiment9PlayerScalability() {
        super(4, "Gradually increase the number of players up to the point where a latency of 50ms cannot be achieved.");
    }

    @Override
    protected void before() {
        this.botsTotal = Integer.parseInt(options.experimentParams.get("bots"));
        this.durationInSeconds = Integer.parseInt(options.experimentParams.getOrDefault("duration", "600"));
        this.secondsBetweenJoin = Integer.parseInt(options.experimentParams.getOrDefault("joininterval", "1"));
        this.numberOfBotsPerJoin = Integer.parseInt(options.experimentParams.getOrDefault("numbotsperjoin", "1"));
        this.movement = new BoundingBoxMovementModel(
            Integer.parseInt(options.experimentParams.getOrDefault("boxDiameter", "32")),
            Boolean.parseBoolean(options.experimentParams.getOrDefault("spawnAnchor", "false"))
        );
        this.startMillis = System.currentTimeMillis();
    }

    @Override
    protected void tick() {
        synchronized (botList) {
            List<Bot> disconnectedBots = botList.stream()
                .filter(bot -> !bot.isJoined())
                .collect(Collectors.toList());
            disconnectedBots.forEach(bot -> bot.disconnect("Bot is not connected"));
            botList.removeAll(disconnectedBots);
        }
        if (System.currentTimeMillis() - this.lastJoin > secondsBetweenJoin * 1000
            && botList.size() <= this.botsTotal) {
            lastJoin = System.currentTimeMillis();
            int botsToConnect = Math.min(this.numberOfBotsPerJoin, this.botsTotal - botList.size());
            for (int i = 0; i < botsToConnect; i++) {
                new Thread(() -> {
                    long startTime = System.currentTimeMillis();
                    try {
                        Bot bot = createBot();
                        botSpawnLocations.put(bot, bot.getPlayer().getLocation());
                        botList.add(bot);
                    } catch (ConnectException e) {
                        logger.warning(String.format("Could not connect bot on %s:%d after %d ms.", options.host, options.port, System.currentTimeMillis() - startTime));
                    }
                }).start();
            }
        }
        synchronized (botList) {
            for (Bot bot : botList) {
                botTick(bot);
            }
        }
    }

    private void botTick(Bot bot) {
        TaskExecutor t = bot.getTaskExecutor();
        if (t == null || t.getStatus().getType() != TaskStatus.StatusType.IN_PROGRESS) {
            Vector3i newLocation = movement.newTargetLocation(bot);
            bot.getLogger().info(String.format("Setting task for bot to walk to %s", newLocation));
            bot.setTaskExecutor(new WalkTaskExecutor(bot, newLocation));
        }
    }

    @Override
    protected boolean isDone() {
        return false;
    }

    @Override
    protected void after() {
        for (Bot bot : botList) {
            bot.disconnect("disconnect");
        }
    }
}
