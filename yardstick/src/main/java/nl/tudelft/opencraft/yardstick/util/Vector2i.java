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

package nl.tudelft.opencraft.yardstick.util;

import com.fasterxml.jackson.annotation.JsonProperty;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.World;

public class Vector2i {
    private final int x;
    private final int z;

    public Vector2i(@JsonProperty("x") int x, @JsonProperty("z") int z) {
        this.x = x;
        this.z = z;
    }

    public Vector3i getHighestWalkTarget(World world) throws ChunkNotLoadedException {
        return new Vector3i(x, world.getHighestBlockAt(x, z).getY() + 1, z);
    }

    public int getX() {
        return x;
    }

    public int getZ() {
        return z;
    }
}
