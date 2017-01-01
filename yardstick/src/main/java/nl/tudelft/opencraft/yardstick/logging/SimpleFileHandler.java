/*
 * Copyright 2015 Jerom van der Sar.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package nl.tudelft.opencraft.yardstick.logging;

import java.io.File;
import java.io.IOException;
import java.util.logging.FileHandler;
import java.util.logging.Formatter;
import java.util.logging.Handler;
import java.util.logging.LogRecord;

public class SimpleFileHandler extends Handler {

    private final Handler handle;

    public SimpleFileHandler(Formatter formatter, File file) {
        this(formatter, file.getPath());

        if (file.exists()) {
            file.delete();
        }
    }

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
