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

import java.util.Random;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector2i;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class RandomSquareWalkXZTask implements Task {

    private final Logger logger = LoggerFactory.getLogger(RandomSquareWalkXZTask.class);

    private Vector2i center;
    private int radius;

    public Vector2i getCenter() {
        return center;
    }

    public void setCenter(Vector2i center) {
        this.center = center;
    }

    public int getRadius() {
        return radius;
    }

    public void setRadius(int radius) {
        this.radius = radius;
    }

    @Override
    public TaskExecutor toExecutor(Bot bot) {
        Random random = new Random();
        int x = random.nextInt() % ((2 * radius) + 1) + center.getX();
        int z = random.nextInt() % ((2 * radius) + 1) + center.getZ();
        Vector2i v = new Vector2i(x, z);
        Vector3i target;
        try {
            target = v.getHighestWalkTarget(bot.getWorld());
        } catch (ChunkNotLoadedException e) {
            logger.warn(e.getMessage());
            target = bot.getPlayer().getLocation().intVector();
        }
        return new WalkTaskExecutor(bot, target);
    }
}
