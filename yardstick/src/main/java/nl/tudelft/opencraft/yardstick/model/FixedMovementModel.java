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

import com.github.steveice10.mc.protocol.data.game.entity.metadata.Position;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import nl.tudelft.opencraft.yardstick.util.ZigZagRange;

import java.util.Random;

/**
 * Finds a target location in a fixed direction with minor fuzzing
 */
public class FixedMovementModel implements BotModel {

    private final int step_size = 4;
    private Random RANDOM;

    public FixedMovementModel(int seed) {
        this.RANDOM = new Random(seed);
    }

    public Vector3i newTargetLocation(Bot bot, Vector3d direction) {
        int curr_step_size = step_size;

        int step_size_min = (step_size/2);
        int step_size_max = (int) (step_size*1.5);

        int x_offset = 0;
        int y_offset = 0;

        // Step size fuzz
        if(this.RANDOM.nextFloat() <= 0.5){
            curr_step_size *=  step_size_min + (this.RANDOM.nextFloat()) * (step_size_max - step_size_min);
        }

        // Direction fuzz x
        if(this.RANDOM.nextFloat() <= 0.1){
            x_offset = -2 + this.RANDOM.nextInt(4);
        }
        // Direction fuzz y
        if(this.RANDOM.nextFloat() <= 0.1){
            y_offset = -2 + this.RANDOM.nextInt(4);
        }

        int x = (int) (bot.getPlayer().getLocation().getX() + (direction.getX() * curr_step_size)) + x_offset;
        int z = (int) (bot.getPlayer().getLocation().getZ() + (direction.getZ() * curr_step_size)) + y_offset;

        return getTargetAt(bot, x, z);
    }

    private Vector3i getTargetAt(Bot bot, int x, int z) {
        Vector3d botLoc = bot.getPlayer().getLocation();

        int y = -1;
        try {
            for (ZigZagRange it = new ZigZagRange(0, 255, (int) botLoc.getY()); it.hasNext(); ) {
                y = it.next();
                Block test = bot.getWorld().getBlockAt(x, y, z);
                if (test.getTraversable()
                        && !test.getRelative(BlockFace.BOTTOM).getTraversable()) {
                    break;
                }
            }

            if (y < 0 || y > 255) {
                return botLoc.intVector();
            }

            return new Vector3i(x, y, z);
        } catch (ChunkNotLoadedException ex) {
            bot.getLogger().warning("Bot target not loaded: (" + x + "," + y + "," + z + ")");
            return botLoc.intVector();
        }
    }


    @Override
    public TaskExecutor newTask(Bot bot) {
        return null;
    }
}
