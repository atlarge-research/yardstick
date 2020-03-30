package nl.tudelft.opencraft.yardstick.bot.ai.task;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

import java.util.ArrayList;
import java.util.List;

public class BreakBlocksTask implements Task {

    private List<Vector3i> blockLocations;

    public List<Vector3i> getBlockLocations() {
        return blockLocations;
    }

    public void setBlockLocations(List<Vector3i> blockLocations) {
        this.blockLocations = blockLocations;
    }

    @Override
    public TaskExecutor toExecutor(Bot bot) {
        List<Block> list = new ArrayList<>();
        for (Vector3i location : blockLocations) {
            Block blockAt = null;
            try {
                blockAt = bot.getWorld().getBlockAt(location);
                list.add(blockAt);
            } catch (ChunkNotLoadedException e) {
                // FIXME log
                e.printStackTrace();
            }
        }
        return new BreakBlocksTaskExecutor(bot, list);
    }
}
