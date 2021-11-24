package nl.tudelft.opencraft.yardstick.model.box;

import com.typesafe.config.Config;
import java.text.MessageFormat;
import nl.tudelft.opencraft.yardstick.model.MovementModelBuilder;
import nl.tudelft.opencraft.yardstick.util.Vector2i;

public class BoundingBoxMovementBuilder implements MovementModelBuilder {
    @Override
    public BoundingBoxMovementModel fromConfig(Config config) {
        var diameter = config.getInt("diameter");
        var typeString = config.getString("center.type");
        Box2D box;
        switch (typeString.toLowerCase()) {
            case "worldspawn":
                box = new WorldSpawnBox2D(diameter);
                break;
            case "bot":
                box = new BotBox2D(diameter);
                break;
            case "absolute":
                var x = config.getInt("center.absolute.x");
                var z = config.getInt("center.absolute.z");
                var center = new Vector2i(x, z);
                box = new AbsoluteBox2D(diameter, center);
                break;
            default:
                throw new IllegalArgumentException(MessageFormat.format("box type {0} is not supported", typeString));
        }
        return new BoundingBoxMovementModel(box);
    }
}
