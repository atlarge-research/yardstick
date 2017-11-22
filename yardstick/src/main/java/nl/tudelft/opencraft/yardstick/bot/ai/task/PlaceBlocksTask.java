package nl.tudelft.opencraft.yardstick.bot.ai.task;

import java.util.Iterator;
import java.util.List;
import com.beust.jcommander.internal.Lists;
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

        Block target = getTargetBlock(toPlace);
        if (target == null) {
            logger.warning("No attached block found: " + location);
            return onTick();
        }

        Vector3d hit = raytrace(bot.getPlayer().getEyeLocation(), target);

        // TODO: interface with BotController
        // TODO: get item into inventory
        return TaskStatus.forInProgress();
    }

    @Override
    protected void onStop() {
    }

    private Block getTargetBlock(Block toPlace) {
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

            // We've found a block
            return placeAt;
        }

        return null;
    }

    private Vector3d raytrace(Vector3d from, Block block) {
        return null; // TODO: implement raytracing
    }

}
