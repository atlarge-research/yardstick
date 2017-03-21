package nl.tudelft.opencraft.yardstick.bot.world;

import java.util.Objects;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import com.github.steveice10.mc.protocol.data.game.chunk.BlockStorage;
import com.github.steveice10.mc.protocol.data.game.chunk.Column;
import com.github.steveice10.mc.protocol.data.game.world.block.BlockState;

public class Block {

    private final int x, y, z;
    private final Chunk chunk;

    public Block(int x, int y, int z, Chunk chunk) {
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

    public Chunk getChunk() {
        return chunk;
    }

    public World getWorld() {
        return chunk.getWorld();
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
        Column handle = chunk.getColumn();

        // TODO: Test this
        int chunkIndex = Math.floorDiv(y, 16);
        //GlobalLogger.getLogger().info("Get Internal Storage - index: " + chunkIndex);

        com.github.steveice10.mc.protocol.data.game.chunk.Chunk[] c = handle.getChunks();

        if (c[chunkIndex] == null) {
            //GlobalLogger.getLogger().info("Making new chunk section for air chunk section: (" + chunk.getX() + "," + chunkIndex + "," + chunk.getZ() + ")");
            c[chunkIndex] = new com.github.steveice10.mc.protocol.data.game.chunk.Chunk(handle.hasSkylight());
        }

        return c[chunkIndex].getBlocks();

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
