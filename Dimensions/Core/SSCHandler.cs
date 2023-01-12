using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using TrProtocol;
using TrProtocol.Packets;

namespace Dimensions.Core
{
    public class SSCHandler : ClientHandler
    {
        private enum State
        {
            FreshConnection,
            SSC,
            NonSSC
        }
        private State current = State.FreshConnection;
        private const int maxInventory = 350;
        private SyncPlayer syncPlayer;
        private PlayerMana playerMana;
        private PlayerHealth playerHealth;
        private AnglerQuestCountSync anglerQuest;
        private byte currentSlot;
        private readonly SyncEquipment[] equipments = new SyncEquipment[maxInventory];
        public override void OnC2SPacket(PacketReceiveArgs args)
        {
            if (current == State.SSC) return;
            
            switch (args.Packet)
            {
                case SyncEquipment equip:
                    equipments[equip.ItemSlot] = equip;
                    break;
                case SyncPlayer plr:
                    syncPlayer = plr;
                    break;
                case PlayerMana mana:
                    playerMana = mana;
                    break;
                case PlayerHealth health:
                    playerHealth = health;
                    break;
                case AnglerQuestCountSync angler:
                    anglerQuest = angler;
                    break;
            }
        }

        private IEnumerable<IPlayerSlot> GetRestores()
        {
            foreach (var equip in equipments)
                yield return equip;
            yield return syncPlayer;
            yield return playerMana;
            yield return playerHealth;
            yield return anglerQuest;
        }
        
        private void RestoreCharacter()
        {
            foreach (var restore in GetRestores())
            {
                if (restore == null) continue;
                restore.PlayerSlot = currentSlot;
                Parent.SendClient(restore as Packet);
            }
        }
        
        public override void OnS2CPacket(PacketReceiveArgs args)
        {
            switch (args.Packet)
            {
                case LoadPlayer plr:
                    currentSlot = plr.PlayerSlot;
                    break;
                case WorldData data:
                    var isSSC = data.EventInfo1[6];

                    if (current == State.NonSSC && isSSC)
                        RestoreCharacter();

                    current = isSSC ? State.SSC : State.NonSSC;
                    break;
            }
        }
    }
}
