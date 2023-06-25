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

import com.google.common.base.Preconditions;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import science.atlarge.opencraft.mcprotocollib.data.game.chunk.BlockStorage;
import science.atlarge.opencraft.mcprotocollib.data.game.chunk.Column;
import science.atlarge.opencraft.mcprotocollib.data.game.world.block.BlockState;

import java.util.Objects;

public class Block {

    private final Logger logger = LoggerFactory.getLogger(Block.class);
    private final int x, y, z;
    private final Chunk chunk;

    public Block(int x, int y, int z, Chunk chunk) {
        Preconditions.checkArgument(y >= 0, "Argument was %s but expected nonnegative", y);
        Preconditions.checkArgument(y < 256, "Argument was %s but expected lower than 256", y);
        Preconditions.checkArgument(chunk != null);
        this.x = x;
        this.y = y;
        this.z = z;
        this.chunk = chunk;
    }

    public int getX() {
        return x;
    }

    public int getY() {
        return y;
    }

    public int getZ() {
        return z;
    }

    public Vector3i getLocation() {
        return new Vector3i(x, y, z);
    }

    public Chunk getChunk() {
        return chunk;
    }

    public World getWorld() {
        return chunk.getWorld();
    }

    public Block getRelative(BlockFace face) throws ChunkNotLoadedException {
        return getWorld().getBlockAt(getLocation().add(face.getOffset()));
    }

    public int getTypeId() {
        return getInternalState().getId();
    }

    public void setTypeId(int newType) {
        setInternalState(new BlockState(newType, getData()));
    }

    public int getData() {
        return getInternalState().getData();
    }

    public void setData(byte newData) {
        setInternalState(new BlockState(getTypeId(), newData));
    }

    public void setTypeIdAndData(int newType, byte newData) {
        setInternalState(new BlockState(newType, newData));
    }

    public void setInternalState(BlockState newState) {
        int locX = Math.floorMod(x, 16);
        int locY = Math.floorMod(y, 16);
        int locZ = Math.floorMod(z, 16);
        //GlobalLogger.getLogger().info("Set internal state: (" + x + "," + y + "," + z + ") -> (" + locX + "," + locY + "," + locZ + ")");

        getInternalStorage().set(
                locX,
                locY,
                locZ,
                newState);
    }

    public Material getMaterial() {
        return Material.getById(this.getTypeId());
    }

    public Block getRelative(int x, int y, int z) throws ChunkNotLoadedException {
        return getWorld().getBlockAt(this.x + x, this.y + y, this.z + z);
    }

    public Block getRelative(Vector3i offset) throws ChunkNotLoadedException {
        return getRelative(offset.getX(), offset.getY(), offset.getZ());
    }

    private BlockStorage getInternalStorage() {
        Column handle = chunk.getHandle();

        // TODO: Test this
        int index = Math.floorDiv(y, 16);
        //GlobalLogger.getLogger().info("Get Internal Storage - y: " + y + ", index: " + index);
        if (index > 15) {
            logger.warn("How did this happen: ({},{},{})", x, y, z);
        }

        science.atlarge.opencraft.mcprotocollib.data.game.chunk.Chunk[] sections = handle.getChunks();

        if (sections[index] == null) {
            //GlobalLogger.getLogger().info("Making new chunk section for air chunk section: (" + handle.getX() + "," + index + "," + handle.getZ() + ")");
            sections[index] = new science.atlarge.opencraft.mcprotocollib.data.game.chunk.Chunk(handle.hasSkylight());
        }

        return sections[index].getBlocks();

    }

    private BlockState getInternalState() {
        int locX = Math.floorMod(x, 16);
        int locY = Math.floorMod(y, 16);
        int locZ = Math.floorMod(z, 16);
        //GlobalLogger.getLogger().info("Get internal state: (" + x + "," + y + "," + z + ") -> (" + locX + "," + locY + "," + locZ + ")");

        return getInternalStorage().get(
                locX,
                locY,
                locZ);
    }

    @Override
    public int hashCode() {
        int hash = 7;
        return hash;
    }

    @Override
    public boolean equals(Object obj) {
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        final Block other = (Block) obj;
        if (this.x != other.x) {
            return false;
        }
        if (this.y != other.y) {
            return false;
        }
        if (this.z != other.z) {
            return false;
        }
        if (!Objects.equals(this.chunk, other.chunk)) {
            return false;
        }
        return true;
    }

}
