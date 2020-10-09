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
