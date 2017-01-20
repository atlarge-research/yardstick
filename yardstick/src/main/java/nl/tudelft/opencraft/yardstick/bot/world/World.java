package nl.tudelft.opencraft.yardstick.bot.world;

import java.util.Collection;
import java.util.HashMap;
import java.util.Map;
import nl.tudelft.opencraft.yardstick.bot.Vector3i;
import nl.tudelft.opencraft.yardstick.bot.entity.Entity;
import org.spacehq.mc.protocol.data.game.entity.metadata.Position;
import org.spacehq.mc.protocol.data.game.world.WorldType;

public class World {

    private final Dimension dimension;
    private final WorldType type;
    //
    private final Map<ChunkLocation, Chunk> chunks = new HashMap<>();
    private final Map<Integer, Entity> entities = new HashMap<>();
    private Position spawnPoint;

    public World(Dimension dimension, WorldType type) {
        this.dimension = dimension;
        this.type = type;
    }

    public Dimension getDimension() {
        return dimension;
    }

    public WorldType getType() {
        return type;
    }

    public Collection<Chunk> getChunks() {
        return chunks.values();
    }

    public void loadChunk(Chunk chunk) {
        chunks.put(new ChunkLocation(chunk.getX(), chunk.getZ()), chunk);
    }

    public void unloadChunk(Chunk chunk) {
        unloadChunk(chunk.getX(), chunk.getZ());
    }

    public void unloadChunk(int x, int z) {
        chunks.remove(new ChunkLocation(x, z));
    }
    
    public Block getBlockAt(Vector3i v) {
        return getBlockAt(v.getX(), v.getY(), v.getZ());
    }

    public Block getBlockAt(int x, int y, int z) {
        int chunkX = Math.floorDiv(x, 16);
        int chunkZ = Math.floorDiv(z, 16);

        Chunk chunk = chunks.get(new ChunkLocation(chunkX, chunkZ));
        if (chunk == null) {
            return null; // Block not loaded
        }

        return new Block(x, y, z, chunk);
    }

    public Collection<Entity> getVisibleEntities() {
        return entities.values();
    }

    public boolean isEntityLoaded(int id) {
        return entities.containsKey(id);
    }
    
    public void loadEntity(Entity entity) {
        entities.put(entity.getId(), entity);
    }

    public void unloadEntity(Entity entity) {
        unloadEntity(entity.getId());
    }

    public void unloadEntity(int id) {
        entities.remove(id);
    }

    public Entity getEntity(int id) {
        return entities.get(id);
    }

    public Position getSpawnPoint() {
        return spawnPoint;
    }

    public void setSpawnPoint(Position spawnPoint) {
        this.spawnPoint = spawnPoint;
    }

    public static class ChunkLocation {

        private final int x, z;

        public ChunkLocation(int x, int z) {
            this.x = 0;
            this.z = 0;
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
    }

}
