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

package nl.tudelft.opencraft.yardstick.workload;

import science.atlarge.opencraft.packetlib.event.session.PacketReceivedEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketSentEvent;
import science.atlarge.opencraft.packetlib.event.session.SessionAdapter;

/**
 * A {@link SessionAdapter} which writes packets to a {@link WorkloadDumper}.
 */
public class WorkloadSessionListener extends SessionAdapter {

    private final WorkloadDumper dumper;
    private final String botName;

    /**
     * Creates a new WorkloadSessionListener.
     *
     * @param dumper  the dumper to use.
     * @param botName The name of the bot this listener is attached to.
     */
    public WorkloadSessionListener(WorkloadDumper dumper, String botName) {
        this.dumper = dumper;
        this.botName = botName;
    }

    @Override
    public void packetReceived(PacketReceivedEvent pre) {
        dumper.packetReceived(botName, pre);
    }

    @Override
    public void packetSent(PacketSentEvent pse) {
        dumper.packetSent(botName, pse);
    }

}
