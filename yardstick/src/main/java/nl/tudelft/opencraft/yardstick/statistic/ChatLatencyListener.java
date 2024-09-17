package nl.tudelft.opencraft.yardstick.statistic;

import nl.tudelft.opencraft.yardstick.experiment.Experiment12RandomE2E;
import science.atlarge.opencraft.mcprotocollib.packet.ingame.server.ServerChatPacket;
import science.atlarge.opencraft.packetlib.event.session.ConnectedEvent;
import science.atlarge.opencraft.packetlib.event.session.DisconnectedEvent;
import science.atlarge.opencraft.packetlib.event.session.DisconnectingEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketReceivedEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketSendingEvent;
import science.atlarge.opencraft.packetlib.event.session.PacketSentEvent;
import science.atlarge.opencraft.packetlib.event.session.SessionListener;
import science.atlarge.opencraft.packetlib.packet.Packet;

import java.io.IOException;

public class ChatLatencyListener implements SessionListener {
    @Override
    public void packetReceived(PacketReceivedEvent event) {
        Packet packet = event.getPacket();
        if (packet instanceof ServerChatPacket) {
            ServerChatPacket p = (ServerChatPacket) packet;
            // log time
            long end = System.currentTimeMillis();

            String key = null;
            if (p.getMessage().getText().startsWith("There are")) {
                key = "banlist";
            }
            if (p.getMessage().getText().startsWith("Banned player")) {
                key = "ban";
            }
            if (p.getMessage().getText().startsWith("Unbanned")) {
                key = "unban";
            }
            if (p.getMessage().getText().startsWith("Changing to clear")) {
                key = "clear";
            }
            if (p.getMessage().getText().startsWith("Changing to rain and thunder")) {
                key = "thunder";
            }
            try {
                if (key != null) {
                    Experiment12RandomE2E.fw.write(end + "\t" + key + "\t" + (end - Experiment12RandomE2E.GMStartTime) + "\n");
                    Experiment12RandomE2E.fw.flush();
                }
            } catch (IOException e) {
                e.printStackTrace();
            }
        }
    }

    @Override
    public void packetSending(PacketSendingEvent event) {

    }

    @Override
    public void packetSent(PacketSentEvent event) {

    }

    @Override
    public void connected(ConnectedEvent event) {

    }

    @Override
    public void disconnecting(DisconnectingEvent event) {

    }

    @Override
    public void disconnected(DisconnectedEvent event) {

    }
}
