namespace TrProtocol.Models;

public partial class PlayerDeathReason
{
    // Token: 0x170003D7 RID: 983
    // (get) Token: 0x060033D3 RID: 13267 RVA: 0x0058D70C File Offset: 0x0058B90C
    public int? SourceProjectileType
    {
        get
        {
            if (this._sourceProjectileIndex == -1)
            {
                return null;
            }
            return new int?(this._sourceProjectileType);
        }
    }

    // Token: 0x060033D4 RID: 13268 RVA: 0x0058D738 File Offset: 0x0058B938
    public static PlayerDeathReason LegacyEmpty()
    {
        return new PlayerDeathReason
        {
            _sourceOtherIndex = 254
        };
    }

    // Token: 0x060033D5 RID: 13269 RVA: 0x0058D74C File Offset: 0x0058B94C
    public static PlayerDeathReason LegacyDefault()
    {
        return new PlayerDeathReason
        {
            _sourceOtherIndex = 255
        };
    }

    // Token: 0x060033D6 RID: 13270 RVA: 0x0058D760 File Offset: 0x0058B960
    public static PlayerDeathReason ByNPC(int index)
    {
        return new PlayerDeathReason
        {
            _sourceNPCIndex = index
        };
    }

    // Token: 0x060033D7 RID: 13271 RVA: 0x0058D770 File Offset: 0x0058B970
    public static PlayerDeathReason ByCustomReason(string reasonInEnglish)
    {
        return new PlayerDeathReason
        {
            _sourceCustomReason = reasonInEnglish
        };
    }

    // Token: 0x060033D8 RID: 13272 RVA: 0x0058D780 File Offset: 0x0058B980
    public static PlayerDeathReason ByPlayer(int index)
    {
        return new PlayerDeathReason
        {
            _sourcePlayerIndex = index
        };
    }

    // Token: 0x060033D9 RID: 13273 RVA: 0x0058D7E4 File Offset: 0x0058B9E4
    public static PlayerDeathReason ByOther(int type)
    {
        return new PlayerDeathReason
        {
            _sourceOtherIndex = type
        };
    }

    // Token: 0x060033DA RID: 13274 RVA: 0x0058D7F4 File Offset: 0x0058B9F4
    public static PlayerDeathReason ByProjectile(int playerIndex, int projectileIndex)
    {
        PlayerDeathReason playerDeathReason = new()
        {
            _sourcePlayerIndex = playerIndex,
            _sourceProjectileIndex = projectileIndex
        };
        return playerDeathReason;
    }

    // Token: 0x060033DC RID: 13276 RVA: 0x0058D8BC File Offset: 0x0058BABC
    public void WriteSelfTo(BinaryWriter writer)
    {
        BitsByte bb = 0;
        bb[0] = (this._sourcePlayerIndex != -1);
        bb[1] = (this._sourceNPCIndex != -1);
        bb[2] = (this._sourceProjectileIndex != -1);
        bb[3] = (this._sourceOtherIndex != -1);
        bb[4] = (this._sourceProjectileType != 0);
        bb[5] = (this._sourceItemType != 0);
        bb[6] = (this._sourceItemPrefix != 0);
        bb[7] = (this._sourceCustomReason != null);
        writer.Write(bb);
        if (bb[0])
        {
            writer.Write((short)this._sourcePlayerIndex);
        }
        if (bb[1])
        {
            writer.Write((short)this._sourceNPCIndex);
        }
        if (bb[2])
        {
            writer.Write((short)this._sourceProjectileIndex);
        }
        if (bb[3])
        {
            writer.Write((byte)this._sourceOtherIndex);
        }
        if (bb[4])
        {
            writer.Write((short)this._sourceProjectileType);
        }
        if (bb[5])
        {
            writer.Write((short)this._sourceItemType);
        }
        if (bb[6])
        {
            writer.Write((byte)this._sourceItemPrefix);
        }
        if (bb[7])
        {
            writer.Write(this._sourceCustomReason);
        }
    }

    // Token: 0x060033DD RID: 13277 RVA: 0x0058DA28 File Offset: 0x0058BC28
    public static PlayerDeathReason FromReader(BinaryReader reader)
    {
        PlayerDeathReason playerDeathReason = new();
        BitsByte bitsByte = reader.ReadByte();
        if (bitsByte[0])
        {
            playerDeathReason._sourcePlayerIndex = (int)reader.ReadInt16();
        }
        if (bitsByte[1])
        {
            playerDeathReason._sourceNPCIndex = (int)reader.ReadInt16();
        }
        if (bitsByte[2])
        {
            playerDeathReason._sourceProjectileIndex = (int)reader.ReadInt16();
        }
        if (bitsByte[3])
        {
            playerDeathReason._sourceOtherIndex = (int)reader.ReadByte();
        }
        if (bitsByte[4])
        {
            playerDeathReason._sourceProjectileType = (int)reader.ReadInt16();
        }
        if (bitsByte[5])
        {
            playerDeathReason._sourceItemType = (int)reader.ReadInt16();
        }
        if (bitsByte[6])
        {
            playerDeathReason._sourceItemPrefix = (int)reader.ReadByte();
        }
        if (bitsByte[7])
        {
            playerDeathReason._sourceCustomReason = reader.ReadString();
        }
        return playerDeathReason;
    }

    // Token: 0x040059C3 RID: 22979
    public int _sourcePlayerIndex = -1;

    // Token: 0x040059C4 RID: 22980
    public int _sourceNPCIndex = -1;

    // Token: 0x040059C5 RID: 22981
    public int _sourceProjectileIndex = -1;

    // Token: 0x040059C6 RID: 22982
    public int _sourceOtherIndex = -1;

    // Token: 0x040059C7 RID: 22983
    public int _sourceProjectileType;

    // Token: 0x040059C8 RID: 22984
    public int _sourceItemType;

    // Token: 0x040059C9 RID: 22985
    public int _sourceItemPrefix;

    // Token: 0x040059CA RID: 22986
    public string _sourceCustomReason;
}