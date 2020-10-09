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
