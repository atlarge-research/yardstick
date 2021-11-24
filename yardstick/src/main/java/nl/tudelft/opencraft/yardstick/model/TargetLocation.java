package nl.tudelft.opencraft.yardstick.model;

import java.text.MessageFormat;
import java.util.Random;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector2i;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import nl.tudelft.opencraft.yardstick.util.ZigZagRange;

public class TargetLocation {

    private static final Random random = new Random();

    /**
     * Function to make bot walk in a specific area.
     *
     * @return New random location in a field that has the original location at
     * its center.
     */
    public Vector3i newTargetLocation(Vector2i center, int diameter, Bot bot) {
        int radius = diameter / 2;
        int maxx = center.getX() + radius;
        int minx = center.getX() - radius;
        int maxz = center.getZ() + radius;
        int minz = center.getZ() - radius;

        int newX = (int) (Math.floor(random.nextInt(maxx - minx) + minx) + 0.5);
        int newZ = (int) (Math.floor(random.nextInt(maxz - minz) + minz) + 0.5);

        return getTargetAt(bot, newX, newZ);
    }

    // TODO make sure this also uses the getStartingLoc Function
    // TODO remove bot from param list
    private Vector3i getTargetAt(Bot bot, int x, int z) {
        Vector3d botLoc = bot.getPlayer().getLocation();

        int y = -1;
        try {
            for (ZigZagRange it = new ZigZagRange(0, 255, (int) botLoc.getY()); it.hasNext(); ) {
                y = it.next();
                Block test = bot.getWorld().getBlockAt(x, y, z);
                if (test.getMaterial().isTraversable()
                        && !test.getRelative(BlockFace.BOTTOM).getMaterial().isTraversable()) {
                    break;
                }
            }

            if (y < 0 || y > 255) {
                return botLoc.intVector();
            }

            return new Vector3i(x, y, z);
        } catch (ChunkNotLoadedException ex) {
            bot.getLogger().warning(MessageFormat.format("Bot target not loaded: ({0},{1},{2})", x, y, z));
            return botLoc.intVector();
        }
    }
}
