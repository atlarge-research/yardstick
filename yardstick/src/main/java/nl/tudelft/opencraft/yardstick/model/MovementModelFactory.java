package nl.tudelft.opencraft.yardstick.model;

import nl.tudelft.opencraft.yardstick.model.box.BoundingBoxMovementBuilder;

import java.text.MessageFormat;

public class MovementModelFactory {
    MovementModelBuilder fromName(String name) {
        if (name.equals("box")) {
            return new BoundingBoxMovementBuilder();
        } else {
            throw new IllegalArgumentException(MessageFormat.format("movement model ''{0}'' does not exist", name));
        }
    }
}
