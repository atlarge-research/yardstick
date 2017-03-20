package nl.tudelft.opencraft.yardstick.bot.entity;

import java.util.UUID;
import com.github.steveice10.mc.protocol.data.game.entity.type.MobType;

public class Mob extends Entity {

    protected final MobType type;

    public Mob(int id, UUID uuid, MobType type) {
        super(id, uuid);

        this.type = type;
    }

    public MobType getType() {
        return type;
    }

}
