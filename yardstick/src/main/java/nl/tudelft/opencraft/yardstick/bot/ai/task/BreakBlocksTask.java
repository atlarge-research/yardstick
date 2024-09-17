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

import java.util.ArrayList;
import java.util.List;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class BreakBlocksTask implements Task {

    private List<Vector3i> blockLocations;

    public List<Vector3i> getBlockLocations() {
        return blockLocations;
    }

    public void setBlockLocations(List<Vector3i> blockLocations) {
        this.blockLocations = blockLocations;
    }

    @Override
    public TaskExecutor toExecutor(Bot bot) {
        List<Block> list = new ArrayList<>();
        for (Vector3i location : blockLocations) {
            Block blockAt = null;
            try {
                blockAt = bot.getWorld().getBlockAt(location);
                list.add(blockAt);
            } catch (ChunkNotLoadedException e) {
                // FIXME log
                e.printStackTrace();
            }
        }
        return new BreakBlocksTaskExecutor(bot, list);
    }
}
