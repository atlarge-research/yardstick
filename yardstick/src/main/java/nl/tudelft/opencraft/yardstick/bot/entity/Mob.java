package nl.tudelft.opencraft.yardstick.bot.entity;

import java.util.UUID;
import com.github.steveice10.mc.protocol.data.game.entity.type.EntityType;

public class Mob extends Entity {

    protected final EntityType type;

    public Mob(int id, UUID uuid, EntityType type) {
        super(id, uuid);

        this.type = type;
    }

    public EntityType getType() {
        return type;
    }

}
