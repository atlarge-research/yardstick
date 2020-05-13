package nl.tudelft.opencraft.yardstick.bot.world;

import com.github.steveice10.mc.protocol.data.game.chunk.Chunk;
import com.github.steveice10.mc.protocol.data.game.world.block.BlockState;
import com.google.common.base.Preconditions;
import java.util.Objects;

import nl.tudelft.opencraft.yardstick.logging.GlobalLogger;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class Block {

    private final int x, y, z;
    private final Chunk chunk;
    private final World world;

    public Block(int x, int y, int z, Chunk chunk, World world) {
        Preconditions.checkArgument(y >= 0, "Argument was %s but expected nonnegative", y);
        Preconditions.checkArgument(y < 256, "Argument was %s but expected lower than 256", y);
        this.x = x;
        this.y = y;
        this.z = z;
        this.chunk = chunk;
        this.world = world;
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
        return world;
    }

    public Block getRelative(BlockFace face) throws ChunkNotLoadedException {
        return getWorld().getBlockAt(getLocation().add(face.getOffset()));
    }

    public int getTypeId() {
        return getInternalState().getId();
    }

    public void setTypeId(int newType) {
        setInternalState(new BlockState(newType));
    }

    private static int index(int x, int y, int z) {
        return y << 8 | z << 4 | x;
    }

    public void setInternalState(BlockState newState) {
        int locX = Math.floorMod(x, 16);
        int locY = Math.floorMod(y, 16);
        int locZ = Math.floorMod(z, 16);
        //GlobalLogger.getLogger().info("Set internal state: (" + x + "," + y + "," + z + ") -> (" + locX + "," + locY + "," + locZ + ")");

        chunk.set(locX, locY, locZ, newState);
    }

    public Material getMaterial() {
        return Material.getById(this.getTypeId());
    }

    public String getBlockMaterial(){
        return BlockMaterial.getMaterial(this.getTypeId());
    }

    public Block getRelative(int x, int y, int z) throws ChunkNotLoadedException {
        return getWorld().getBlockAt(this.x + x, this.y + y, this.z + z);
    }

    public Block getRelative(Vector3i offset) throws ChunkNotLoadedException {
        return getRelative(offset.getX(), offset.getY(), offset.getZ());
    }

    private BlockState getInternalState() {
        int locX = Math.floorMod(x, 16);
        int locY = Math.floorMod(y, 16);
        int locZ = Math.floorMod(z, 16);
        //GlobalLogger.getLogger().info("Get internal state: (" + x + "," + y + "," + z + ") -> (" + locX + "," + locY + "," + locZ + ")");

        return chunk.get(locX, locY, locZ);
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
