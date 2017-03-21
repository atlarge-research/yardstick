package nl.tudelft.opencraft.yardstick.bot.world;

/**
 * Created by jesse on 1/30/17.
 */
public class ChunkLocation {

    private final int x, z;

    public ChunkLocation(int x, int z) {
        this.x = x;
        this.z = z;
    }

    public int getX() {
        return x;
    }

    public int getZ() {
        return z;
    }

    @Override
    public int hashCode() {
        int hash = 3;
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
        final ChunkLocation other = (ChunkLocation) obj;
        if (this.x != other.x) {
            return false;
        }
        if (this.z != other.z) {
            return false;
        }
        return true;
    }

    @Override
    public String toString() {
        return "ChunkLocation{" +
                "x=" + x +
                ", z=" + z +
                '}';
    }
}

