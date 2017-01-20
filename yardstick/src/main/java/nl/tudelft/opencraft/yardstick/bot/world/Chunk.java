package nl.tudelft.opencraft.yardstick.bot.world;

import java.util.Objects;
import org.spacehq.mc.protocol.data.game.chunk.Column;

/**
 * Represents a vertical column of 16x16x16 chunks.
 */
public class Chunk {

    private final World world;
    private final int x, z;
    private final Column column;

    public Chunk(World world, Column column) {
        this.world = world;
        this.x = column.getX();
        this.z = column.getZ();
        this.column = column;

        // TODO: Tile entities, biome data
    }

    public Column getHandle() {
        return column;
    }

    public World getWorld() {
        return world;
    }

    public int getX() {
        return x;
    }

    public int getZ() {
        return z;
    }

    // TODO block operations
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
        final Chunk other = (Chunk) obj;
        if (!Objects.equals(this.world, other.world)) {
            return false;
        }
        if (this.x != other.x) {
            return false;
        }
        if (this.z != other.z) {
            return false;
        }
        return true;
    }

}
