package nl.tudelft.opencraft.yardstick.bot.world;

import science.atlarge.opencraft.mcprotocollib.data.game.chunk.Column;

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
