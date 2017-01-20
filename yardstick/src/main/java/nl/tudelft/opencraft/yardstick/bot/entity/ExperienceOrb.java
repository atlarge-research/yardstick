package nl.tudelft.opencraft.yardstick.bot.entity;

import java.util.UUID;

/**
 * Represents an experience orb.
 */
public class ExperienceOrb extends Entity {

    private int count;

    public ExperienceOrb(int id, UUID uuid) {
        super(id, uuid);
    }

    public int getCount() {
        return count;
    }

    public void setCount(int count) {
        this.count = count;
    }

    // TODO: Paintings should not have velocity. Restructure heirarchy?
}
