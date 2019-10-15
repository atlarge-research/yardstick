package nl.tudelft.opencraft.yardstick.bot.ai.task;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import nl.tudelft.opencraft.yardstick.bot.Bot;

@JsonTypeInfo(
        use = JsonTypeInfo.Id.NAME,
        include = JsonTypeInfo.As.PROPERTY,
        property = "type")
@JsonSubTypes({
        @JsonSubTypes.Type(value = BreakBlocksTask.class, name = "break-blocks"),
        @JsonSubTypes.Type(value = PlaceBlocksTask.class, name = "place-blocks"),
        @JsonSubTypes.Type(value = WalkXZTask.class, name="walk-xz"),
        @JsonSubTypes.Type(value = RandomSquareWalkXZTask.class, name="random-square-walk-xz")
})
@JsonAutoDetect(fieldVisibility = JsonAutoDetect.Visibility.ANY)
public interface Task {
    TaskExecutor toExecutor(Bot bot);
}
