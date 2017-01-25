package nl.tudelft.opencraft.yardstick.bot.entity;

import java.util.UUID;

public class Living extends Entity {

    protected double health;

    public Living(int id, UUID uuid) {
        super(id, uuid);
    }

    public double getHealth() {
        return health;
    }

    public void setHealth(double health) {
        this.health = health;
    }

}
