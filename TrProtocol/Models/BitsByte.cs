namespace TrProtocol.Models;

// Token: 0x020000F4 RID: 244

// Token: 0x0200072A RID: 1834
// Token: 0x02000010 RID: 16
public partial struct BitsByte
{
    // Token: 0x060000E2 RID: 226 RVA: 0x00005028 File Offset: 0x00003228
    public BitsByte(bool b1 = false, bool b2 = false, bool b3 = false, bool b4 = false, bool b5 = false, bool b6 = false, bool b7 = false, bool b8 = false)
    {
        this.value = 0;
        this[0] = b1;
        this[1] = b2;
        this[2] = b3;
        this[3] = b4;
        this[4] = b5;
        this[5] = b6;
        this[6] = b7;
        this[7] = b8;
    }

    // Token: 0x060000E3 RID: 227 RVA: 0x00005084 File Offset: 0x00003284
    public void ClearAll()
    {
        this.value = 0;
    }

    // Token: 0x060000E4 RID: 228 RVA: 0x00005090 File Offset: 0x00003290
    public void SetAll()
    {
        this.value = byte.MaxValue;
    }

    // Token: 0x17000063 RID: 99
    public bool this[int key]
    {
        get
        {
            return ((int)this.value & 1 << key) != 0;
        }
        set
        {
            if (value)
            {
                this.value |= (byte)(1 << key);
                return;
            }
            this.value &= (byte)(~(byte)(1 << key));
        }
    }

    // Token: 0x060000E7 RID: 231 RVA: 0x000050E8 File Offset: 0x000032E8
    public void Retrieve(ref bool b0)
    {
        this.Retrieve(ref b0, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null);
    }

    // Token: 0x060000E8 RID: 232 RVA: 0x00005120 File Offset: 0x00003320
    public void Retrieve(ref bool b0, ref bool b1)
    {
        this.Retrieve(ref b0, ref b1, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null);
    }

    // Token: 0x060000E9 RID: 233 RVA: 0x00005154 File Offset: 0x00003354
    public void Retrieve(ref bool b0, ref bool b1, ref bool b2)
    {
        this.Retrieve(ref b0, ref b1, ref b2, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null);
    }

    // Token: 0x060000EA RID: 234 RVA: 0x00005184 File Offset: 0x00003384
    public void Retrieve(ref bool b0, ref bool b1, ref bool b2, ref bool b3)
    {
        this.Retrieve(ref b0, ref b1, ref b2, ref b3, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null);
    }

    // Token: 0x060000EB RID: 235 RVA: 0x000051B0 File Offset: 0x000033B0
    public void Retrieve(ref bool b0, ref bool b1, ref bool b2, ref bool b3, ref bool b4)
    {
        this.Retrieve(ref b0, ref b1, ref b2, ref b3, ref b4, ref BitsByte.Null, ref BitsByte.Null, ref BitsByte.Null);
    }

    // Token: 0x060000EC RID: 236 RVA: 0x000051DC File Offset: 0x000033DC
    public void Retrieve(ref bool b0, ref bool b1, ref bool b2, ref bool b3, ref bool b4, ref bool b5)
    {
        this.Retrieve(ref b0, ref b1, ref b2, ref b3, ref b4, ref b5, ref BitsByte.Null, ref BitsByte.Null);
    }

    // Token: 0x060000ED RID: 237 RVA: 0x00005204 File Offset: 0x00003404
    public void Retrieve(ref bool b0, ref bool b1, ref bool b2, ref bool b3, ref bool b4, ref bool b5, ref bool b6)
    {
        this.Retrieve(ref b0, ref b1, ref b2, ref b3, ref b4, ref b5, ref b6, ref BitsByte.Null);
    }

    // Token: 0x060000EE RID: 238 RVA: 0x00005228 File Offset: 0x00003428
    public void Retrieve(ref bool b0, ref bool b1, ref bool b2, ref bool b3, ref bool b4, ref bool b5, ref bool b6, ref bool b7)
    {
        b0 = this[0];
        b1 = this[1];
        b2 = this[2];
        b3 = this[3];
        b4 = this[4];
        b5 = this[5];
        b6 = this[6];
        b7 = this[7];
    }

    // Token: 0x060000EF RID: 239 RVA: 0x00005284 File Offset: 0x00003484
    public static implicit operator byte(BitsByte bb)
    {
        return bb.value;
    }

    // Token: 0x060000F0 RID: 240 RVA: 0x0000528C File Offset: 0x0000348C
    public static implicit operator BitsByte(byte b)
    {
        return new BitsByte
        {
            value = b
        };
    }

    // Token: 0x060000F1 RID: 241 RVA: 0x000052AC File Offset: 0x000034AC
    public static BitsByte[] ComposeBitsBytesChain(bool optimizeLength, params bool[] flags)
    {
        int i = flags.Length;
        int num = 0;
        while (i > 0)
        {
            num++;
            i -= 7;
        }
        BitsByte[] array = new BitsByte[num];
        int num2 = 0;
        int num3 = 0;
        for (int j = 0; j < flags.Length; j++)
        {
            array[num3][num2] = flags[j];
            num2++;
            if (num2 == 7 && num3 < num - 1)
            {
                array[num3][num2] = true;
                num2 = 0;
                num3++;
            }
        }
        if (optimizeLength)
        {
            int num4 = array.Length - 1;
            while (array[num4] == 0 && num4 > 0)
            {
                array[num4 - 1][7] = false;
                num4--;
            }
            Array.Resize<BitsByte>(ref array, num4 + 1);
        }
        return array;
    }

    // Token: 0x060000F2 RID: 242 RVA: 0x00005368 File Offset: 0x00003568
    public static BitsByte[] DecomposeBitsBytesChain(BinaryReader reader)
    {
        List<BitsByte> list = new();
        BitsByte item;
        do
        {
            item = reader.ReadByte();
            list.Add(item);
        }
        while (item[7]);
        return list.ToArray();
    }

    // Token: 0x04000073 RID: 115
    private static bool Null;

    // Token: 0x04000074 RID: 116
    public byte value;
}
