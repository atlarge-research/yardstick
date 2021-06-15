/*
 * Yardstick: A Benchmark for Minecraft-like Services
 * Copyright (C) 2020 AtLarge Research
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Lesser General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public License
 * along with this program.  If not, see <https://www.gnu.org/licenses/>.
 */

package nl.tudelft.opencraft.yardstick.model;

import com.github.steveice10.mc.protocol.data.game.entity.metadata.Position;
import java.util.Random;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import nl.tudelft.opencraft.yardstick.util.ZigZagRange;

/**
 * Represents a model which moves the bot randomly to short and long distance
 * locations.
 */
public class SimpleMovementModel implements BotModel {


    private final boolean anchored;
    private Vector3d anchor;
    private final int boxDiameter;
    private Random RANDOM;
    private boolean first = true;
    private boolean bounded = true;


    public SimpleMovementModel() {
        anchored = false;
        boxDiameter = 32;
        this.RANDOM = new Random(System.nanoTime());
    }

    public SimpleMovementModel(int boxDiameter) {
        this.anchored = false;
        this.boxDiameter = boxDiameter;
        this.RANDOM = new Random(System.nanoTime());
    }

    public SimpleMovementModel(int boxDiameter, boolean spawnAnchor) {
        this.anchored = spawnAnchor;
        this.boxDiameter = boxDiameter;
        this.RANDOM = new Random(System.nanoTime());
    }

    public SimpleMovementModel(int boxDiameter, boolean spawnAnchor, int seed) {
        this.anchored = spawnAnchor;
        this.boxDiameter = boxDiameter;
        this.RANDOM = new Random(seed);
    }

    @Override
    public TaskExecutor newTask(Bot bot) {
        return new WalkTaskExecutor(bot, newTargetLocation(bot));
    }

    public Vector3i newTargetLocation(Bot bot) {
        if(bounded){
            return getNewFieldLocation(bot);
        }
        if (RANDOM.nextDouble() < 0.1) {
            return getNewLongDistanceTarget(bot);
        } else {
            return getNewFieldLocation(bot);
        }
    }

    /**
     * Function to make bot walk in a specific area.
     *
     * @return New random location in a field that has the original location at
     * its center.
     */
    Vector3i getNewFieldLocation(Bot bot) {
        Vector3d originalLocation = getStartLocation(bot);
        int maxx = ((int) originalLocation.getX()) + boxDiameter / 2;
        int minx = ((int) originalLocation.getX()) - boxDiameter / 2;
        int maxz = ((int) originalLocation.getZ()) + boxDiameter / 2;
        int minz = ((int) originalLocation.getZ()) - boxDiameter / 2;

        int newX = (int) (Math.floor(RANDOM.nextInt(maxx - minx) + minx) + 0.5);
        int newZ = (int) (Math.floor(RANDOM.nextInt(maxz - minz) + minz) + 0.5);

        return getTargetAt(bot, newX, newZ);
    }

    private Vector3d getStartLocation(Bot bot) {
        if(first){
            anchor = bot.getPlayer().getLocation();
            //bot.getLogger().info("Setting spawn to " + anchor.toString());
            first = false;
        }
        return anchor;
    }

    private Vector3i getNewLongDistanceTarget(Bot bot) {
        // TODO make param for this value.
        int maxDist = 64 * 5;
        int minDist = 64 * 1;
        int distance = RANDOM.nextInt(maxDist - minDist) + minDist;
        int angle = RANDOM.nextInt(360);

        Vector3d location = getStartLocation(bot);
        int newX = (int) (Math.floor(location.getX() + (distance * Math.cos(angle))) + 0.5);
        int newZ = (int) (Math.floor(location.getZ() + (distance * Math.sin(angle))) + 0.5);

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
                if (test.getTraversable()
                        && !test.getRelative(BlockFace.BOTTOM).getTraversable()) {
                    break;
                }
            }

            if (y < 0 || y > 255) {
                return botLoc.intVector();
            }

            return new Vector3i(x, y, z);
        } catch (ChunkNotLoadedException ex) {
            bot.getLogger().warning("Bot target not loaded: (" + x + "," + y + "," + z + ")");
            return botLoc.intVector();
        }
    }

}
