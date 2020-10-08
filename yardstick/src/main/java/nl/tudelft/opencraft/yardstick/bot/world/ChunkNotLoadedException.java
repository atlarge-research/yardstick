package nl.tudelft.opencraft.yardstick.bot.world;

public class ChunkNotLoadedException extends Exception {

    public ChunkNotLoadedException(ChunkLocation l) {
        super("Chunk not loaded: (" + l.getX() + ", " + l.getZ() + ")");
    }
}
