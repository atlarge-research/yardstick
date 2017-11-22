package nl.tudelft.opencraft.yardstick.bot.ai.task;

import java.util.Iterator;
import java.util.List;
import com.beust.jcommander.internal.Lists;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.BotController;
import nl.tudelft.opencraft.yardstick.bot.entity.Player;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.logging.SubLogger;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class BreakBlocksTask implements Task {

    private final String shortName;
    private final Bot bot;
    private final SubLogger logger;
    private final Iterator<Block> blocks;
    //
    private Block current = null;
    private int state = 0;
    private BlockFace face;

    public BreakBlocksTask(Bot bot, List<Block> blocks) {
        this.bot = bot;
        this.blocks = Lists.newArrayList(blocks).iterator();

        // Get a format like: BreakBlocksTask[(21,64,3), (21,65,4), (21,64,3)]
        StringBuilder sb = new StringBuilder("BreakBlocksTask[");
        if (blocks.size() > 0) {
            sb.append(blocks.get(0).getLocation().toString());
        }

        if (blocks.size() > 1) {
            for (int i = 1; i < blocks.size(); i++) {
                sb.append(", ").append(blocks.get(i).getLocation().toString());
            }
        }
        sb.append(']');

        this.shortName = sb.toString();
        this.logger = bot.getLogger().newSubLogger(shortName);
    }

    public String getShortName() {
        return shortName;
    }

    @Override
    public TaskStatus getStatus() {
        if (current != null) {
            return TaskStatus.forInProgress();
        }

        return blocks.hasNext() ? TaskStatus.forInProgress() : TaskStatus.forSuccess();
    }

    @Override
    public TaskStatus tick() {
        if (current == null && !blocks.hasNext()) {
            return TaskStatus.forSuccess();
        }

        // Get the next block
        if (current == null) {
            current = blocks.next();
            state = 0;

            // Find a block face
            face = getVisibleBlockFace(bot.getPlayer(), current);
            if (face == null) {
                logger.severe("Could not find block face for block: " + current.getLocation().toString());

                // Couldn't find one, next block
                current = null;
                return tick();
            }
        }

        switch (state++) {
            case 0: {
                bot.getController().updateDigging(current, face, BotController.DiggingState.STARTED_DIGGING);
                break;
            }
            case 1: {
                bot.getController().updateDigging(current, face, BotController.DiggingState.FINISHED_DIGGING);
                // We're done with this block
                current = null;
                break;
            }
        }

        return TaskStatus.forInProgress();
    }

    @Override
    public void stop() {

    }

    /**
     * Calculates and selects a visible block face the player can see for a
     * given block if such a face exists. This takes into account the
     * environment (block occlusion).
     *
     * @param player The player.
     * @param block The block the player is observing.
     * @return An arbitrary block face that is visible, or null, if none exists.
     */
    public static BlockFace getVisibleBlockFace(Player player, Block block) {
        BlockFace[] directed = getDirectedBlockFaces(player, block);

        for (int i = 0; i < directed.length; i++) {
            Block relative;
            try {
                relative = block.getRelative(directed[i]);
            } catch (ChunkNotLoadedException ex) {
                continue;
            }

            // Check if the adjacent block is AIR
            if (relative.getMaterial() == Material.AIR) {
                // We got it!
                return directed[i];
            }
        }

        // All block faces are occluded by another block
        return null;
    }

    /**
     * Geometrically calculates the three block faces (potentially) visible to a
     * player looking at a block from. This does not take into account the
     * distance (is the player inside the block, or is the block even rendered?)
     * and the surroundings (is there a block blocking the access to the face?).
     *
     * @param player The player.
     * @param block The block the player is observing.
     * @return An array of three block faces.
     */
    public static BlockFace[] getDirectedBlockFaces(Player player, Block block) {
        // Determine the block face
        Vector3d playerLoc = player.getLocation();
        Vector3d blockLoc = block.getLocation().doubleVector().add(0.5, 0.5, 0.5);

        // Calculate unit vector from the center of the block pointing at the player
        Vector3d diff = playerLoc.subtract(blockLoc).unit();

        // Now, the three faces are computed by rounding two components down, and one component up
        BlockFace[] faces = new BlockFace[3];

        int x = diff.getX() > 0 ? 1 : -1;
        faces[0] = BlockFace.forUnitVector(new Vector3i(x, 0, 0));
        int y = diff.getY() > 0 ? 1 : -1;
        faces[1] = BlockFace.forUnitVector(new Vector3i(0, y, 0));
        int z = diff.getY() > 0 ? 1 : -1;
        faces[2] = BlockFace.forUnitVector(new Vector3i(0, 0, z));

        return faces;
    }

}
