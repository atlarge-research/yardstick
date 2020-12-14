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

public class ZigZagRange implements Iterator<Integer> {

    private final int lower;
    private final int upper;
    private final int lowerCount;
    private final int upperCount;
    private final int start;
    private final ZigZagCounter counter = new ZigZagCounter();
    private boolean reachedUpper = false;
    private boolean reachedLower = false;

    public ZigZagRange(int lower, int upper, int start) {
        this.lower = lower;
        this.upper = upper;
        this.lowerCount = lower - start;
        this.upperCount = upper - start;
        this.start = start;
    }

    @Override
    public boolean hasNext() {
        return start >= lower && start <= upper && !(reachedUpper && reachedLower);
    }

    @Override
    public Integer next() {
        int val = counter.next();
        if (val < lowerCount || val > upperCount) {
            val = counter.next();
        }
        if (val <= lowerCount) {
            reachedLower = true;
        }
        if (val >= upperCount) {
            reachedUpper = true;
        }
        return start + val;
    }
}
