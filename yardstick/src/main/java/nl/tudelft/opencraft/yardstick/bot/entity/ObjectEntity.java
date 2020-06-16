package nl.tudelft.opencraft.yardstick.bot.entity;

import com.github.steveice10.mc.protocol.data.game.entity.type.EntityType;

import java.util.UUID;

/**
 * Represents an Object.
 *
 * <p>
 * http://wiki.vg/Entities#Objects</p>
 */
public class ObjectEntity extends Entity {

    protected int data;
    protected EntityType type;

    public ObjectEntity(int id, UUID uuid) {
        super(id, uuid);
    }

    public int getData() {
        return data;
    }

    public void setData(int data) {
        this.data = data;
    }

    public EntityType getType() {
        return type;
    }

    public void setType(EntityType type) {
        this.type = type;
    }

}
