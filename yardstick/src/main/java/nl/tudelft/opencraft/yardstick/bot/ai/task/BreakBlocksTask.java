package nl.tudelft.opencraft.yardstick.bot.ai.task;

import java.util.Iterator;
import java.util.List;
import com.beust.jcommander.internal.Lists;
import nl.tudelft.opencraft.yardstick.bot.world.Block;

public class BreakBlocksTask implements Task {

    private final Iterator blocks;

    public BreakBlocksTask(List<Block> blocks) {
        this.blocks = Lists.newArrayList(blocks).iterator();
    }

    @Override
    public TaskStatus getStatus() {
        return blocks.hasNext() ? TaskStatus.forInProgress() : TaskStatus.forSuccess();
    }

    @Override
    public TaskStatus tick() {
    }

    @Override
    public void stop() {
    }

}
