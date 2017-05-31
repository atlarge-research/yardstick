package nl.tudelft.opencraft.yardstick.util;

import java.lang.reflect.Field;
import java.util.Map;
import java.util.Map.Entry;
import com.github.steveice10.packetlib.packet.Packet;
import com.github.steveice10.packetlib.packet.PacketProtocol;

public class PacketUtil {

    private PacketUtil() {
    }

    //private final Map<Class<? extends Packet>, Integer> outgoing;
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
