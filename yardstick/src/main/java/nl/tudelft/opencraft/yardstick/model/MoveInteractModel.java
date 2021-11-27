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

package nl.tudelft.opencraft.yardstick.model;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;

/**
 * Represents a model which moves and interacts with the environment.
 */
public class MoveInteractModel implements BotModel {

    private static final double INTERACT_TO_MOVEMENT = 1f / 2f;
    //
    private final BotModel interact = new SimpleInteractionModel();
    private final BotModel movement = new SimpleMovementModel();

    @Override
    public TaskExecutor newTask(Bot bot) throws ChunkNotLoadedException {
        TaskExecutor taskExecutor;
        if (Math.random() < INTERACT_TO_MOVEMENT) {
            // Interact
            taskExecutor = interact.newTask(bot);
        } else {
            // Movement
            taskExecutor = movement.newTask(bot);
        }

        return taskExecutor;
    }

}
