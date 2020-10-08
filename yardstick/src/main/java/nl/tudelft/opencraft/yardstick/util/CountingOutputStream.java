package nl.tudelft.opencraft.yardstick.util;

import java.io.IOException;
import java.io.OutputStream;

/**
 * An {@link OutputStream} which does not write any bytes, but counts them
 * instead.
 */
public class CountingOutputStream extends OutputStream {

    private long count;

    @Override
    public void write(int b) throws IOException {
        count++;
    }

    @Override
    public void write(byte[] b, int off, int len) throws IOException {
        count += len;
    }

    @Override
    public void write(byte[] b) throws IOException {
        count += b.length;
    }

    /**
     * Returns the number of bytes written.
     *
     * @return the byte count.
     */
    public long getCount() {
        return count;
    }

    /**
     * Resets the counter.
     */
    public void reset() {
        count = 0;
    }

}
