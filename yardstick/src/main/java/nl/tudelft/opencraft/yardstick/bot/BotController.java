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

package nl.tudelft.opencraft.yardstick.bot;

import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.metadata.ItemStack;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.metadata.Position;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.player.Hand;
import science.atlarge.opencraft.mcprotocollib.data.game.entity.player.PlayerAction;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.ClientChatPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.player.ClientPlayerActionPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.player.ClientPlayerPlaceBlockPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.player.ClientPlayerPositionPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.player.ClientPlayerRotationPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.player.ClientPlayerSwingArmPacket;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.client.window.ClientCreativeInventoryActionPacket;
import science.atlarge.opencraft.packetlib.Session;
import science.atlarge.opencraft.packetlib.packet.Packet;

/**
 * Represents actions for controlling a {@link Bot}.
 */
public class BotController {

    // http://wiki.vg/Inventory
    public static final int PLAYER_INVENTORY_HOTBAR_0 = 36;

    private final Bot bot;

    /**
     * Creates a new controller.
     *
     * @param bot the bot.
     */
    public BotController(Bot bot) {
        this.bot = bot;
    }

    /**
     * Gets the player data for the bot.
     *
     * @return the player data.
     */
    private BotPlayer getPlayer() {
        return bot.getPlayer();
    }

    /**
     * Returns the session for the bot.
     *
     * @return the session.
     */
    private Session getSession() {
        return bot.getClient().getSession();
    }

    /**
     * Sends a new location to the Minecraft server.
     *
     * @param vector the location.
     */
    public void updateLocation(Vector3d vector) {
        // TODO: fix onGround calculation
        boolean onGround = vector.getY() - Math.floor(vector.getY()) < 0.1;
        getPlayer().setLocation(vector);
        getSession().send(new ClientPlayerPositionPacket(onGround, vector.getX(), vector.getY(), vector.getZ()));
    }

    /**
     * Updates the Minecraft server of the Bot's digging status.
     *
     * @param block the block the bot is digging.
     * @param face  the face the bot is digging.
     * @param state the digging state.
     */
    public void updateDigging(Block block, BlockFace face, DiggingState state) {
        Position pos = new Position(block.getX(), block.getY(), block.getZ());
        Packet p;
        switch (state) {
            case STARTED_DIGGING:
                p = new ClientPlayerActionPacket(PlayerAction.START_DIGGING, pos, face.getInternalFace());
                break;
            case CANCELLED_DIGGING:
                p = new ClientPlayerActionPacket(PlayerAction.CANCEL_DIGGING, pos, face.getInternalFace());
                break;
            case FINISHED_DIGGING:
                p = new ClientPlayerActionPacket(PlayerAction.FINISH_DIGGING, pos, face.getInternalFace());
                break;
            default:
                throw new UnsupportedOperationException("Unsupported digging state");
        }
        getSession().send(p);
    }

    /**
     * Updates the Minecraft server of block placement.
     *
     * @param block    The block the bot is placing.
     * @param face     The face the bot is placing at.
     * @param hitpoint The hitpoint of the cursor.
     */
    public void placeBlock(Vector3i block, BlockFace face, Vector3d hitpoint) {
        // Look at the block
        Vector3d absoluteHit = block.doubleVector().add(0.5, 0.5, 0.5).add(face.getOffset().doubleVector().multiply(0.5));
        double[] yawPitch = calculateYawPitch(getPlayer().getEyeLocation(), absoluteHit);
        getSession().send(new ClientPlayerRotationPacket(true,
                (float) yawPitch[0],
                (float) yawPitch[1]));
        // Swing the arm
        getSession().send(new ClientPlayerSwingArmPacket(Hand.MAIN_HAND));
        // Place the block
        getSession().send(new ClientPlayerPlaceBlockPacket(
                // TODO: Figure this out
                new Position(block.getX(), block.getY() - 1, block.getZ()),
                face.getInternalFace(),
                Hand.MAIN_HAND,
                (float) hitpoint.getX(),
                (float) hitpoint.getY(),
                (float) hitpoint.getZ()));
        //bot.getLogger().info("Controller: place  -- block: " + block + ", face: " + face + ", hit: " + hitpoint);
    }

    /**
     * Updates the Minecraft server of a a creative inventory action. In
     * particular, getting a material and setting it as the first slot.
     *
     * @param mat the material to set.
     * @param amt the amount of material to set.
     */
    public void creativeInventoryAction(Material mat, int amt) {
        getSession().send(new ClientCreativeInventoryActionPacket(PLAYER_INVENTORY_HOTBAR_0, new ItemStack(mat.getId(), amt)));
    }

    public void sendChatMsg(String msg) {
        getSession().send(new ClientChatPacket(msg));
    }

    /**
     * A state of breaking blocks.
     */
    public static enum DiggingState {
        STARTED_DIGGING,
        CANCELLED_DIGGING,
        FINISHED_DIGGING;
    }

    // http://wiki.vg/Protocol#Player_Look
    private double[] calculateYawPitch(Vector3d from, Vector3d to) {
        Vector3d dv = to.subtract(from);

        double r = dv.length();

        double yaw = -Math.atan2(dv.getX(), dv.getZ()) / Math.PI * 180;
        if (yaw < 0) {
            yaw += 360;
        }
        double pitch = -Math.asin(dv.getY() / r) / Math.PI * 180;
        return new double[] {yaw, pitch};
    }

}
