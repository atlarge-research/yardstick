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

import java.util.logging.Logger;

public class SubLogger extends Logger {

    public SubLogger(String name) {
        super(name, null);
    }

    public SubLogger newSubLogger(String name) {
        SubLogger logger;
        if (getName() == null) {
            logger = new SubLogger(name);
        } else {
            logger = new SubLogger(getName() + '.' + name);
        }
        logger.setParent(this);
        return logger;
    }

}
