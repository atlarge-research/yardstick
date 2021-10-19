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

import java.util.List;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.BotManager;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.game.GameFactory;
import nl.tudelft.opencraft.yardstick.model.BoundingBoxMovementModel;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

// TODO remove this class once we have a good BotModel interface.
public class Experiment8BoxWalkAround extends Experiment {

    private BoundingBoxMovementModel movement;

    private long startMillis;
    private int durationInSeconds;
    private BotManager botManager;
    private ScheduledFuture<?> runningBotManager;

    public Experiment8BoxWalkAround() {
        super(4, "Bots walking around based on a movement model for Second Life.");
    }

    @Override
    protected void before() {
        int botsTotal = Integer.parseInt(options.experimentParams.get("bots"));
        this.durationInSeconds = Integer.parseInt(options.experimentParams.getOrDefault("duration", "600"));
        int secondsBetweenJoin = Integer.parseInt(options.experimentParams.getOrDefault("joininterval", "1"));
        int numberOfBotsPerJoin = Integer.parseInt(options.experimentParams.getOrDefault("numbotsperjoin", "1"));
        this.movement = new BoundingBoxMovementModel(
                Integer.parseInt(options.experimentParams.getOrDefault("boxDiameter", "32")),
                Boolean.parseBoolean(options.experimentParams.getOrDefault("spawnAnchor", "false"))
        );
        this.startMillis = System.currentTimeMillis();

        botManager = new BotManager(new GameFactory().getGame(options.host, options.port, options.gameParams));
        botManager.setPlayerStepIncrease(numberOfBotsPerJoin);
        botManager.setPlayerCountTarget(botsTotal);
        runningBotManager = Yardstick.THREAD_POOL.scheduleAtFixedRate(botManager, 0, secondsBetweenJoin, TimeUnit.SECONDS);
    }

    @Override
    protected void tick() {
        List<Bot> bots = botManager.getConnectedBots();
        synchronized (bots) {
            for (Bot bot : bots) {
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
        return System.currentTimeMillis() - this.startMillis > this.durationInSeconds * 1_000L;
    }

    @Override
    protected void after() {
        runningBotManager.cancel(false);
        List<Bot> botList = botManager.getConnectedBots();
        for (Bot bot : botList) {
            bot.disconnect("disconnect");
        }
    }
}
