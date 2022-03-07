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

import org.apache.commons.collections4.IteratorUtils;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

import java.util.Arrays;
import java.util.Collections;

class ZigZagRangeTest {
    @Test
    public void testSingleValueRange() {
        Assertions.assertEquals(Collections.singletonList(0), IteratorUtils.toList(new ZigZagRange(0, 0, 0)));
    }

    @Test
    public void testEmptyList() {
        Assertions.assertEquals(Collections.emptyList(), IteratorUtils.toList(new ZigZagRange(0, 0, 5)));
    }

    @Test
    public void testNormalCase() {
        Assertions.assertEquals(Arrays.asList(5, 6, 4, 7, 3, 8, 2, 9, 1, 10, 0), IteratorUtils.toList(new ZigZagRange(0, 10, 5)));
    }

    @Test
    public void testSkewedTop() {
        Assertions.assertEquals(Arrays.asList(8, 9, 7, 10, 6, 5, 4, 3, 2, 1, 0), IteratorUtils.toList(new ZigZagRange(0, 10, 8)));
    }

    @Test
    public void testSkewedBottom() {
        Assertions.assertEquals(Arrays.asList(2, 3, 1, 4, 0, 5, 6, 7, 8, 9, 10), IteratorUtils.toList(new ZigZagRange(0, 10, 2)));
    }

    @Test
    public void testFullRange() {
        Assertions.assertEquals(256, IteratorUtils.toList(new ZigZagRange(0, 255, 56)).size());
    }
}
