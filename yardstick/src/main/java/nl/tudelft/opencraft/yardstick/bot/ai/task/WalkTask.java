/*
 Copyright (c) 2013, DarkStorm (darkstorm@evilminecraft.net)
 All rights reserved.

 Redistribution and use in source and binary forms, with or without
 modification, are permitted provided that the following conditions are met:

 1. Redistributions of source code must retain the above copyright notice, this
 list of conditions and the following disclaimer.
 2. Redistributions in binary form must reproduce the above copyright notice,
 this list of conditions and the following disclaimer in the documentation
 and/or other materials provided with the distribution.

 THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
 ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
 ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
 LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
 ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
package nl.tudelft.opencraft.yardstick.bot.ai.task;

import java.util.concurrent.*;
import java.util.logging.Logger;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.PathNode;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.ChunkNotLoadedException;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class WalkTask implements Task {

    private static double defaultSpeed = 0.15, defaultJumpFactor = 3, defaultFallFactor = 4, defaultLiquidFactor = 0.5;
    private static int defaultTimeout = 10000;

    private final Bot bot;
    private final Logger logger;
    private final ExecutorService service = Executors.newSingleThreadExecutor();
    private final Vector3i target;

    private final long startTime;

    private Future<PathNode> pathFuture;
    private PathNode nextStep;
    private int ticksSinceStepChange = 0;
    private int timeout = defaultTimeout;
    private double speed = defaultSpeed, jumpFactor = defaultJumpFactor, fallFactor = defaultFallFactor, liquidFactor = defaultLiquidFactor;

    private TaskStatus status = TaskStatus.forInProgress();

    private Callable<PathNode> task = new Callable<PathNode>() {
        @Override
        public PathNode call() throws Exception {
            BotPlayer player = bot.getPlayer();
            logger.info("Calculating path ...");
            PathNode start = bot.getPathFinder().provideSearch(player.getLocation().intVector(), target);
            logger.info("Calculating path done!");
            return start;
        }
    };

    public WalkTask(final Bot bot, final Vector3i target) {
        this.bot = bot;
        this.target = target;
        this.logger = bot.getLogger().newSubLogger("WalkTask{" + target.toString() + "}");

        pathFuture = service.submit(task);
        startTime = System.currentTimeMillis();
    }

    public Vector3i getTarget() {
        return target;
    }

    public void setTimeout(int timeout) {
        this.timeout = timeout;
    }

    /**
     * Walk speed, in blocks/tick. Default is 0.15.
     */
    public double getSpeed() {
        return speed;
    }

    /**
     * Set walk speed.
     *
     * @param speed Walk speed, in blocks/tick. Default is 0.15.
     */
    public void setSpeed(double speed) {
        this.speed = speed;
    }

    public double getJumpFactor() {
        return jumpFactor;
    }

    public void setJumpFactor(double jumpFactor) {
        this.jumpFactor = jumpFactor;
    }

    public double getFallFactor() {
        return fallFactor;
    }

    public void setFallFactor(double fallFactor) {
        this.fallFactor = fallFactor;
    }

    public double getLiquidFactor() {
        return liquidFactor;
    }

    public void setLiquidFactor(double liquidFactor) {
        this.liquidFactor = liquidFactor;
    }

    @Override
    public TaskStatus tick() {
        if (pathFuture != null && !pathFuture.isDone()) {
            if (timeout > 0 && System.currentTimeMillis() - startTime > timeout) {
                pathFuture.cancel(true);
                pathFuture = null;
                nextStep = null;
                return status = TaskStatus.forFailure("Path search timed out (" + timeout + " ms)");
            } else {
                return status = TaskStatus.forInProgress();
            }
        } else if (pathFuture != null && pathFuture.isDone() && !pathFuture.isCancelled()) {
            try {
                nextStep = pathFuture.get();
                logger.info(String.format("First step of path: %s", nextStep));
                ticksSinceStepChange = 0;
            } catch (InterruptedException e) {
                return status = TaskStatus.forFailure(e.getMessage());
            } catch (ExecutionException e) {
                if (e.getCause() instanceof ChunkNotLoadedException) {
                    return status = TaskStatus.forInProgress();
                }
                return status = TaskStatus.forFailure(e.getMessage());
            } finally {
                pathFuture = null;
            }
        }

        if (nextStep == null) {
            return status = TaskStatus.forSuccess();
        }

        BotPlayer player = bot.getPlayer();
        if (nextStep.getNext() != null && player.getLocation().distanceSquared(nextStep.getNext().getLocation().doubleVector()) < 0.2) {
            nextStep = nextStep.getNext();
            ticksSinceStepChange = 0;
        }
        if (player.getLocation().distanceSquared(nextStep.getLocation().doubleVector()) > 4) {
            logger.info(String.format("Strayed from path. %s -> %s", player.getLocation(), nextStep.getLocation()));
            TaskStatus status = TaskStatus.forInProgress();
            pathFuture = service.submit(task);
            return status;
        }
        ticksSinceStepChange++;
        if (ticksSinceStepChange > 80) {
            nextStep = null;
            return status = TaskStatus.forFailure("Too many ticks since step change");
        }
        double speed = this.speed;
        Vector3i location = nextStep.getLocation();
        Vector3i block = player.getLocation().intVector();
        Vector3d playerLoc = player.getLocation();

        double x = location.getX(), y = location.getY(), z = location.getZ();
        boolean inLiquid = false; // TODO: player.isInLiquid();
        Vector3i blockPosition = block.add(new Vector3i(0, -1, 0));
        Block thisBlock;
        try {
            thisBlock = bot.getWorld().getBlockAt(blockPosition);
        } catch (ChunkNotLoadedException e) {
            // Wait until chunk is loaded.
            logger.warning(String.format("Block under player: %s", blockPosition));
            logger.warning(String.format("Player at %s", playerLoc));
            return status = TaskStatus.forInProgress();
        }
        if (thisBlock == null) {
            logger.warning(String.format("Could not get block at %s", blockPosition));
            return TaskStatus.forInProgress();
        }
        if (Material.getById(thisBlock.getTypeId()) == Material.SOUL_SAND) {
            if (Material.getById(thisBlock.getTypeId()) == Material.SOUL_SAND) {
                y -= 0.12;
            }
            speed *= liquidFactor;
        } else if (inLiquid) {
            speed *= liquidFactor;
        }
        if (playerLoc.getY() != y) {
            boolean canClimbBlock = false;
            try {
                canClimbBlock = bot.getPathFinder().getWorldPhysics().canClimb(block);
            } catch (ChunkNotLoadedException e) {
                return status = TaskStatus.forInProgress();
            }
            if (!inLiquid && !canClimbBlock) {
                if (playerLoc.getY() < y) {
                    speed *= jumpFactor;
                } else {
                    speed *= fallFactor;
                }
            }
            double offsetY = playerLoc.getY() < y ? Math.min(speed, y - playerLoc.getY()) : Math.max(-speed, y - playerLoc.getY());
            playerLoc = playerLoc.add(new Vector3d(0, offsetY, 0));
        }

        if (playerLoc.getX() != x) {
            double offsetX = playerLoc.getX() < x ? Math.min(speed, x - playerLoc.getX()) : Math.max(-speed, x - playerLoc.getX());
            playerLoc = playerLoc.add(new Vector3d(offsetX, 0, 0));
        }

        if (playerLoc.getZ() != z) {
            double offsetZ = playerLoc.getZ() < z ? Math.min(speed, z - playerLoc.getZ()) : Math.max(-speed, z - playerLoc.getZ());
            playerLoc = playerLoc.add(new Vector3d(0, 0, offsetZ));
        }

        // Set new player location
        player.updateLocation(playerLoc);

        if (playerLoc.getX() == x && playerLoc.getY() == y && playerLoc.getZ() == z) {
            nextStep = nextStep.getNext();
            ticksSinceStepChange = 0;
        }

        return status = TaskStatus.forInProgress();
    }

    @Override
    public void stop() {
        if (pathFuture != null && !pathFuture.isDone()) {
            pathFuture.cancel(true);
        }
        nextStep = null;
        this.service.shutdown();
    }

    @Override
    public TaskStatus getStatus() {
        return status;
    }

    public boolean isMoving() {
        return nextStep != null;
    }

    public static double getDefaultSpeed() {
        return defaultSpeed;
    }

    public static void setDefaultSpeed(double defaultSpeed) {
        WalkTask.defaultSpeed = defaultSpeed;
    }

    public static double getDefaultJumpFactor() {
        return defaultJumpFactor;
    }

    public static void setDefaultJumpFactor(double defaultJumpFactor) {
        WalkTask.defaultJumpFactor = defaultJumpFactor;
    }

    public static double getDefaultFallFactor() {
        return defaultFallFactor;
    }

    public static void setDefaultFallFactor(double defaultFallFactor) {
        WalkTask.defaultFallFactor = defaultFallFactor;
    }

    public static double getDefaultLiquidFactor() {
        return defaultLiquidFactor;
    }

    public static void setDefaultLiquidFactor(double defaultLiquidFactor) {
        WalkTask.defaultLiquidFactor = defaultLiquidFactor;
    }

    public static int getDefaultTimeout() {
        return defaultTimeout;
    }

    public static void setDefaultTimeout(int defaultTimeout) {
        WalkTask.defaultTimeout = defaultTimeout;
    }
}
