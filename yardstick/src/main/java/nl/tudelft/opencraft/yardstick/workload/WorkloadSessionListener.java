package nl.tudelft.opencraft.yardstick.workload;

import com.github.steveice10.packetlib.event.session.ConnectedEvent;
import com.github.steveice10.packetlib.event.session.DisconnectedEvent;
import com.github.steveice10.packetlib.event.session.DisconnectingEvent;
import com.github.steveice10.packetlib.event.session.PacketReceivedEvent;
import com.github.steveice10.packetlib.event.session.PacketSentEvent;
import com.github.steveice10.packetlib.event.session.SessionListener;

public class WorkloadSessionListener implements SessionListener {

    private final WorkloadDumper dumper;
    private final String botName;
    
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

    @Override
    public void connected(ConnectedEvent ce) {
    }

    @Override
    public void disconnecting(DisconnectingEvent de) {
    }

    @Override
    public void disconnected(DisconnectedEvent de) {
    }

}
