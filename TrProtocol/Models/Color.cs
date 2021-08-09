using System;
using System.Globalization;

namespace TrProtocol.Models
{
    // Token: 0x02000854 RID: 2132
    public partial struct Color : IPackedVector<uint>, IPackedVector, IEquatable<Color>
    {
        // Token: 0x17000458 RID: 1112
        // (get) Token: 0x060037AF RID: 14255 RVA: 0x00590958 File Offset: 0x0058EB58
        // (set) Token: 0x060037B0 RID: 14256 RVA: 0x00590974 File Offset: 0x0058EB74
        public byte R
        {
            get => (byte)packedValue;
            set => packedValue = ((packedValue & 4294967040u) | value);
        }

        // Token: 0x17000459 RID: 1113
        // (get) Token: 0x060037B1 RID: 14257 RVA: 0x0059098C File Offset: 0x0058EB8C
        // (set) Token: 0x060037B2 RID: 14258 RVA: 0x005909A8 File Offset: 0x0058EBA8
        public byte G
        {
            get => (byte)(packedValue >> 8);
            set => packedValue = ((packedValue & 4294902015u) | (uint)value << 8);
        }

        // Token: 0x1700045A RID: 1114
        // (get) Token: 0x060037B3 RID: 14259 RVA: 0x005909C4 File Offset: 0x0058EBC4
        // (set) Token: 0x060037B4 RID: 14260 RVA: 0x005909E0 File Offset: 0x0058EBE0
        public byte B
        {
            get => (byte)(packedValue >> 16);
            set => packedValue = ((packedValue & 4278255615u) | (uint)value << 16);
        }

        // Token: 0x1700045B RID: 1115
        // (get) Token: 0x060037B5 RID: 14261 RVA: 0x005909FC File Offset: 0x0058EBFC
        // (set) Token: 0x060037B6 RID: 14262 RVA: 0x00590A18 File Offset: 0x0058EC18
        public byte A
        {
            get => (byte)(packedValue >> 24);
            set => packedValue = ((packedValue & 16777215u) | (uint)value << 24);
        }

        // Token: 0x1700045C RID: 1116
        // (get) Token: 0x060037B7 RID: 14263 RVA: 0x00590A34 File Offset: 0x0058EC34
        // (set) Token: 0x060037B8 RID: 14264 RVA: 0x00590A4C File Offset: 0x0058EC4C
        public uint PackedValue
        {
            get => packedValue;
            set => packedValue = value;
        }

        // Token: 0x1700045D RID: 1117
        // (get) Token: 0x060037B9 RID: 14265 RVA: 0x00590A58 File Offset: 0x0058EC58
        public static Color Transparent => new Color(0u);

        // Token: 0x1700045E RID: 1118
        // (get) Token: 0x060037BA RID: 14266 RVA: 0x00590A70 File Offset: 0x0058EC70
        public static Color AliceBlue => new Color(4294965488u);

        // Token: 0x1700045F RID: 1119
        // (get) Token: 0x060037BB RID: 14267 RVA: 0x00590A8C File Offset: 0x0058EC8C
        public static Color AntiqueWhite => new Color(4292340730u);

        // Token: 0x17000460 RID: 1120
        // (get) Token: 0x060037BC RID: 14268 RVA: 0x00590AA8 File Offset: 0x0058ECA8
        public static Color Aqua => new Color(4294967040u);

        // Token: 0x17000461 RID: 1121
        // (get) Token: 0x060037BD RID: 14269 RVA: 0x00590AC4 File Offset: 0x0058ECC4
        public static Color Aquamarine => new Color(4292149119u);

        // Token: 0x17000462 RID: 1122
        // (get) Token: 0x060037BE RID: 14270 RVA: 0x00590AE0 File Offset: 0x0058ECE0
        public static Color Azure => new Color(4294967280u);

        // Token: 0x17000463 RID: 1123
        // (get) Token: 0x060037BF RID: 14271 RVA: 0x00590AFC File Offset: 0x0058ECFC
        public static Color Beige => new Color(4292670965u);

        // Token: 0x17000464 RID: 1124
        // (get) Token: 0x060037C0 RID: 14272 RVA: 0x00590B18 File Offset: 0x0058ED18
        public static Color Bisque => new Color(4291093759u);

        // Token: 0x17000465 RID: 1125
        // (get) Token: 0x060037C1 RID: 14273 RVA: 0x00590B34 File Offset: 0x0058ED34
        public static Color Black => new Color(4278190080u);

        // Token: 0x17000466 RID: 1126
        // (get) Token: 0x060037C2 RID: 14274 RVA: 0x00590B50 File Offset: 0x0058ED50
        public static Color BlanchedAlmond => new Color(4291685375u);

        // Token: 0x17000467 RID: 1127
        // (get) Token: 0x060037C3 RID: 14275 RVA: 0x00590B6C File Offset: 0x0058ED6C
        public static Color Blue => new Color(4294901760u);

        // Token: 0x17000468 RID: 1128
        // (get) Token: 0x060037C4 RID: 14276 RVA: 0x00590B88 File Offset: 0x0058ED88
        public static Color BlueViolet => new Color(4293012362u);

        // Token: 0x17000469 RID: 1129
        // (get) Token: 0x060037C5 RID: 14277 RVA: 0x00590BA4 File Offset: 0x0058EDA4
        public static Color Brown => new Color(4280953509u);

        // Token: 0x1700046A RID: 1130
        // (get) Token: 0x060037C6 RID: 14278 RVA: 0x00590BC0 File Offset: 0x0058EDC0
        public static Color BurlyWood => new Color(4287084766u);

        // Token: 0x1700046B RID: 1131
        // (get) Token: 0x060037C7 RID: 14279 RVA: 0x00590BDC File Offset: 0x0058EDDC
        public static Color CadetBlue => new Color(4288716383u);

        // Token: 0x1700046C RID: 1132
        // (get) Token: 0x060037C8 RID: 14280 RVA: 0x00590BF8 File Offset: 0x0058EDF8
        public static Color Chartreuse => new Color(4278255487u);

        // Token: 0x1700046D RID: 1133
        // (get) Token: 0x060037C9 RID: 14281 RVA: 0x00590C14 File Offset: 0x0058EE14
        public static Color Chocolate => new Color(4280183250u);

        // Token: 0x1700046E RID: 1134
        // (get) Token: 0x060037CA RID: 14282 RVA: 0x00590C30 File Offset: 0x0058EE30
        public static Color Coral => new Color(4283465727u);

        // Token: 0x1700046F RID: 1135
        // (get) Token: 0x060037CB RID: 14283 RVA: 0x00590C4C File Offset: 0x0058EE4C
        public static Color CornflowerBlue => new Color(4293760356u);

        // Token: 0x17000470 RID: 1136
        // (get) Token: 0x060037CC RID: 14284 RVA: 0x00590C68 File Offset: 0x0058EE68
        public static Color Cornsilk => new Color(4292671743u);

        // Token: 0x17000471 RID: 1137
        // (get) Token: 0x060037CD RID: 14285 RVA: 0x00590C84 File Offset: 0x0058EE84
        public static Color Crimson => new Color(4282127580u);

        // Token: 0x17000472 RID: 1138
        // (get) Token: 0x060037CE RID: 14286 RVA: 0x00590CA0 File Offset: 0x0058EEA0
        public static Color Cyan => new Color(4294967040u);

        // Token: 0x17000473 RID: 1139
        // (get) Token: 0x060037CF RID: 14287 RVA: 0x00590CBC File Offset: 0x0058EEBC
        public static Color DarkBlue => new Color(4287299584u);

        // Token: 0x17000474 RID: 1140
        // (get) Token: 0x060037D0 RID: 14288 RVA: 0x00590CD8 File Offset: 0x0058EED8
        public static Color DarkCyan => new Color(4287335168u);

        // Token: 0x17000475 RID: 1141
        // (get) Token: 0x060037D1 RID: 14289 RVA: 0x00590CF4 File Offset: 0x0058EEF4
        public static Color DarkGoldenrod => new Color(4278945464u);

        // Token: 0x17000476 RID: 1142
        // (get) Token: 0x060037D2 RID: 14290 RVA: 0x00590D10 File Offset: 0x0058EF10
        public static Color DarkGray => new Color(4289309097u);

        // Token: 0x17000477 RID: 1143
        // (get) Token: 0x060037D3 RID: 14291 RVA: 0x00590D2C File Offset: 0x0058EF2C
        public static Color DarkGreen => new Color(4278215680u);

        // Token: 0x17000478 RID: 1144
        // (get) Token: 0x060037D4 RID: 14292 RVA: 0x00590D48 File Offset: 0x0058EF48
        public static Color DarkKhaki => new Color(4285249469u);

        // Token: 0x17000479 RID: 1145
        // (get) Token: 0x060037D5 RID: 14293 RVA: 0x00590D64 File Offset: 0x0058EF64
        public static Color DarkMagenta => new Color(4287299723u);

        // Token: 0x1700047A RID: 1146
        // (get) Token: 0x060037D6 RID: 14294 RVA: 0x00590D80 File Offset: 0x0058EF80
        public static Color DarkOliveGreen => new Color(4281297749u);

        // Token: 0x1700047B RID: 1147
        // (get) Token: 0x060037D7 RID: 14295 RVA: 0x00590D9C File Offset: 0x0058EF9C
        public static Color DarkOrange => new Color(4278226175u);

        // Token: 0x1700047C RID: 1148
        // (get) Token: 0x060037D8 RID: 14296 RVA: 0x00590DB8 File Offset: 0x0058EFB8
        public static Color DarkOrchid => new Color(4291572377u);

        // Token: 0x1700047D RID: 1149
        // (get) Token: 0x060037D9 RID: 14297 RVA: 0x00590DD4 File Offset: 0x0058EFD4
        public static Color DarkRed => new Color(4278190219u);

        // Token: 0x1700047E RID: 1150
        // (get) Token: 0x060037DA RID: 14298 RVA: 0x00590DF0 File Offset: 0x0058EFF0
        public static Color DarkSalmon => new Color(4286224105u);

        // Token: 0x1700047F RID: 1151
        // (get) Token: 0x060037DB RID: 14299 RVA: 0x00590E0C File Offset: 0x0058F00C
        public static Color DarkSeaGreen => new Color(4287347855u);

        // Token: 0x17000480 RID: 1152
        // (get) Token: 0x060037DC RID: 14300 RVA: 0x00590E28 File Offset: 0x0058F028
        public static Color DarkSlateBlue => new Color(4287315272u);

        // Token: 0x17000481 RID: 1153
        // (get) Token: 0x060037DD RID: 14301 RVA: 0x00590E44 File Offset: 0x0058F044
        public static Color DarkSlateGray => new Color(4283387695u);

        // Token: 0x17000482 RID: 1154
        // (get) Token: 0x060037DE RID: 14302 RVA: 0x00590E60 File Offset: 0x0058F060
        public static Color DarkTurquoise => new Color(4291939840u);

        // Token: 0x17000483 RID: 1155
        // (get) Token: 0x060037DF RID: 14303 RVA: 0x00590E7C File Offset: 0x0058F07C
        public static Color DarkViolet => new Color(4292018324u);

        // Token: 0x17000484 RID: 1156
        // (get) Token: 0x060037E0 RID: 14304 RVA: 0x00590E98 File Offset: 0x0058F098
        public static Color DeepPink => new Color(4287829247u);

        // Token: 0x17000485 RID: 1157
        // (get) Token: 0x060037E1 RID: 14305 RVA: 0x00590EB4 File Offset: 0x0058F0B4
        public static Color DeepSkyBlue => new Color(4294950656u);

        // Token: 0x17000486 RID: 1158
        // (get) Token: 0x060037E2 RID: 14306 RVA: 0x00590ED0 File Offset: 0x0058F0D0
        public static Color DimGray => new Color(4285098345u);

        // Token: 0x17000487 RID: 1159
        // (get) Token: 0x060037E3 RID: 14307 RVA: 0x00590EEC File Offset: 0x0058F0EC
        public static Color DodgerBlue => new Color(4294938654u);

        // Token: 0x17000488 RID: 1160
        // (get) Token: 0x060037E4 RID: 14308 RVA: 0x00590F08 File Offset: 0x0058F108
        public static Color Firebrick => new Color(4280427186u);

        // Token: 0x17000489 RID: 1161
        // (get) Token: 0x060037E5 RID: 14309 RVA: 0x00590F24 File Offset: 0x0058F124
        public static Color FloralWhite => new Color(4293982975u);

        // Token: 0x1700048A RID: 1162
        // (get) Token: 0x060037E6 RID: 14310 RVA: 0x00590F40 File Offset: 0x0058F140
        public static Color ForestGreen => new Color(4280453922u);

        // Token: 0x1700048B RID: 1163
        // (get) Token: 0x060037E7 RID: 14311 RVA: 0x00590F5C File Offset: 0x0058F15C
        public static Color Fuchsia => new Color(4294902015u);

        // Token: 0x1700048C RID: 1164
        // (get) Token: 0x060037E8 RID: 14312 RVA: 0x00590F78 File Offset: 0x0058F178
        public static Color Gainsboro => new Color(4292664540u);

        // Token: 0x1700048D RID: 1165
        // (get) Token: 0x060037E9 RID: 14313 RVA: 0x00590F94 File Offset: 0x0058F194
        public static Color GhostWhite => new Color(4294965496u);

        // Token: 0x1700048E RID: 1166
        // (get) Token: 0x060037EA RID: 14314 RVA: 0x00590FB0 File Offset: 0x0058F1B0
        public static Color Gold => new Color(4278245375u);

        // Token: 0x1700048F RID: 1167
        // (get) Token: 0x060037EB RID: 14315 RVA: 0x00590FCC File Offset: 0x0058F1CC
        public static Color Goldenrod => new Color(4280329690u);

        // Token: 0x17000490 RID: 1168
        // (get) Token: 0x060037EC RID: 14316 RVA: 0x00590FE8 File Offset: 0x0058F1E8
        public static Color Gray => new Color(4286611584u);

        // Token: 0x17000491 RID: 1169
        // (get) Token: 0x060037ED RID: 14317 RVA: 0x00591004 File Offset: 0x0058F204
        public static Color Green => new Color(4278222848u);

        // Token: 0x17000492 RID: 1170
        // (get) Token: 0x060037EE RID: 14318 RVA: 0x00591020 File Offset: 0x0058F220
        public static Color GreenYellow => new Color(4281335725u);

        // Token: 0x17000493 RID: 1171
        // (get) Token: 0x060037EF RID: 14319 RVA: 0x0059103C File Offset: 0x0058F23C
        public static Color Honeydew => new Color(4293984240u);

        // Token: 0x17000494 RID: 1172
        // (get) Token: 0x060037F0 RID: 14320 RVA: 0x00591058 File Offset: 0x0058F258
        public static Color HotPink => new Color(4290013695u);

        // Token: 0x17000495 RID: 1173
        // (get) Token: 0x060037F1 RID: 14321 RVA: 0x00591074 File Offset: 0x0058F274
        public static Color IndianRed => new Color(4284243149u);

        // Token: 0x17000496 RID: 1174
        // (get) Token: 0x060037F2 RID: 14322 RVA: 0x00591090 File Offset: 0x0058F290
        public static Color Indigo => new Color(4286709835u);

        // Token: 0x17000497 RID: 1175
        // (get) Token: 0x060037F3 RID: 14323 RVA: 0x005910AC File Offset: 0x0058F2AC
        public static Color Ivory => new Color(4293984255u);

        // Token: 0x17000498 RID: 1176
        // (get) Token: 0x060037F4 RID: 14324 RVA: 0x005910C8 File Offset: 0x0058F2C8
        public static Color Khaki => new Color(4287424240u);

        // Token: 0x17000499 RID: 1177
        // (get) Token: 0x060037F5 RID: 14325 RVA: 0x005910E4 File Offset: 0x0058F2E4
        public static Color Lavender => new Color(4294633190u);

        // Token: 0x1700049A RID: 1178
        // (get) Token: 0x060037F6 RID: 14326 RVA: 0x00591100 File Offset: 0x0058F300
        public static Color LavenderBlush => new Color(4294308095u);

        // Token: 0x1700049B RID: 1179
        // (get) Token: 0x060037F7 RID: 14327 RVA: 0x0059111C File Offset: 0x0058F31C
        public static Color LawnGreen => new Color(4278254716u);

        // Token: 0x1700049C RID: 1180
        // (get) Token: 0x060037F8 RID: 14328 RVA: 0x00591138 File Offset: 0x0058F338
        public static Color LemonChiffon => new Color(4291689215u);

        // Token: 0x1700049D RID: 1181
        // (get) Token: 0x060037F9 RID: 14329 RVA: 0x00591154 File Offset: 0x0058F354
        public static Color LightBlue => new Color(4293318829u);

        // Token: 0x1700049E RID: 1182
        // (get) Token: 0x060037FA RID: 14330 RVA: 0x00591170 File Offset: 0x0058F370
        public static Color LightCoral => new Color(4286611696u);

        // Token: 0x1700049F RID: 1183
        // (get) Token: 0x060037FB RID: 14331 RVA: 0x0059118C File Offset: 0x0058F38C
        public static Color LightCyan => new Color(4294967264u);

        // Token: 0x170004A0 RID: 1184
        // (get) Token: 0x060037FC RID: 14332 RVA: 0x005911A8 File Offset: 0x0058F3A8
        public static Color LightGoldenrodYellow => new Color(4292016890u);

        // Token: 0x170004A1 RID: 1185
        // (get) Token: 0x060037FD RID: 14333 RVA: 0x005911C4 File Offset: 0x0058F3C4
        public static Color LightGreen => new Color(4287688336u);

        // Token: 0x170004A2 RID: 1186
        // (get) Token: 0x060037FE RID: 14334 RVA: 0x005911E0 File Offset: 0x0058F3E0
        public static Color LightGray => new Color(4292072403u);

        // Token: 0x170004A3 RID: 1187
        // (get) Token: 0x060037FF RID: 14335 RVA: 0x005911FC File Offset: 0x0058F3FC
        public static Color LightPink => new Color(4290885375u);

        // Token: 0x170004A4 RID: 1188
        // (get) Token: 0x06003800 RID: 14336 RVA: 0x00591218 File Offset: 0x0058F418
        public static Color LightSalmon => new Color(4286226687u);

        // Token: 0x170004A5 RID: 1189
        // (get) Token: 0x06003801 RID: 14337 RVA: 0x00591234 File Offset: 0x0058F434
        public static Color LightSeaGreen => new Color(4289376800u);

        // Token: 0x170004A6 RID: 1190
        // (get) Token: 0x06003802 RID: 14338 RVA: 0x00591250 File Offset: 0x0058F450
        public static Color LightSkyBlue => new Color(4294626951u);

        // Token: 0x170004A7 RID: 1191
        // (get) Token: 0x06003803 RID: 14339 RVA: 0x0059126C File Offset: 0x0058F46C
        public static Color LightSlateGray => new Color(4288252023u);

        // Token: 0x170004A8 RID: 1192
        // (get) Token: 0x06003804 RID: 14340 RVA: 0x00591288 File Offset: 0x0058F488
        public static Color LightSteelBlue => new Color(4292789424u);

        // Token: 0x170004A9 RID: 1193
        // (get) Token: 0x06003805 RID: 14341 RVA: 0x005912A4 File Offset: 0x0058F4A4
        public static Color LightYellow => new Color(4292935679u);

        // Token: 0x170004AA RID: 1194
        // (get) Token: 0x06003806 RID: 14342 RVA: 0x005912C0 File Offset: 0x0058F4C0
        public static Color Lime => new Color(4278255360u);

        // Token: 0x170004AB RID: 1195
        // (get) Token: 0x06003807 RID: 14343 RVA: 0x005912DC File Offset: 0x0058F4DC
        public static Color LimeGreen => new Color(4281519410u);

        // Token: 0x170004AC RID: 1196
        // (get) Token: 0x06003808 RID: 14344 RVA: 0x005912F8 File Offset: 0x0058F4F8
        public static Color Linen => new Color(4293325050u);

        // Token: 0x170004AD RID: 1197
        // (get) Token: 0x06003809 RID: 14345 RVA: 0x00591314 File Offset: 0x0058F514
        public static Color Magenta => new Color(4294902015u);

        // Token: 0x170004AE RID: 1198
        // (get) Token: 0x0600380A RID: 14346 RVA: 0x00591330 File Offset: 0x0058F530
        public static Color Maroon => new Color(4278190208u);

        // Token: 0x170004AF RID: 1199
        // (get) Token: 0x0600380B RID: 14347 RVA: 0x0059134C File Offset: 0x0058F54C
        public static Color MediumAquamarine => new Color(4289383782u);

        // Token: 0x170004B0 RID: 1200
        // (get) Token: 0x0600380C RID: 14348 RVA: 0x00591368 File Offset: 0x0058F568
        public static Color MediumBlue => new Color(4291624960u);

        // Token: 0x170004B1 RID: 1201
        // (get) Token: 0x0600380D RID: 14349 RVA: 0x00591384 File Offset: 0x0058F584
        public static Color MediumOrchid => new Color(4292040122u);

        // Token: 0x170004B2 RID: 1202
        // (get) Token: 0x0600380E RID: 14350 RVA: 0x005913A0 File Offset: 0x0058F5A0
        public static Color MediumPurple => new Color(4292571283u);

        // Token: 0x170004B3 RID: 1203
        // (get) Token: 0x0600380F RID: 14351 RVA: 0x005913BC File Offset: 0x0058F5BC
        public static Color MediumSeaGreen => new Color(4285641532u);

        // Token: 0x170004B4 RID: 1204
        // (get) Token: 0x06003810 RID: 14352 RVA: 0x005913D8 File Offset: 0x0058F5D8
        public static Color MediumSlateBlue => new Color(4293814395u);

        // Token: 0x170004B5 RID: 1205
        // (get) Token: 0x06003811 RID: 14353 RVA: 0x005913F4 File Offset: 0x0058F5F4
        public static Color MediumSpringGreen => new Color(4288346624u);

        // Token: 0x170004B6 RID: 1206
        // (get) Token: 0x06003812 RID: 14354 RVA: 0x00591410 File Offset: 0x0058F610
        public static Color MediumTurquoise => new Color(4291613000u);

        // Token: 0x170004B7 RID: 1207
        // (get) Token: 0x06003813 RID: 14355 RVA: 0x0059142C File Offset: 0x0058F62C
        public static Color MediumVioletRed => new Color(4286911943u);

        // Token: 0x170004B8 RID: 1208
        // (get) Token: 0x06003814 RID: 14356 RVA: 0x00591448 File Offset: 0x0058F648
        public static Color MidnightBlue => new Color(4285536537u);

        // Token: 0x170004B9 RID: 1209
        // (get) Token: 0x06003815 RID: 14357 RVA: 0x00591464 File Offset: 0x0058F664
        public static Color MintCream => new Color(4294639605u);

        // Token: 0x170004BA RID: 1210
        // (get) Token: 0x06003816 RID: 14358 RVA: 0x00591480 File Offset: 0x0058F680
        public static Color MistyRose => new Color(4292994303u);

        // Token: 0x170004BB RID: 1211
        // (get) Token: 0x06003817 RID: 14359 RVA: 0x0059149C File Offset: 0x0058F69C
        public static Color Moccasin => new Color(4290110719u);

        // Token: 0x170004BC RID: 1212
        // (get) Token: 0x06003818 RID: 14360 RVA: 0x005914B8 File Offset: 0x0058F6B8
        public static Color NavajoWhite => new Color(4289584895u);

        // Token: 0x170004BD RID: 1213
        // (get) Token: 0x06003819 RID: 14361 RVA: 0x005914D4 File Offset: 0x0058F6D4
        public static Color Navy => new Color(4286578688u);

        // Token: 0x170004BE RID: 1214
        // (get) Token: 0x0600381A RID: 14362 RVA: 0x005914F0 File Offset: 0x0058F6F0
        public static Color OldLace => new Color(4293326333u);

        // Token: 0x170004BF RID: 1215
        // (get) Token: 0x0600381B RID: 14363 RVA: 0x0059150C File Offset: 0x0058F70C
        public static Color Olive => new Color(4278222976u);

        // Token: 0x170004C0 RID: 1216
        // (get) Token: 0x0600381C RID: 14364 RVA: 0x00591528 File Offset: 0x0058F728
        public static Color OliveDrab => new Color(4280520299u);

        // Token: 0x170004C1 RID: 1217
        // (get) Token: 0x0600381D RID: 14365 RVA: 0x00591544 File Offset: 0x0058F744
        public static Color Orange => new Color(4278232575u);

        // Token: 0x170004C2 RID: 1218
        // (get) Token: 0x0600381E RID: 14366 RVA: 0x00591560 File Offset: 0x0058F760
        public static Color OrangeRed => new Color(4278207999u);

        // Token: 0x170004C3 RID: 1219
        // (get) Token: 0x0600381F RID: 14367 RVA: 0x0059157C File Offset: 0x0058F77C
        public static Color Orchid => new Color(4292243674u);

        // Token: 0x170004C4 RID: 1220
        // (get) Token: 0x06003820 RID: 14368 RVA: 0x00591598 File Offset: 0x0058F798
        public static Color PaleGoldenrod => new Color(4289390830u);

        // Token: 0x170004C5 RID: 1221
        // (get) Token: 0x06003821 RID: 14369 RVA: 0x005915B4 File Offset: 0x0058F7B4
        public static Color PaleGreen => new Color(4288215960u);

        // Token: 0x170004C6 RID: 1222
        // (get) Token: 0x06003822 RID: 14370 RVA: 0x005915D0 File Offset: 0x0058F7D0
        public static Color PaleTurquoise => new Color(4293848751u);

        // Token: 0x170004C7 RID: 1223
        // (get) Token: 0x06003823 RID: 14371 RVA: 0x005915EC File Offset: 0x0058F7EC
        public static Color PaleVioletRed => new Color(4287852763u);

        // Token: 0x170004C8 RID: 1224
        // (get) Token: 0x06003824 RID: 14372 RVA: 0x00591608 File Offset: 0x0058F808
        public static Color PapayaWhip => new Color(4292210687u);

        // Token: 0x170004C9 RID: 1225
        // (get) Token: 0x06003825 RID: 14373 RVA: 0x00591624 File Offset: 0x0058F824
        public static Color PeachPuff => new Color(4290370303u);

        // Token: 0x170004CA RID: 1226
        // (get) Token: 0x06003826 RID: 14374 RVA: 0x00591640 File Offset: 0x0058F840
        public static Color Peru => new Color(4282353101u);

        // Token: 0x170004CB RID: 1227
        // (get) Token: 0x06003827 RID: 14375 RVA: 0x0059165C File Offset: 0x0058F85C
        public static Color Pink => new Color(4291543295u);

        // Token: 0x170004CC RID: 1228
        // (get) Token: 0x06003828 RID: 14376 RVA: 0x00591678 File Offset: 0x0058F878
        public static Color Plum => new Color(4292714717u);

        // Token: 0x170004CD RID: 1229
        // (get) Token: 0x06003829 RID: 14377 RVA: 0x00591694 File Offset: 0x0058F894
        public static Color PowderBlue => new Color(4293320880u);

        // Token: 0x170004CE RID: 1230
        // (get) Token: 0x0600382A RID: 14378 RVA: 0x005916B0 File Offset: 0x0058F8B0
        public static Color Purple => new Color(4286578816u);

        // Token: 0x170004CF RID: 1231
        // (get) Token: 0x0600382B RID: 14379 RVA: 0x005916CC File Offset: 0x0058F8CC
        public static Color Red => new Color(4278190335u);

        // Token: 0x170004D0 RID: 1232
        // (get) Token: 0x0600382C RID: 14380 RVA: 0x005916E8 File Offset: 0x0058F8E8
        public static Color RosyBrown => new Color(4287598524u);

        // Token: 0x170004D1 RID: 1233
        // (get) Token: 0x0600382D RID: 14381 RVA: 0x00591704 File Offset: 0x0058F904
        public static Color RoyalBlue => new Color(4292962625u);

        // Token: 0x170004D2 RID: 1234
        // (get) Token: 0x0600382E RID: 14382 RVA: 0x00591720 File Offset: 0x0058F920
        public static Color SaddleBrown => new Color(4279453067u);

        // Token: 0x170004D3 RID: 1235
        // (get) Token: 0x0600382F RID: 14383 RVA: 0x0059173C File Offset: 0x0058F93C
        public static Color Salmon => new Color(4285694202u);

        // Token: 0x170004D4 RID: 1236
        // (get) Token: 0x06003830 RID: 14384 RVA: 0x00591758 File Offset: 0x0058F958
        public static Color SandyBrown => new Color(4284523764u);

        // Token: 0x170004D5 RID: 1237
        // (get) Token: 0x06003831 RID: 14385 RVA: 0x00591774 File Offset: 0x0058F974
        public static Color SeaGreen => new Color(4283927342u);

        // Token: 0x170004D6 RID: 1238
        // (get) Token: 0x06003832 RID: 14386 RVA: 0x00591790 File Offset: 0x0058F990
        public static Color SeaShell => new Color(4293850623u);

        // Token: 0x170004D7 RID: 1239
        // (get) Token: 0x06003833 RID: 14387 RVA: 0x005917AC File Offset: 0x0058F9AC
        public static Color Sienna => new Color(4281160352u);

        // Token: 0x170004D8 RID: 1240
        // (get) Token: 0x06003834 RID: 14388 RVA: 0x005917C8 File Offset: 0x0058F9C8
        public static Color Silver => new Color(4290822336u);

        // Token: 0x170004D9 RID: 1241
        // (get) Token: 0x06003835 RID: 14389 RVA: 0x005917E4 File Offset: 0x0058F9E4
        public static Color SkyBlue => new Color(4293643911u);

        // Token: 0x170004DA RID: 1242
        // (get) Token: 0x06003836 RID: 14390 RVA: 0x00591800 File Offset: 0x0058FA00
        public static Color SlateBlue => new Color(4291648106u);

        // Token: 0x170004DB RID: 1243
        // (get) Token: 0x06003837 RID: 14391 RVA: 0x0059181C File Offset: 0x0058FA1C
        public static Color SlateGray => new Color(4287660144u);

        // Token: 0x170004DC RID: 1244
        // (get) Token: 0x06003838 RID: 14392 RVA: 0x00591838 File Offset: 0x0058FA38
        public static Color Snow => new Color(4294638335u);

        // Token: 0x170004DD RID: 1245
        // (get) Token: 0x06003839 RID: 14393 RVA: 0x00591854 File Offset: 0x0058FA54
        public static Color SpringGreen => new Color(4286578432u);

        // Token: 0x170004DE RID: 1246
        // (get) Token: 0x0600383A RID: 14394 RVA: 0x00591870 File Offset: 0x0058FA70
        public static Color SteelBlue => new Color(4290019910u);

        // Token: 0x170004DF RID: 1247
        // (get) Token: 0x0600383B RID: 14395 RVA: 0x0059188C File Offset: 0x0058FA8C
        public static Color Tan => new Color(4287411410u);

        // Token: 0x170004E0 RID: 1248
        // (get) Token: 0x0600383C RID: 14396 RVA: 0x005918A8 File Offset: 0x0058FAA8
        public static Color Teal => new Color(4286611456u);

        // Token: 0x170004E1 RID: 1249
        // (get) Token: 0x0600383D RID: 14397 RVA: 0x005918C4 File Offset: 0x0058FAC4
        public static Color Thistle => new Color(4292394968u);

        // Token: 0x170004E2 RID: 1250
        // (get) Token: 0x0600383E RID: 14398 RVA: 0x005918E0 File Offset: 0x0058FAE0
        public static Color Tomato => new Color(4282868735u);

        // Token: 0x170004E3 RID: 1251
        // (get) Token: 0x0600383F RID: 14399 RVA: 0x005918FC File Offset: 0x0058FAFC
        public static Color Turquoise => new Color(4291878976u);

        // Token: 0x170004E4 RID: 1252
        // (get) Token: 0x06003840 RID: 14400 RVA: 0x00591918 File Offset: 0x0058FB18
        public static Color Violet => new Color(4293821166u);

        // Token: 0x170004E5 RID: 1253
        // (get) Token: 0x06003841 RID: 14401 RVA: 0x00591934 File Offset: 0x0058FB34
        public static Color Wheat => new Color(4289978101u);

        // Token: 0x170004E6 RID: 1254
        // (get) Token: 0x06003842 RID: 14402 RVA: 0x00591950 File Offset: 0x0058FB50
        public static Color White => new Color(uint.MaxValue);

        // Token: 0x170004E7 RID: 1255
        // (get) Token: 0x06003843 RID: 14403 RVA: 0x00591968 File Offset: 0x0058FB68
        public static Color WhiteSmoke => new Color(4294309365u);

        // Token: 0x170004E8 RID: 1256
        // (get) Token: 0x06003844 RID: 14404 RVA: 0x00591984 File Offset: 0x0058FB84
        public static Color Yellow => new Color(4278255615u);

        // Token: 0x170004E9 RID: 1257
        // (get) Token: 0x06003845 RID: 14405 RVA: 0x005919A0 File Offset: 0x0058FBA0
        public static Color YellowGreen => new Color(4281519514u);

        // Token: 0x06003846 RID: 14406 RVA: 0x005919BC File Offset: 0x0058FBBC
        public Color(uint packedValue)
        {
            this.packedValue = packedValue;
        }

        // Token: 0x06003847 RID: 14407 RVA: 0x005919C8 File Offset: 0x0058FBC8
        public Color(int r, int g, int b)
        {
            bool flag = ((r | g | b) & -256) != 0;
            if (flag)
            {
                r = Color.ClampToByte64(r);
                g = Color.ClampToByte64(g);
                b = Color.ClampToByte64(b);
            }
            g <<= 8;
            b <<= 16;
            packedValue = (uint)(r | g | b | -16777216);
        }

        // Token: 0x06003848 RID: 14408 RVA: 0x00591A24 File Offset: 0x0058FC24
        public Color(int r, int g, int b, int a)
        {
            bool flag = ((r | g | b | a) & -256) != 0;
            if (flag)
            {
                r = Color.ClampToByte32(r);
                g = Color.ClampToByte32(g);
                b = Color.ClampToByte32(b);
                a = Color.ClampToByte32(a);
            }
            g <<= 8;
            b <<= 16;
            a <<= 24;
            packedValue = (uint)(r | g | b | a);
        }

        // Token: 0x06003849 RID: 14409 RVA: 0x00591A8C File Offset: 0x0058FC8C
        public Color(float r, float g, float b)
        {
            packedValue = Color.PackHelper(r, g, b, 1f);
        }

        // Token: 0x0600384A RID: 14410 RVA: 0x00591AA4 File Offset: 0x0058FCA4
        public Color(float r, float g, float b, float a)
        {
            packedValue = Color.PackHelper(r, g, b, a);
        }

        // Token: 0x0600384B RID: 14411 RVA: 0x00591AB8 File Offset: 0x0058FCB8
        public Color(Vector3 vector)
        {
            packedValue = Color.PackHelper(vector.X, vector.Y, vector.Z, 1f);
        }

        // Token: 0x0600384C RID: 14412 RVA: 0x00591AE0 File Offset: 0x0058FCE0
        public Color(Vector4 vector)
        {
            packedValue = Color.PackHelper(vector.X, vector.Y, vector.Z, vector.W);
        }

        // Token: 0x0600384D RID: 14413 RVA: 0x00591B08 File Offset: 0x0058FD08
        void IPackedVector.PackFromVector4(Vector4 vector)
        {
            packedValue = Color.PackHelper(vector.X, vector.Y, vector.Z, vector.W);
        }

        // Token: 0x0600384E RID: 14414 RVA: 0x00591B30 File Offset: 0x0058FD30
        public static Color FromNonPremultiplied(Vector4 vector)
        {
            Color result;
            result.packedValue = Color.PackHelper(vector.X * vector.W, vector.Y * vector.W, vector.Z * vector.W, vector.W);
            return result;
        }

        // Token: 0x0600384F RID: 14415 RVA: 0x00591B7C File Offset: 0x0058FD7C
        public static Color FromNonPremultiplied(int r, int g, int b, int a)
        {
            r = Color.ClampToByte64(r * (long)a / 255L);
            g = Color.ClampToByte64(g * (long)a / 255L);
            b = Color.ClampToByte64(b * (long)a / 255L);
            a = Color.ClampToByte32(a);
            g <<= 8;
            b <<= 16;
            a <<= 24;
            Color result;
            result.packedValue = (uint)(r | g | b | a);
            return result;
        }

        // Token: 0x06003850 RID: 14416 RVA: 0x00591BF0 File Offset: 0x0058FDF0
        public static uint PackHelper(float vectorX, float vectorY, float vectorZ, float vectorW)
        {
            uint num = Color.PackUNorm(255f, vectorX);
            uint num2 = Color.PackUNorm(255f, vectorY) << 8;
            uint num3 = Color.PackUNorm(255f, vectorZ) << 16;
            uint num4 = Color.PackUNorm(255f, vectorW) << 24;
            return num | num2 | num3 | num4;
        }

        // Token: 0x06003851 RID: 14417 RVA: 0x00591C44 File Offset: 0x0058FE44
        public static uint PackUNorm(float bitmask, float value)
        {
            value *= bitmask;
            return (uint)Color.ClampAndRound(value, 0f, bitmask);
        }

        // Token: 0x06003852 RID: 14418 RVA: 0x00591C68 File Offset: 0x0058FE68
        private static double ClampAndRound(float value, float min, float max)
        {
            bool flag = float.IsNaN(value);
            double result;
            if (flag)
            {
                result = 0.0;
            }
            else
            {
                bool flag2 = float.IsInfinity(value);
                if (flag2)
                {
                    result = float.IsNegativeInfinity(value) ? min : max;
                }
                else
                {
                    bool flag3 = value < min;
                    if (flag3)
                    {
                        result = min;
                    }
                    else
                    {
                        bool flag4 = value > max;
                        if (flag4)
                        {
                            result = max;
                        }
                        else
                        {
                            result = Math.Round(value);
                        }
                    }
                }
            }
            return result;
        }

        // Token: 0x06003853 RID: 14419 RVA: 0x00591CD4 File Offset: 0x0058FED4
        private static int ClampToByte32(int value)
        {
            bool flag = value < 0;
            int result;
            if (flag)
            {
                result = 0;
            }
            else
            {
                bool flag2 = value > 255;
                if (flag2)
                {
                    result = 255;
                }
                else
                {
                    result = value;
                }
            }
            return result;
        }

        // Token: 0x06003854 RID: 14420 RVA: 0x00591D0C File Offset: 0x0058FF0C
        private static int ClampToByte64(long value)
        {
            bool flag = value < 0L;
            int result;
            if (flag)
            {
                result = 0;
            }
            else
            {
                bool flag2 = value > 255L;
                if (flag2)
                {
                    result = 255;
                }
                else
                {
                    result = (int)value;
                }
            }
            return result;
        }

        // Token: 0x06003855 RID: 14421 RVA: 0x00591D44 File Offset: 0x0058FF44
        public Vector3 ToVector3()
        {
            Vector3 result;
            result.X = Color.UnpackUNorm(255u, packedValue);
            result.Y = Color.UnpackUNorm(255u, packedValue >> 8);
            result.Z = Color.UnpackUNorm(255u, packedValue >> 16);
            return result;
        }

        // Token: 0x06003856 RID: 14422 RVA: 0x00591DA4 File Offset: 0x0058FFA4
        public Vector4 ToVector4()
        {
            Vector4 result;
            result.X = Color.UnpackUNorm(255u, packedValue);
            result.Y = Color.UnpackUNorm(255u, packedValue >> 8);
            result.Z = Color.UnpackUNorm(255u, packedValue >> 16);
            result.W = Color.UnpackUNorm(255u, packedValue >> 24);
            return result;
        }

        // Token: 0x06003857 RID: 14423 RVA: 0x00591E1C File Offset: 0x0059001C
        public static float UnpackUNorm(uint bitmask, uint value)
        {
            value &= bitmask;
            return value / bitmask;
        }

        // Token: 0x06003858 RID: 14424 RVA: 0x00591E38 File Offset: 0x00590038
        public static Color Lerp(Color value1, Color value2, float amount)
        {
            uint num = value1.packedValue;
            uint num2 = value2.packedValue;
            int num3 = (byte)num;
            int num4 = (byte)(num >> 8);
            int num5 = (byte)(num >> 16);
            int num6 = (byte)(num >> 24);
            int num7 = (byte)num2;
            int num8 = (byte)(num2 >> 8);
            int num9 = (byte)(num2 >> 16);
            int num10 = (byte)(num2 >> 24);
            int num11 = (int)Color.PackUNorm(65536f, amount);
            int num12 = num3 + ((num7 - num3) * num11 >> 16);
            int num13 = num4 + ((num8 - num4) * num11 >> 16);
            int num14 = num5 + ((num9 - num5) * num11 >> 16);
            int num15 = num6 + ((num10 - num6) * num11 >> 16);
            Color result;
            result.packedValue = (uint)(num12 | num13 << 8 | num14 << 16 | num15 << 24);
            return result;
        }

        // Token: 0x06003859 RID: 14425 RVA: 0x00591EF0 File Offset: 0x005900F0
        public static Color Multiply(Color value, float scale)
        {
            uint num = value.packedValue;
            uint num2 = (byte)num;
            uint num3 = (byte)(num >> 8);
            uint num4 = (byte)(num >> 16);
            uint num5 = (byte)(num >> 24);
            scale *= 65536f;
            bool flag = scale < 0f;
            uint num6;
            if (flag)
            {
                num6 = 0u;
            }
            else
            {
                bool flag2 = scale > 16777215f;
                if (flag2)
                {
                    num6 = 16777215u;
                }
                else
                {
                    num6 = (uint)scale;
                }
            }
            num2 = num2 * num6 >> 16;
            num3 = num3 * num6 >> 16;
            num4 = num4 * num6 >> 16;
            num5 = num5 * num6 >> 16;
            bool flag3 = num2 > 255u;
            if (flag3)
            {
                num2 = 255u;
            }
            bool flag4 = num3 > 255u;
            if (flag4)
            {
                num3 = 255u;
            }
            bool flag5 = num4 > 255u;
            if (flag5)
            {
                num4 = 255u;
            }
            bool flag6 = num5 > 255u;
            if (flag6)
            {
                num5 = 255u;
            }
            Color result;
            result.packedValue = (num2 | num3 << 8 | num4 << 16 | num5 << 24);
            return result;
        }

        // Token: 0x0600385A RID: 14426 RVA: 0x00591FF4 File Offset: 0x005901F4
        public static Color operator *(Color value, float scale)
        {
            uint num = value.packedValue;
            uint num2 = (byte)num;
            uint num3 = (byte)(num >> 8);
            uint num4 = (byte)(num >> 16);
            uint num5 = (byte)(num >> 24);
            scale *= 65536f;
            bool flag = scale < 0f;
            uint num6;
            if (flag)
            {
                num6 = 0u;
            }
            else
            {
                bool flag2 = scale > 16777215f;
                if (flag2)
                {
                    num6 = 16777215u;
                }
                else
                {
                    num6 = (uint)scale;
                }
            }
            num2 = num2 * num6 >> 16;
            num3 = num3 * num6 >> 16;
            num4 = num4 * num6 >> 16;
            num5 = num5 * num6 >> 16;
            bool flag3 = num2 > 255u;
            if (flag3)
            {
                num2 = 255u;
            }
            bool flag4 = num3 > 255u;
            if (flag4)
            {
                num3 = 255u;
            }
            bool flag5 = num4 > 255u;
            if (flag5)
            {
                num4 = 255u;
            }
            bool flag6 = num5 > 255u;
            if (flag6)
            {
                num5 = 255u;
            }
            Color result;
            result.packedValue = (num2 | num3 << 8 | num4 << 16 | num5 << 24);
            return result;
        }

        // Token: 0x0600385B RID: 14427 RVA: 0x005920F8 File Offset: 0x005902F8
        public override string ToString()
        {
            return string.Format(CultureInfo.CurrentCulture, "{{R:{0} G:{1} B:{2} A:{3}}}", new object[]
            {
                R,
                G,
                B,
                A
            });
        }

        // Token: 0x0600385C RID: 14428 RVA: 0x00592158 File Offset: 0x00590358
        public override int GetHashCode()
        {
            return packedValue.GetHashCode();
        }

        // Token: 0x0600385D RID: 14429 RVA: 0x00592178 File Offset: 0x00590378
        public override bool Equals(object obj)
        {
            return obj is Color && Equals((Color)obj);
        }

        // Token: 0x0600385E RID: 14430 RVA: 0x005921A4 File Offset: 0x005903A4
        public bool Equals(Color other)
        {
            return packedValue.Equals(other.packedValue);
        }

        // Token: 0x0600385F RID: 14431 RVA: 0x005921C8 File Offset: 0x005903C8
        public static bool operator ==(Color a, Color b)
        {
            return a.Equals(b);
        }

        // Token: 0x06003860 RID: 14432 RVA: 0x005921E4 File Offset: 0x005903E4
        public static bool operator !=(Color a, Color b)
        {
            return !a.Equals(b);
        }

        // Token: 0x04006176 RID: 24950
        private uint packedValue;
    }
}
