package nl.tudelft.opencraft.yardstick.model;

import com.typesafe.config.Config;

public interface MovementModelBuilder {
    BotModel fromConfig(Config config);
}
