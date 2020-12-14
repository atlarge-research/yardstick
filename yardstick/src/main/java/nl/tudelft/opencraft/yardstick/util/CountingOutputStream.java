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
