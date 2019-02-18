package nl.tudelft.opencraft.yardstick.bot.ai.task;

import java.util.Iterator;
import java.util.List;
import com.beust.jcommander.internal.Lists;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.BotController;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.util.WorldUtil;

/**
 * Represents a task for breaking blocks.
 */
public class BreakBlocksTask extends AbstractTask {

    private final Iterator<Block> blocks;
    //
    private Block current = null;
    private int state = 0;
    private BlockFace face;

    /**
     * Creates a new BreakBlocksTask. The blocks must be in reach and visible to
     * the bot.
     *
     * @param bot the bot of the task.
     * @param blocks the blocks that must be broken.
     */
    public BreakBlocksTask(Bot bot, List<Block> blocks) {
        super(bot);
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
    }

    @Override
    protected TaskStatus onTick() {
        if (current == null && !blocks.hasNext()) {
            return TaskStatus.forSuccess();
        }

        // Get the next block
        if (current == null) {
            current = blocks.next();
            state = 0;

            // Find a block face
            face = WorldUtil.getVisibleBlockFace(bot.getPlayer(), current);
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
    protected void onStop() {
    }

}
