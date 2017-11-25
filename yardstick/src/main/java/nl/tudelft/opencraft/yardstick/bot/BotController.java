package nl.tudelft.opencraft.yardstick.bot;

import com.github.steveice10.mc.protocol.data.game.entity.metadata.ItemStack;
import com.github.steveice10.mc.protocol.data.game.entity.metadata.Position;
import com.github.steveice10.mc.protocol.data.game.entity.player.Hand;
import com.github.steveice10.mc.protocol.data.game.entity.player.PlayerAction;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerActionPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerPlaceBlockPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerPositionPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.window.ClientCreativeInventoryActionPacket;
import com.github.steveice10.packetlib.Session;
import com.github.steveice10.packetlib.packet.Packet;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.bot.world.Material;
import nl.tudelft.opencraft.yardstick.util.Vector3d;
import nl.tudelft.opencraft.yardstick.util.Vector3i;

public class BotController {

    // http://wiki.vg/Inventory
    public static final int PLAYER_INVENTORY_HOTBAR_0 = 36;

    private final Bot bot;

    public BotController(Bot bot) {
        this.bot = bot;
    }

    private BotPlayer getPlayer() {
        return bot.getPlayer();
    }

    private Session getSession() {
        return bot.getClient().getSession();
    }

    public void updateLocation(Vector3d vector) {
        // TODO: fix onGround calculation
        boolean onGround = vector.getY() - Math.floor(vector.getY()) < 0.1;
        getPlayer().setLocation(vector);
        getSession().send(new ClientPlayerPositionPacket(onGround, vector.getX(), vector.getY(), vector.getZ()));
    }

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

    public void placeBlock(Vector3i block, BlockFace face, Vector3d hitpoint) {
        getSession().send(new ClientPlayerPlaceBlockPacket(
                new Position(block.getX(), block.getY(), block.getZ()),
                face.getInternalFace(),
                Hand.MAIN_HAND,
                (float) hitpoint.getX(),
                (float) hitpoint.getY(),
                (float) hitpoint.getZ()));
    }

    public void creativeInventoryAction(Material mat, int amt) {
        getSession().send(new ClientCreativeInventoryActionPacket(PLAYER_INVENTORY_HOTBAR_0, new ItemStack(mat.getId(), amt)));
    }

    public static enum DiggingState {
        STARTED_DIGGING,
        CANCELLED_DIGGING,
        FINISHED_DIGGING;
    }

}
