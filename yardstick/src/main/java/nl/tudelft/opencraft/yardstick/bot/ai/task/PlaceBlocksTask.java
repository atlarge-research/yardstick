package nl.tudelft.opencraft.yardstick.bot.ai.task;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

import java.util.List;

public class PlaceBlocksTask implements Task {

    private List<Vector3i> blockPositions;
    private Material material;

    public List<Vector3i> getBlockPositions() {
        return blockPositions;
    }

    public void setBlockPositions(List<Vector3i> blockPositions) {
        this.blockPositions = blockPositions;
    }

    public Material getMaterial() {
        return material;
    }

    public void setMaterial(Material material) {
        this.material = material;
    }

    @Override
    public TaskExecutor toExecutor(Bot bot) {
        return new PlaceBlocksTaskExecutor(bot, blockPositions, material);
    }
}
