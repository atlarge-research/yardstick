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

package nl.tudelft.opencraft.yardstick.util;

import java.util.Iterator;

public class ZigZagCounter implements Iterator<Integer> {

    private int val = 0;
    private boolean start = true;

    @Override
    public boolean hasNext() {
        return true;
    }

    @Override
    public Integer next() {
        if (start) {
            start = false;
        } else if (val <= 0) {
            val--;
        }
        val = -val;
        return val;
    }
}
