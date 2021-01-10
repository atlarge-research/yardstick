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

package nl.tudelft.opencraft.yardstick.bot.entity;

import java.util.UUID;
import com.github.steveice10.mc.protocol.data.game.entity.type.EntityType;

/**
 * Represents an EntityObject.
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
