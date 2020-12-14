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

import java.util.Objects;
import java.util.UUID;

import nl.tudelft.opencraft.yardstick.util.Vector3d;

/**
 * Represents an entity.
 *
 * <p>
 * http://wiki.vg/Entities#Entity</p>
 */
public class Entity {

    protected final int id;
    protected final UUID uuid;
    //
    protected Vector3d location;
    protected double yaw, headYaw, pitch;
    protected Vector3d velocity;
    protected boolean onGround = true;
    // TODO: Metadata

    public Entity(int id, UUID uuid) {
        this.id = id;
        this.uuid = uuid;
    }

    public int getId() {
        return id;
    }

    public UUID getUuid() {
        return uuid;
    }

    public Vector3d getLocation() {
        return location;
    }

    public double getYaw() {
        return yaw;
    }

    public double getHeadYaw() {
        return headYaw;
    }

    public double getPitch() {
        return pitch;
    }

    public Vector3d getVelocity() {
        return velocity;
    }

    public boolean isOnGround() {
        return onGround;
    }

    public void setLocation(Vector3d location) {
        this.location = location;
    }

    public void setYaw(double yaw) {
        this.yaw = yaw;
    }

    public void setHeadYaw(double headYaw) {
        this.headYaw = headYaw;
    }

    public void setPitch(double pitch) {
        this.pitch = pitch;
    }

    public void setVelocity(Vector3d velocity) {
        this.velocity = velocity;
    }

    public void setOnGround(boolean onGround) {
        this.onGround = onGround;
    }

    @Override
    public int hashCode() {
        int hash = 5;
        hash = 97 * hash + this.id;
        hash = 97 * hash + Objects.hashCode(this.uuid);
        return hash;
    }

    @Override
    public boolean equals(Object obj) {
        if (obj == null) {
            return false;
        }
        if (getClass() != obj.getClass()) {
            return false;
        }
        final Entity other = (Entity) obj;
        if (this.id != other.id) {
            return false;
        }
        if (!Objects.equals(this.uuid, other.uuid)) {
            return false;
        }
        return true;
    }
}
