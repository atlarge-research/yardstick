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
package nl.tudelft.opencraft.yardstick.logging;

import java.io.File;
import java.io.IOException;
import java.util.logging.FileHandler;
import java.util.logging.Formatter;
import java.util.logging.Handler;
import java.util.logging.LogRecord;

/**
 * A handler for publishing logs to a file.
 */
public class SimpleFileHandler extends Handler {

    private final Handler handle;

    /**
     * Creates a new SimpleFileHandler for the given formatter and file. If the
     * file exists, it will be permanently deleted.
     *
     * @param formatter the formatter to use.
     * @param file the file to write to.
     */
    public SimpleFileHandler(Formatter formatter, File file) {
        this(formatter, file.getPath());

        if (file.exists()) {
            file.delete();
        }
    }

    /**
     * Creates a new SimpleFileHandler for the given formatter and file name. If
     * the file exists, it will be permanently deleted.
     *
     * @param formatter the formatter to use.
     * @param name the file to write to.
     */
    public SimpleFileHandler(Formatter formatter, String name) {
        Handler fileHandler = null;
        try {
            fileHandler = new FileHandler(name);
            fileHandler.setFormatter(formatter);
        } catch (IOException | SecurityException ex) {
            ex.printStackTrace(); // No logger here yet
        }

        handle = fileHandler;
    }

    @Override
    public void publish(LogRecord lr) {
        handle.publish(lr);
    }

    @Override
    public void flush() {
        handle.flush();
    }

    @Override
    public void close() throws SecurityException {
        handle.close();
    }
}
