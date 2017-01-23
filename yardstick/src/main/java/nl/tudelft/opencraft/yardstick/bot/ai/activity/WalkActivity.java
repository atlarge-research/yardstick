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
package nl.tudelft.opencraft.yardstick.bot.ai.activity;

import java.util.concurrent.Callable;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.PathNode;
import nl.tudelft.opencraft.yardstick.bot.ai.pathfinding.PathSearch;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.bot.world.World;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class WalkActivity implements Activity {

    private static double defaultSpeed = 0.15, defaultJumpFactor = 3, defaultFallFactor = 4, defaultLiquidFactor = 0.5;
    private static int defaultTimeout = 60000;

    private final Bot bot;
    private final ExecutorService service = Executors.newSingleThreadExecutor();
    private final Vector3i target;

    private final long startTime;

    private Future<PathNode> thread;
    private PathNode nextStep;
    private int ticksSinceStepChange = 0;
    private int timeout = defaultTimeout;
    private double speed = defaultSpeed, jumpFactor = defaultJumpFactor, fallFactor = defaultFallFactor, liquidFactor = defaultLiquidFactor;

    public WalkActivity(Bot bot, Vector3i target) {
        this(bot, target, false);
    }

    public WalkActivity(final Bot bot, final Vector3i target, boolean keepWalking) {
        this.bot = bot;
        this.target = target;
        System.out.println("Walking!");
        if (keepWalking) {
            Activity activity = bot.getTasks().getActivity();
            if (activity != null && activity instanceof WalkActivity && ((WalkActivity) activity).isMoving()) {
                WalkActivity walkActivity = (WalkActivity) activity;
                nextStep = walkActivity.nextStep;
                ticksSinceStepChange = walkActivity.ticksSinceStepChange;
            }
        }
        thread = service.submit(new Callable<PathNode>() {
            @Override
            public PathNode call() throws Exception {
                World world = bot.getWorld();
                BotPlayer player = bot.getPlayer();
                if (world == null || player == null || target == null) {
                    return null;
                }
                Vector3d ourLocation = player.getLocation();
                PathSearch search = bot.getPathFinder().provideSearch(ourLocation.intVector(), target);
                while (!search.isDone() && (thread == null || !thread.isCancelled())) {
                    System.out.println("Stepping...");
                    search.step();
                }
                return search.getPath();
            }
        });
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
    public void tick() {
        if (thread != null && !thread.isDone()) {
            if (timeout > 0 && System.currentTimeMillis() - startTime > timeout) {
                thread.cancel(true);
                thread = null;
                nextStep = null;
                return;
            }
        } else if (thread != null && thread.isDone() && !thread.isCancelled()) {
            try {
                nextStep = thread.get();
                System.out.println("Path found, walking...");
                ticksSinceStepChange = 0;
            } catch (Exception exception) {
                exception.printStackTrace();
                nextStep = null;
                return;
            } finally {
                thread = null;
            }
        }
        if (nextStep != null) {
            BotPlayer player = bot.getPlayer();
            System.out.println(" -> Moving from " + player.getLocation() + " to " + nextStep);
            if (nextStep.getNext() != null && player.getLocation().distanceSquared(nextStep.getNext().getLocation().doubleVector()) < 0.2) {
                nextStep = nextStep.getNext();
                ticksSinceStepChange = 0;
            }
            if (player.getLocation().distanceSquared(nextStep.getLocation().doubleVector()) > 4) {
                nextStep = null;
                return;
            }
            ticksSinceStepChange++;
            if (ticksSinceStepChange > 80) {
                nextStep = null;
                return;
            }
            double speed = this.speed;
            Vector3i location = nextStep.getLocation();
            Vector3i block = player.getLocation().intVector();
            Vector3d playerLoc = player.getLocation();

            double x = location.getX() + 0.5, y = location.getY(), z = location.getZ() + 0.5;
            boolean inLiquid = false; // TODO: player.isInLiquid();
            if (Material.getById(bot.getWorld().getBlockAt(block.add(new Vector3i(0, -1, 0))).getTypeId())
                    == Material.SOUL_SAND) {
                if (Material.getById(bot.getWorld().getBlockAt(location.add(new Vector3i(0, -1, 0))).getTypeId()) == Material.SOUL_SAND) {
                    y -= 0.12;
                }
                speed *= liquidFactor;
            } else if (inLiquid) {
                speed *= liquidFactor;
            }

            if (playerLoc.getY() != y) {
                if (!inLiquid && !bot.getPathFinder().getWorldPhysics().canClimb(block)) {
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
        }
    }

    @Override
    public void stop() {
        if (thread != null && !thread.isDone()) {
            thread.cancel(true);
        }
        nextStep = null;
    }

    public boolean isMoving() {
        return nextStep != null;
    }

    @Override
    public boolean isActive() {
        return thread != null || nextStep != null;
    }

    public static double getDefaultSpeed() {
        return defaultSpeed;
    }

    public static void setDefaultSpeed(double defaultSpeed) {
        WalkActivity.defaultSpeed = defaultSpeed;
    }

    public static double getDefaultJumpFactor() {
        return defaultJumpFactor;
    }

    public static void setDefaultJumpFactor(double defaultJumpFactor) {
        WalkActivity.defaultJumpFactor = defaultJumpFactor;
    }

    public static double getDefaultFallFactor() {
        return defaultFallFactor;
    }

    public static void setDefaultFallFactor(double defaultFallFactor) {
        WalkActivity.defaultFallFactor = defaultFallFactor;
    }

    public static double getDefaultLiquidFactor() {
        return defaultLiquidFactor;
    }

    public static void setDefaultLiquidFactor(double defaultLiquidFactor) {
        WalkActivity.defaultLiquidFactor = defaultLiquidFactor;
    }

    public static int getDefaultTimeout() {
        return defaultTimeout;
    }

    public static void setDefaultTimeout(int defaultTimeout) {
        WalkActivity.defaultTimeout = defaultTimeout;
    }
}
