package nl.tudelft.opencraft.yardstick.bot.entity;

import java.util.UUID;
import nl.tudelft.opencraft.yardstick.playerbehavior.Vector3d;

public class Player extends Living {

    public Player(UUID uuid, int id) {
        super(id, uuid);
    }

    public Vector3d getEyeLocation() {
        // https://minecraft.gamepedia.com/The_Player
        return getLocation().add(0, 1.62f, 0);
    }

}
