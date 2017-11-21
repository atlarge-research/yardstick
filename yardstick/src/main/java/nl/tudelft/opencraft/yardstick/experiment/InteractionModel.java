package nl.tudelft.opencraft.yardstick.experiment;

import java.util.Collections;
import java.util.List;
import java.util.Random;
import com.google.common.collect.Lists;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.bot.world.World;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class InteractionModel {

    private static final Random RANDOM = new Random(System.nanoTime());
    public static int BREAK_MAX = 5;
    public static int BREAK_MIN = 2;
    public static int BREAK_SEARCH_DISTANCE = 2;

    public List<Block> newBreakBlocks(Bot bot) {
        // Get all reachable blocks
        List<Block> b = reachable(bot);

        // Shuffle
        Collections.shuffle(b);

        // See how many we need
        int breakAmt = BREAK_MIN + RANDOM.nextInt(BREAK_MAX + 1);
        int lastIndex = Math.min(breakAmt, b.size());

        return b.subList(0, lastIndex);
    }

    private List<Block> reachable(Bot bot) {
        List<Block> blocks = Lists.newArrayList();

        Vector3i loc = bot.getPlayer().getLocation().intVector();
        World world = bot.getWorld();

        for (int x = -BREAK_SEARCH_DISTANCE; x <= BREAK_SEARCH_DISTANCE; x++) {
            for (int y = -BREAK_SEARCH_DISTANCE; y <= BREAK_SEARCH_DISTANCE; y++) {
                for (int z = -BREAK_SEARCH_DISTANCE; z <= BREAK_SEARCH_DISTANCE; z++) {

                    Vector3i loopLoc = loc.add(x, y, z);
                    if (loc.distance(loopLoc) > 4) {
                        // Don't break faraway blocks
                        continue;
                    }

                    if (x == 0 && z == 0 && y <= 0) {
                        // Don't break blocks under the player
                        continue;
                    }

                    Block b;
                    try {
                        b = world.getBlockAt(loopLoc);
                    } catch (ChunkNotLoadedException ex) {
                        continue;
                    }

                    if (b.getMaterial() == Material.AIR
                            || b.getMaterial() == Material.UNKNOWN
                            || b.getMaterial().isFluid()
                            || b.getMaterial().isIndestructable()) {
                        continue;
                    }

                    // TODO: Is there a block in the way?
                    blocks.add(b);
                }
            }
        }

        return blocks;
    }

}
