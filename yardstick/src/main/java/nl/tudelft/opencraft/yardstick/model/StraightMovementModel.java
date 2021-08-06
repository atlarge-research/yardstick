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

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.task.TaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.ai.task.WalkTaskExecutor;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import nl.tudelft.opencraft.yardstick.util.ZigZagRange;

import java.util.HashMap;
import java.util.Random;

/**
 * Represents a model which moves the bot randomly to short and long distance
 * locations.
 */
public class StraightMovementModel implements BotModel {
    private Random random;
    public static HashMap<Bot, Vector3i> botsTarget = new HashMap<>();
    public double walkSpeed = 0.15;

    public StraightMovementModel() {
        this.random = new Random();
    }

    @Override
    public TaskExecutor newTask(Bot bot) {
        WalkTaskExecutor exe = new WalkTaskExecutor(bot, newTargetLocation(bot));
        if (walkSpeed != 0.15)
            exe.setSpeed(walkSpeed);
        return exe;
    }

    public Vector3i newTargetLocation(Bot bot) {
        Vector3d originalLocation = bot.getPlayer().getLocation();
        int dis = 16;

        int newX = (int) originalLocation.getX();
        int newZ = (int) originalLocation.getZ();

        int botId = Integer.parseInt(bot.getName().split("-")[1]);

        double factor = 0;
        if (botId > 7)
            factor = botId / 8.0;

        switch (botId % 8) {
            case 0:
                newX+=dis;
                newZ+=(int)factor*dis;
                break;
            case 1:
                newZ+=dis;
                newX+=(int)factor*dis;
                break;
            case 2:
                newX-=dis;
                newZ-=(int)factor*dis;
                break;
            case 3:
                newZ-=dis;
                newX-=(int)factor*dis;
                break;
            case 4:
                newX+=dis+(int)factor*dis;
                newZ+=dis+(int)factor*dis;
                break;
            case 5:
                newX-=dis-(int)factor*dis;
                newZ-=dis-(int)factor*dis;
                break;
            case 6:
                newX+=dis+(int)factor*dis;
                newZ-=dis-(int)factor*dis;
                break;
            case 7:
                newX-=dis-(int)factor*dis;
                newZ+=dis+(int)factor*dis;
                break;
        }

        Vector3i prevTarget = botsTarget.get(bot);
        if (prevTarget!=null && (int)prevTarget.getX() == newX && (int)prevTarget.getZ() == newZ) {
            newX = (int) (originalLocation.getX() + random.nextInt(8) * (random.nextBoolean() ? -1 : 1) * random.nextDouble());
            newZ = (int) (originalLocation.getZ() + random.nextInt(8) * (random.nextBoolean() ? -1 : 1) * random.nextDouble());
        }

//        String regionFile = "r." + (newX >> 5) + "." + (newZ >> 5);
//        System.out.println("BotID="+botId+",newX="+newX+",newZ="+newZ);

        Vector3i nextTarget = getTargetAt(bot, newX, newZ);
        botsTarget.put(bot, nextTarget);

        return nextTarget;
    }

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
            bot.getLogger().warning("Bot target not loaded: (" + x + "," + y + "," + z + ")");
            return botLoc.intVector();
        }
    }

    public void setWalkSpeed(double walkSpeed) {
        this.walkSpeed = walkSpeed;
    }
}
