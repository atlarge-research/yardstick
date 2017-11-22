package nl.tudelft.opencraft.yardstick.experiment;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.ThreadLocalRandom;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.BreakBlocksTask;
import nl.tudelft.opencraft.yardstick.bot.ai.task.Task;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTask;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class BotModel {

    private static final double INTERACT_TO_MOVEMENT = 1f / 3f;
    private static final int INTERACT_BLOCK_AMOUNT = 3;
    private static final int INTERACT_RADIUS = 1;
    //
    private final InteractionModel interact = new InteractionModel();
    private final MovementModel movement = new MovementModel();

    public Task nextTask(Bot bot) {
        Task task;
        if (Math.random() < INTERACT_TO_MOVEMENT) {
            // Interact
            List<Block> selection = selectBlocks(bot);
            if (selection.isEmpty()) {
                bot.getLogger().warning("Could not find breakable blocks!");
                return null;
            }

            task = new BreakBlocksTask(bot, selection);
        } else {
            // Movement
            Vector3i newLocation = movement.newTargetLocation(bot);
            task = new WalkTask(bot, newLocation);
        }

        bot.getLogger().info("Activating: " + task.getShortName());
        return task;
    }

    private static List<Block> selectBlocks(Bot bot) {
        List<Block> possibilities = new ArrayList<>();

        Block playerBlock;
        try {
            playerBlock = bot.getWorld().getBlockAt(bot.getPlayer().getLocation().intVector());
        } catch (ChunkNotLoadedException ex) {
            return possibilities;
        }

        int radius = INTERACT_RADIUS;
        for (int x = -radius; x <= radius; x++) {
            for (int y = -radius; y <= radius; y++) {
                for (int z = -radius; z <= radius; z++) {
                    // Can't break blocks under on in the player
                    if (x == 0 && z == 0 && y < 2) {
                        continue;
                    }

                    // Get the relative block
                    Block block;
                    try {
                        block = playerBlock.getRelative(x, y, z);
                    } catch (ChunkNotLoadedException ex) {
                        continue;
                    }

                    // Can't break AIR
                    if (block.getMaterial() == Material.AIR) {
                        continue;
                    }

                    int absX = Math.abs(x);
                    int absZ = Math.abs(z);

                    // Skip corners, we need to be able to see them to break them
                    // and implementing that logic is too complicated for now.
                    if (absX == 1 && absZ == 1) {
                        continue;
                    }

                    if (BreakBlocksTask.getVisibleBlockFace(bot.getPlayer(), block) != null) {
                        possibilities.add(block);
                    }
                }
            }
        }

        Collections.shuffle(possibilities, ThreadLocalRandom.current());
        int idx = Math.min(possibilities.size() - 1, INTERACT_BLOCK_AMOUNT - 1);
        return possibilities.subList(0, idx);
    }

}
