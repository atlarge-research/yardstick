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

package nl.tudelft.opencraft.yardstick.bot.world;

import com.github.steveice10.mc.protocol.data.game.chunk.Column;

/**
 * Represents a vertical column of 16x16x16 chunks.
 */
public class Chunk {

    private final World world;
    private final ChunkLocation location;
    private final Column handle;

    public Chunk(World world, Column column) {
        this.world = world;
        this.handle = column;
        this.location = new ChunkLocation(column.getX(), column.getZ());

        // TODO: Tile entities, biome data
    }

    public Column getHandle() {
        return handle;
    }

    public World getWorld() {
        return world;
    }

    public ChunkLocation getLocation() {
        return this.location;
    }

    // TODO block operations
    @Override
    public int hashCode() {
        int hash = 7;
        return hash;
    }

    @Override
    public boolean equals(Object o) {
        if (this == o) {
            return true;
        }
        if (o == null || getClass() != o.getClass()) {
            return false;
        }

        Chunk chunk = (Chunk) o;

        if (!world.equals(chunk.world)) {
            return false;
        }
        if (!location.equals(chunk.location)) {
            return false;
        }
        return handle.equals(chunk.handle);
    }
}
