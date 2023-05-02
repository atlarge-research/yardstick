using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace TrProtocol.Packets;

public class RequestLucyPopup : Packet
{
    public override MessageID Type => MessageID.RequestLucyPopup;
    public MessageSource Source { get; set; }
    public byte Variation { get; set; }
    public Vector2 Velocity { get; set; }
    public Position Position { get; set; }
}