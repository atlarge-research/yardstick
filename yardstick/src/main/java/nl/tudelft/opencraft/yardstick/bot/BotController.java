package nl.tudelft.opencraft.yardstick.bot;

import com.github.steveice10.mc.protocol.data.game.entity.metadata.Position;
import com.github.steveice10.mc.protocol.data.game.entity.player.PlayerAction;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerActionPacket;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerPositionPacket;
import com.github.steveice10.packetlib.Session;
import com.github.steveice10.packetlib.packet.Packet;
import nl.tudelft.opencraft.yardstick.bot.entity.BotPlayer;
import nl.tudelft.opencraft.yardstick.bot.world.Block;
import nl.tudelft.opencraft.yardstick.bot.world.BlockFace;
import nl.tudelft.opencraft.yardstick.util.Vector3d;

public class BotController {

    private final Bot bot;
    private final BotPlayer player;
    private final Session session;

    public BotController(Bot bot) {
        this.bot = bot;
        this.player = bot.getPlayer();
        this.session = bot.getClient().getSession();
    }

    public void updateLocation(Vector3d vector) {
        // TODO: fix onGround calculation
        boolean onGround = vector.getY() - Math.floor(vector.getY()) < 0.1;
        player.setLocation(vector);
        session.send(new ClientPlayerPositionPacket(onGround, vector.getX(), vector.getY(), vector.getZ()));
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
            default:
                throw new UnsupportedOperationException("Unsupported digging state");

        }
        session.send(p);
    }

    public static enum DiggingState {
        STARTED_DIGGING,
        CANCELLED_DIGGING,
        FINISHED_DIGGING;
    }

}
