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

import java.util.Random;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.model.BotModel;

/**
 * Represents a model which moves the bot randomly to short and long distance
 * locations.
 */
public class BoundingBoxMovementModel implements BotModel {

    private static final Random RANDOM = new Random(System.nanoTime());
    private final Box2D box;

    public BoundingBoxMovementModel(Box2D box) {
        this.box = box;
    }

    @Override
    public TaskExecutor newTask(Bot bot) {
        return new WalkTaskExecutor(bot, box.computeNewLocation(bot));
    }
}
