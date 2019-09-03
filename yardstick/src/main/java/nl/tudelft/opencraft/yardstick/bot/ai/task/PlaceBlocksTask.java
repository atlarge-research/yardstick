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
import nl.tudelft.opencraft.yardstick.playerbehavior.Vector3d;
import nl.tudelft.opencraft.yardstick.playerbehavior.Vector3i;
import nl.tudelft.opencraft.yardstick.util.WorldUtil;

/**
 * Represents a task to place blocks.
 */
public class PlaceBlocksTask extends AbstractTask {

    private final Material material;
    private final Iterator<Vector3i> locations;
    private boolean inventoryAction = false;

    /**
     * Creates a new PlaceBlocksTask. The locations must be visible and
     * reachable to the bot.
     *
     * @param bot the bot for the task.
     * @param locations the locations at which to place blocks.
     * @param material the material type of the blocks.
     */
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
            bot.getController().creativeInventoryAction(material, 1);
            inventoryAction = true;
            return TaskStatus.forInProgress();
        }

        //logger.info("=== START BlockPlace ===");
        Vector3i placeAt = locations.next();

        Block toPlace;
        try {
            toPlace = bot.getWorld().getBlockAt(placeAt);
        } catch (ChunkNotLoadedException ex) {
            logger.warning("Could not get block: " + placeAt);
            return onTick();
        }

        if (toPlace.getMaterial() != Material.AIR) {
            logger.warning("Block not air: " + placeAt);
            return onTick();
        }

        Hitpoint hit = tryGetHitpoint(bot.getPlayer().getEyeLocation(), toPlace);
        if (hit == null) {
            logger.warning("Could not place block -- player: " + bot.getPlayer().getLocation() + ", block: " + placeAt);
            return onTick();
        }

        //logger.info("Placing -- block: " + placeAt + ", face: " + hit.face + ", hit: " + hit.hit + ", player: " + bot.getPlayer().getLocation());
        bot.getController().placeBlock(placeAt, hit.face, hit.hit);

        //logger.info("=== END BlockPlace ===");
        return TaskStatus.forInProgress();
    }

    @Override
    protected void onStop() {
    }

    private Hitpoint tryGetHitpoint(Vector3d from, Block placeAt) {
        BlockFace[] directed = WorldUtil.getDirectedBlockFaces(bot.getPlayer(), placeAt);

        // Invert all the faces to get the faces in the direction of the blocks we're actually targetting
        for (int i = 0; i < directed.length; i++) {
            // TODO: this doesn't seem right?
            //directed[i] = directed[i].getOpposite();
        }

        for (BlockFace placeFace : directed) {
            Block support;
            try {
                support = placeAt.getRelative(placeFace);
            } catch (ChunkNotLoadedException ex) {
                logger.warning("Could not get block: " + placeAt.getLocation().add(placeFace.getOffset()));
                continue;
            }

            if (support.getMaterial().isTraversable()) {
                // We can't place at this block
                //logger.info("Traversable: " + support.getLocation() + ", relative face: " + placeFace.name());
                continue;
            }

            // The face we will be intersecting with
            BlockFace supportFace = placeFace.getOpposite();

            // We've found a block/blockface combination
            Vector3d hitpoint = raytrace(from, support, supportFace);
            if (hitpoint == null) {
                // A block is obstructing
                //logger.info("  -> obstruction -- from: " + from + ", supporting: " + support.getLocation() + ", face: " + supportFace);
                continue;
            }

            // Calculation per http://wiki.vg/Protocol#Player_Block_Placement
            Vector3d relativeHitpoint = supportFace
                    .getOffset().doubleVector()
                    .multiply(0.5)
                    .add(0.5, 0.5, 0.5);

            // We've found a hit!
            Hitpoint hp = new Hitpoint();
            hp.hit = relativeHitpoint;
            hp.face = supportFace;
            return hp;
        }

        return null;
    }

    /**
     * Returns the hit point from a point to the center of a block face of a
     * block.
     *
     * @param from The viewpoint or origin of the ray trace.
     * @param support The block to ray trace to.
     * @param face The face of the block.
     * @return The hit point if the ray trace was successful, null if a
     * occluding block was found.
     */
    private Vector3d raytrace(Vector3d from, Block support, BlockFace face) {
        Vector3d toVector = support.getLocation()
                .doubleVector()
                .add(0.5, 0.5, 0.5)
                .add(face.getOffset().doubleVector().multiply(0.5));

        // We've got the destination, now find out if any blocks are in the way
        Set<Vector3i> intersections = cubeIntersections(from, toVector);
        for (Vector3i hit : intersections) {
            if (support.getLocation().equals(hit)) {
                // Intersection is the supporting block
                continue;
            }

            Block hitBlock;
            try {
                hitBlock = support.getWorld().getBlockAt(hit);
            } catch (ChunkNotLoadedException ex) {
                // If this ever throws, assume it's okay
                continue;
            }

            if (hitBlock.getMaterial() != Material.AIR) {
                // Something hit, we can't place here
                //logger.info("Raytrace hit: " + hitBlock.getLocation());
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
