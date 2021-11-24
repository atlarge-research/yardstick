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

import com.typesafe.config.Config;
import nl.tudelft.opencraft.yardstick.model.SimpleMovementModel;

public class Experiment5SimpleWalk extends AbstractModelExperiment {

    public Experiment5SimpleWalk(int nodeID, String address, Config config) {
        super(5, nodeID, address, config, "Bots move around randomly. Based on a movement model for Half Life 2",
                new SimpleMovementModel());
    }

}
