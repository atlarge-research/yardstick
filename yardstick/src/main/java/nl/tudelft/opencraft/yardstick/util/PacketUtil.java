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
import java.lang.reflect.Field;
import java.util.Map;
import java.util.Map.Entry;
import science.atlarge.opencraft.packetlib.io.NetOutput;
import science.atlarge.opencraft.packetlib.io.stream.StreamNetOutput;
import science.atlarge.opencraft.packetlib.packet.Packet;
import science.atlarge.opencraft.packetlib.packet.PacketProtocol;

/**
 * Represents packet-related utilities.
 */
public class PacketUtil {

    private static final CountingOutputStream cos = new CountingOutputStream();
    private static final NetOutput cno = new StreamNetOutput(cos);

    private PacketUtil() {
    }

    /**
     * Returns, in bytes, the length of the packet.
     *
     * @param packet the packet.
     * @return The length.
     */
    public static int packetLength(Packet packet) {
        cos.reset();
        try {
            packet.write(cno);
        } catch (IOException ex) {
            return -1;
        }
        return (int) cos.getCount();
    }

    /**
     * Returns the packet class corresponding to a packet integer identifier in
     * a {@link PacketProtocol}.
     *
     * @param prot the packet protocol.
     * @param id the ID of the packet.
     * @param outgoing whether the packet is client->server.
     * @return The packet class.
     * @throws Exception upon failure of any sort.
     */
    public static Class<?> getPacketClass(PacketProtocol prot, int id, boolean outgoing) throws Exception {
        if (!outgoing) {
            return prot.createIncomingPacket(id).getClass();
        }

        // Get the private field
        Field outgoingMapField = PacketProtocol.class.getDeclaredField("incoming");

        // Make sure we can access the field
        outgoingMapField.setAccessible(true);

        // Get the map from the PacketProtocol instance
        Map<?, ?> outgoingMap = Map.class.cast(outgoingMapField.get(prot));

        // Loop through the entries
        for (Entry<?, ?> entry : outgoingMap.entrySet()) {
            if (entry.getValue().equals(id)) {
                return Class.class.cast(entry.getKey());
            }
        }

        throw new IllegalArgumentException("Packet ID not registered: " + id);
    }

    //private final Map<Integer, Class<? extends Packet>> incoming;
    public static int getPacketId(PacketProtocol prot, Packet packet, boolean outgoing) throws Exception {
        if (outgoing) {
            return prot.getOutgoingId(packet.getClass());
        }

        // Get the private field
        Field incomingMapField = PacketProtocol.class.getDeclaredField("incoming");

        // Make sure we can access the field
        incomingMapField.setAccessible(true);

        // Get the map from the PacketProtocol instance
        Map<?, ?> incomingMap = Map.class.cast(incomingMapField.get(prot));

        // Loop through the entries
        Class<?> packetClass = packet.getClass();
        for (Entry<?, ?> entry : incomingMap.entrySet()) {
            if (entry.getValue().equals(packetClass)) {
                return Integer.class.cast(entry.getKey());
            }
        }

        throw new IllegalArgumentException("Packet not registered: " + packetClass.getSimpleName());
    }

}
