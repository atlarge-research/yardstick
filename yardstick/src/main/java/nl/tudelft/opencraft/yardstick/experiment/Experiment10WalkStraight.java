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

package nl.tudelft.opencraft.yardstick.experiment;

import nl.tudelft.opencraft.yardstick.bot.Bot;
import nl.tudelft.opencraft.yardstick.model.StraightMovementModel;
import java.util.UUID;


public class Experiment10WalkStraight extends AbstractModelExperiment {

    public static int currBotId;
    public static int clientCount;
    public static double walkSpeed;

    public Experiment10WalkStraight() {
        super(10, "Bots move towards different directions based on their IDs", new StraightMovementModel());
        StraightMovementModel model = (StraightMovementModel) getModel();
        currBotId = Integer.parseInt(options.experimentParams.getOrDefault("botstartid", "0"));
        clientCount = Integer.parseInt(options.experimentParams.getOrDefault("clientcount", "1"));
        walkSpeed = Double.parseDouble(options.experimentParams.getOrDefault("walkspeed", "0.15"));
        model.setWalkSpeed(walkSpeed);

    }

    protected Bot createBot() {
        Bot bot = newBot(UUID.randomUUID().toString().substring(0, 6)+"-"+(currBotId));
        currBotId+=clientCount;
        return bot;
    }
}
