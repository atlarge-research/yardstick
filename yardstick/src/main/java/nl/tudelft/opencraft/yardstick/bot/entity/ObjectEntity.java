package nl.tudelft.opencraft.yardstick.bot.entity;

import java.util.UUID;
import com.github.steveice10.mc.protocol.data.game.entity.type.object.ObjectType;

/**
 * Represents an Object.
 *
 * <p>
 * http://wiki.vg/Entities#Objects</p>
 */
public class ObjectEntity extends Entity {

    protected int data;
    protected ObjectType type;

    public ObjectEntity(int id, UUID uuid) {
        super(id, uuid);
    }

    public int getData() {
        return data;
    }

    public void setData(int data) {
        this.data = data;
    }

    public ObjectType getType() {
        return type;
    }

    public void setType(ObjectType type) {
        this.type = type;
    }

}
