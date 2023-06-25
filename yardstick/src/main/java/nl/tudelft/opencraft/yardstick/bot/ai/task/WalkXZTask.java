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

package nl.tudelft.opencraft.yardstick.bot.ai.task;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector2i;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class WalkXZTask implements Task {

    private final Logger logger = LoggerFactory.getLogger(WalkXZTask.class);
    private Vector2i target;

    public Vector2i getTarget() {
        return target;
    }

    public void setTarget(Vector2i target) {
        this.target = target;
    }

    @Override
    public TaskExecutor toExecutor(Bot bot) {
        try {
            return new WalkTaskExecutor(bot, target.getHighestWalkTarget(bot.getWorld()));
        } catch (ChunkNotLoadedException e) {
            logger.warn(e.getMessage());
            return new WalkTaskExecutor(bot, bot.getPlayer().getLocation().intVector());
        }
    }
}
