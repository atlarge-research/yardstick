package nl.tudelft.opencraft.yardstick.model;

import java.text.MessageFormat;
import nl.tudelft.opencraft.yardstick.model.box.BoundingBoxMovementBuilder;

public class MovementModelFactory {
    MovementModelBuilder fromName(String name) {
        if (name.equals("box")) {
            return new BoundingBoxMovementBuilder();
        } else {
            throw new IllegalArgumentException(MessageFormat.format("movement model ''{0}'' does not exist", name));
        }
    }
}
