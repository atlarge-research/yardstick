package nl.tudelft.opencraft.yardstick.bot.entity;

import java.util.UUID;

public class Painting extends Entity {

    public Painting(int id, UUID uuid) {
        super(id, uuid);
    }

    // TODO: Paintings should not have velocity. Restructure heirarchy?
}
