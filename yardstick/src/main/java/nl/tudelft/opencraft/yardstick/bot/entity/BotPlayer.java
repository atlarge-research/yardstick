package nl.tudelft.opencraft.yardstick.bot.entity;

import java.nio.charset.Charset;
import java.util.UUID;
import com.github.steveice10.mc.protocol.data.game.entity.player.GameMode;
import com.github.steveice10.mc.protocol.packet.ingame.client.player.ClientPlayerPositionPacket;
import com.github.steveice10.packetlib.Session;
import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.util.Vector3d;

public class BotPlayer extends Player {

    private final Bot bot;
    private final Session session;
    //
    private GameMode gamemode;
    private boolean canFly;
    private double flySpeed;
    private double walkSpeed;
    private boolean invincible;
    private boolean flying;
    private double saturation;

    public BotPlayer(Bot bot, int id) {
        super(UUID.nameUUIDFromBytes(bot.getName().getBytes(Charset.forName("UTF-8"))), id);

        this.bot = bot;
        this.session = bot.getClient().getSession();
    }

    public Bot getBot() {
        return bot;
    }

    // TODO: Player actions, data
    public GameMode getGamemode() {
        return gamemode;
    }

    public void setGamemode(GameMode gamemode) {
        this.gamemode = gamemode;
    }

    public boolean getCanFly() {
        return canFly;
    }

    public void setCanFly(boolean canFly) {
        this.canFly = canFly;
    }

    public double getFlySpeed() {
        return flySpeed;
    }

    public void setFlySpeed(double flySpeed) {
        this.flySpeed = flySpeed;
    }

    public double getWalkSpeed() {
        return walkSpeed;
    }

    public void setWalkSpeed(double walkSpeed) {
        this.walkSpeed = walkSpeed;
    }

    public void setFlying(boolean flying) {
        this.flying = flying;
    }

    public boolean isFlying() {
        return flying;
    }

    public boolean isInvincible() {
        return invincible;
    }

    public void setInvincible(boolean invurnable) {
        this.invincible = invurnable;
    }

    public double getSaturation() {
        return saturation;
    }

    public void setSaturation(double saturation) {
        this.saturation = saturation;
    }

    public void updateLocation(Vector3d vector) {
        boolean onGround = vector.getY() - Math.floor(vector.getY()) < 0.1;
        session.send(new ClientPlayerPositionPacket(onGround, vector.getX(), vector.getY(), vector.getZ()));
        this.setLocation(vector);
    }

}
