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

package nl.tudelft.opencraft.yardstick.model.box;

import net.jodah.failsafe.Failsafe;
import net.jodah.failsafe.RetryPolicy;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.FutureTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.model.BotModel;

import java.time.temporal.ChronoUnit;

/**
 * Represents a model which moves the bot randomly to short and long distance
 * locations.
 */
public class BoundingBoxMovementModel implements BotModel {

    private final Box2D box;

    public BoundingBoxMovementModel(Box2D box) {
        this.box = box;
    }

    @Override
    public FutureTaskExecutor newTask(Bot bot) {
        var policy = new RetryPolicy<>()
                .withMaxAttempts(-1)
                .withBackoff(1, 16, ChronoUnit.SECONDS);
        var future = Failsafe.with(policy).getAsync(() -> new WalkTaskExecutor(bot, box.computeNewLocation(bot)));
        return new FutureTaskExecutor(future);
    }
}
