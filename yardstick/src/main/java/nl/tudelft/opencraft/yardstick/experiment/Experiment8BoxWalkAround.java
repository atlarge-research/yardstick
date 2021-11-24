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
import java.time.Duration;
import java.util.List;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import nl.tudelft.opencraft.yardstick.Yardstick;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.BotManager;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskStatus;
import nl.tudelft.opencraft.yardstick.game.GameArchitecture;
import nl.tudelft.opencraft.yardstick.model.box.BoundingBoxMovementBuilder;
import nl.tudelft.opencraft.yardstick.model.box.BoundingBoxMovementModel;

// TODO remove this class once we have a good BotModel interface.
public class Experiment8BoxWalkAround extends Experiment {

    private final Config behaviorConfig;

    private BoundingBoxMovementModel movement;

    private long startMillis;
    private Duration experimentDuration;
    private Duration timeBetweenJoins;
    private int numberOfBotsPerJoin;
    private long lastJoin = System.currentTimeMillis();
    private BotManager botManager;
    private ScheduledFuture<?> runningBotManager;

    public Experiment8BoxWalkAround(int nodeID, GameArchitecture game, Config behaviorConfig) {
        super(4, nodeID, game, "Bots walking around based on a movement model for Second Life.");
        this.behaviorConfig = behaviorConfig;
    }

    @Override
    protected void before() {
        this.experimentDuration = behaviorConfig.getDuration("duration");
        int botsTotal = behaviorConfig.getInt("bots");
        this.timeBetweenJoins = behaviorConfig.getDuration("joininterval");
        this.numberOfBotsPerJoin = behaviorConfig.getInt("numbotsperjoin");
        this.movement = new BoundingBoxMovementBuilder().fromConfig(behaviorConfig.getConfig("box"));
        this.startMillis = System.currentTimeMillis();

        botManager = new BotManager(game);
        botManager.setPlayerStepIncrease(numberOfBotsPerJoin);
        botManager.setPlayerCountTarget(botsTotal);
        runningBotManager = Yardstick.THREAD_POOL.scheduleAtFixedRate(botManager, 0, timeBetweenJoins.getSeconds(),
                TimeUnit.SECONDS);
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
            bot.setTaskExecutor(movement.newTask(bot));
        }
    }

    @Override
    protected boolean isDone() {
        return System.currentTimeMillis() - this.startMillis > this.experimentDuration.toMillis();
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
