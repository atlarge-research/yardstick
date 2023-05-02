namespace TrProtocol.Packets;

public class MenuSunMoon : Packet
{
    public override MessageID Type => MessageID.MenuSunMoon;
    public bool DayTime { get; set; }
    public int Time { get; set; }
    public short Sun { get; set; }
    public short Moon { get; set; }
}
