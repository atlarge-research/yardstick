package nl.tudelft.opencraft.yardstick.util;

import java.util.Arrays;
import java.util.Collections;
import org.apache.commons.collections4.IteratorUtils;
import org.junit.jupiter.api.Assertions;
import org.junit.jupiter.api.Test;

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
