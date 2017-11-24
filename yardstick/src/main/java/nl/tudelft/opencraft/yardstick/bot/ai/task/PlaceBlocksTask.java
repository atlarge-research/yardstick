package nl.tudelft.opencraft.yardstick.bot.ai.task;

import java.util.Iterator;
import java.util.List;
import java.util.Set;
import com.beust.jcommander.internal.Lists;
import com.beust.jcommander.internal.Sets;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import nl.tudelft.opencraft.yardstick.util.WorldUtil;

public class PlaceBlocksTask extends AbstractTask {

    private final Material material;
    private final Iterator<Vector3i> locations;
    private boolean inventoryAction = false;

    public PlaceBlocksTask(Bot bot, List<Vector3i> locations, Material material) {
        super(bot);
        this.locations = Lists.newArrayList(locations).iterator();
        this.material = material;
    }

    @Override
    protected TaskStatus onTick() {
        if (!locations.hasNext()) {
            return TaskStatus.forSuccess();
        }

        // Get the item in the inventory
        if (!inventoryAction) {
            bot.getController().creativeInventoryAction(Material.STONE, 1);
            inventoryAction = true;
            return TaskStatus.forInProgress();
        }

        Vector3i location = locations.next();

        Block toPlace;
        try {
            toPlace = bot.getWorld().getBlockAt(location);
        } catch (ChunkNotLoadedException ex) {
            logger.warning("Could not get block: " + location);
            return onTick();
        }

        if (toPlace.getMaterial() != Material.AIR) {
            logger.warning("Block not air: " + location);
            return onTick();
        }

        Hitpoint hit = tryGetHitpoint(bot.getPlayer().getEyeLocation(), toPlace);
        if (hit == null) {
            logger.warning("Could not place block. Block is obstructed: " + location);
            return onTick();
        }

        bot.getController().placeBlock(location, hit.face, hit.hit);

        return TaskStatus.forInProgress();
    }

    @Override
    protected void onStop() {
    }

    private Hitpoint tryGetHitpoint(Vector3d from, Block toPlace) {
        BlockFace[] directed = WorldUtil.getDirectedBlockFaces(bot.getPlayer(), toPlace);

        // Invert all the faces to get the faces in the direction of the blocks we're actually targetting
        for (int i = 0; i < directed.length; i++) {
            directed[i] = directed[i].getOpposite();
        }

        for (BlockFace face : directed) {
            Block placeAt;
            try {
                placeAt = toPlace.getRelative(face);
            } catch (ChunkNotLoadedException ex) {
                logger.warning("Could not get block: " + toPlace.getLocation().add(face.getOffset()));
                continue;
            }

            if (placeAt.getMaterial().isTraversable()) {
                // We can't place at this block
                continue;
            }

            // We've found a block/blockface combination
            Vector3d hitpoint = raytrace(from, placeAt, face);
            if (hitpoint == null) {
                // A block is obstructing
                continue;
            }

            // We've found a hit!
            Hitpoint hp = new Hitpoint();
            hp.hit = hitpoint;
            hp.face = face;
            return hp;
        }

        return null;
    }

    /**
     * Returns the hit point from a point to the center of a block face of a
     * block.
     *
     * @param from The viewpoint or origin of the ray trace.
     * @param target The block to ray trace to.
     * @param face The face of the block.
     * @return The hit point if
     */
    private Vector3d raytrace(Vector3d from, Block target, BlockFace face) {
        Vector3d toVector = target.getLocation()
                .doubleVector()
                .add(0.5, 0.5, 0.5)
                .add(face.getOffset().doubleVector().multiply(0.5));

        // We've got the destination, now find out if any blocks are in the way
        Set<Vector3i> intersections = cubeIntersections(from, toVector);
        for (Vector3i hit : intersections) {
            if (target.getLocation().equals(hit)) {
                continue;
            }

            if (from.distanceSquared(hit.doubleVector()) < 1.5) {
                continue;
            }

            Block hitBlock;
            try {
                hitBlock = target.getWorld().getBlockAt(hit);
            } catch (ChunkNotLoadedException ex) {
                // If this ever throws, assume it's okay
                continue;
            }

            if (hitBlock.getMaterial() != Material.AIR) {
                // Something hit, we can't place here
                return null;
            }
        }

        return toVector;
    }

    private Set<Vector3i> cubeIntersections(Vector3d begin, Vector3d end) {

        // TODO: improve algorithm to something workable
        Set<Vector3i> intersections = Sets.newHashSet();

        Vector3d step = end.subtract(begin).unit().multiply(0.1);
        Vector3d current = begin;

        while (current.distanceSquared(end) > 1) {
            intersections.add(current.intVector());
            current = current.add(step);
        }

        return intersections;
    }

    private class Hitpoint {

        public BlockFace face;
        public Vector3d hit;
    }

}
