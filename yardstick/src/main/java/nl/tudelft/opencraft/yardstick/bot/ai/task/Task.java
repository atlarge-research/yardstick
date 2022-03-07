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

package nl.tudelft.opencraft.yardstick.bot.ai.task;

import com.fasterxml.jackson.annotation.JsonAutoDetect;
import com.fasterxml.jackson.annotation.JsonSubTypes;
import com.fasterxml.jackson.annotation.JsonTypeInfo;
import nl.tudelft.opencraft.yardstick.bot.Bot;

@JsonTypeInfo(
        use = JsonTypeInfo.Id.NAME,
        include = JsonTypeInfo.As.PROPERTY,
        property = "type")
@JsonSubTypes( {
        @JsonSubTypes.Type(value = BreakBlocksTask.class, name = "break-blocks"),
        @JsonSubTypes.Type(value = PlaceBlocksTask.class, name = "place-blocks"),
        @JsonSubTypes.Type(value = WalkXZTask.class, name = "walk-xz"),
        @JsonSubTypes.Type(value = RandomSquareWalkXZTask.class, name = "random-square-walk-xz")
})
@JsonAutoDetect(fieldVisibility = JsonAutoDetect.Visibility.ANY)
public interface Task {
    TaskExecutor toExecutor(Bot bot);
}
