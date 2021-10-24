using System;
using TrProtocol.Serializers;

namespace TrProtocol
{
    // Token: 0x02000250 RID: 592
    public enum MessageID : byte
    {
        // Token: 0x04002CFD RID: 11517
        NeverCalled = 0,

        // Token: 0x04002CFE RID: 11518
        ClientHello = 1,

        // Token: 0x04002CFF RID: 11519
        Kick = 2,

        // Token: 0x04002D00 RID: 11520
        LoadPlayer = 3,

        // Token: 0x04002D01 RID: 11521
        SyncPlayer = 4,

        // Token: 0x04002D02 RID: 11522
        SyncEquipment = 5,

        // Token: 0x04002D03 RID: 11523
        RequestWorldInfo = 6,

        // Token: 0x04002D04 RID: 11524
        WorldData = 7,

        // Token: 0x04002D05 RID: 11525
        RequestTileData = 8,

        // Token: 0x04002D06 RID: 11526
        StatusText = 9,

        // Token: 0x04002D07 RID: 11527
        TileSection = 10,

        // Token: 0x04002D08 RID: 11528
        FrameSection = 11,

        // Token: 0x04002D09 RID: 11529
        SpawnPlayer = 12,

        // Token: 0x04002D0A RID: 11530
        PlayerControls = 13,

        // Token: 0x04002D0B RID: 11531
        PlayerActive = 14,

        // Token: 0x04002D0C RID: 11532
        Unused15 = 15,

        // Token: 0x04002D0D RID: 11533
        PlayerHealth = 16,

        // Token: 0x04002D0E RID: 11534
        TileChange = 17,

        // Token: 0x04002D0F RID: 11535
        MenuSunMoon = 18,

        // Token: 0x04002D10 RID: 11536
        ChangeDoor = 19,

        // Token: 0x04002D11 RID: 11537
        TileSquare = 20,

        // Token: 0x04002D12 RID: 11538
        SyncItem = 21,

        // Token: 0x04002D13 RID: 11539
        ItemOwner = 22,

        // Token: 0x04002D14 RID: 11540
        SyncNPC = 23,

        // Token: 0x04002D15 RID: 11541
        UnusedStrikeNPC = 24,

        // Token: 0x04002D16 RID: 11542
        [Obsolete("Deprecated. Use NetTextModule instead.")]
        ChatText = 25,

        // Token: 0x04002D17 RID: 11543
        [Obsolete("Deprecated.")]
        HurtPlayer = 26,

        // Token: 0x04002D18 RID: 11544
        SyncProjectile = 27,

        // Token: 0x04002D19 RID: 11545
        StrikeNPC = 28,

        // Token: 0x04002D1A RID: 11546
        KillProjectile = 29,

        // Token: 0x04002D1B RID: 11547
        PlayerPvP = 30,

        // Token: 0x04002D1C RID: 11548
        RequestChestOpen = 31,

        // Token: 0x04002D1D RID: 11549
        SyncChestItem = 32,

        // Token: 0x04002D1E RID: 11550
        SyncPlayerChest = 33,

        // Token: 0x04002D1F RID: 11551
        ChestUpdates = 34,

        // Token: 0x04002D20 RID: 11552
        HealEffect = 35,

        // Token: 0x04002D21 RID: 11553
        PlayerZone = 36,

        // Token: 0x04002D22 RID: 11554
        RequestPassword = 37,

        // Token: 0x04002D23 RID: 11555
        SendPassword = 38,

        // Token: 0x04002D24 RID: 11556
        ResetItemOwner = 39,

        // Token: 0x04002D25 RID: 11557
        PlayerTalkingNPC = 40,

        // Token: 0x04002D26 RID: 11558
        ItemAnimation = 41,

        // Token: 0x04002D27 RID: 11559
        PlayerMana = 42,

        // Token: 0x04002D28 RID: 11560
        ManaEffect = 43,

        // Token: 0x04002D29 RID: 11561
        [Obsolete("Deprecated.")]
        KillPlayer = 44,

        // Token: 0x04002D2A RID: 11562
        PlayerTeam = 45,

        // Token: 0x04002D2B RID: 11563
        RequestReadSign = 46,

        // Token: 0x04002D2C RID: 11564
        ReadSign = 47,

        // Token: 0x04002D2D RID: 11565
        [Obsolete("Deprecated. Use NetLiquidModule instead.")]
        LiquidUpdate = 48,

        // Token: 0x04002D2E RID: 11566
        StartPlaying = 49,

        // Token: 0x04002D2F RID: 11567
        PlayerBuffs = 50,

        // Token: 0x04002D30 RID: 11568
        Assorted1 = 51,

        // Token: 0x04002D31 RID: 11569
        Unlock = 52,

        // Token: 0x04002D32 RID: 11570
        AddNPCBuff = 53,

        // Token: 0x04002D33 RID: 11571
        SendNPCBuffs = 54,

        // Token: 0x04002D34 RID: 11572
        AddPlayerBuff = 55,

        // Token: 0x04002D35 RID: 11573
        SyncNPCName = 56,

        // Token: 0x04002D36 RID: 11574
        TileCounts = 57,

        // Token: 0x04002D37 RID: 11575
        PlayNote = 58,

        // Token: 0x04002D38 RID: 11576
        HitSwitch = 59,

        // Token: 0x04002D39 RID: 11577
        NPCHome = 60,

        // Token: 0x04002D3A RID: 11578
        SpawnBoss = 61,

        // Token: 0x04002D3B RID: 11579
        Dodge = 62,

        // Token: 0x04002D3C RID: 11580
        PaintTile = 63,

        // Token: 0x04002D3D RID: 11581
        PaintWall = 64,

        // Token: 0x04002D3E RID: 11582
        Teleport = 65,

        // Token: 0x04002D3F RID: 11583
        SpiritHeal = 66,

        // Token: 0x04002D40 RID: 11584
        Unused67 = 67,

        // Token: 0x04002D41 RID: 11585
        ClientUUID = 68,

        // Token: 0x04002D42 RID: 11586
        ChestName = 69,

        // Token: 0x04002D43 RID: 11587
        BugCatching = 70,

        // Token: 0x04002D44 RID: 11588
        BugReleasing = 71,

        // Token: 0x04002D45 RID: 11589
        TravelMerchantItems = 72,

        // Token: 0x04002D46 RID: 11590
        TeleportationPotion = 73,

        // Token: 0x04002D47 RID: 11591
        AnglerQuest = 74,

        // Token: 0x04002D48 RID: 11592
        AnglerQuestFinished = 75,

        // Token: 0x04002D49 RID: 11593
        AnglerQuestCountSync = 76,

        // Token: 0x04002D4A RID: 11594
        TemporaryAnimation = 77,

        // Token: 0x04002D4B RID: 11595
        InvasionProgressReport = 78,

        // Token: 0x04002D4C RID: 11596
        PlaceObject = 79,

        // Token: 0x04002D4D RID: 11597
        SyncPlayerChestIndex = 80,

        // Token: 0x04002D4E RID: 11598
        CombatTextInt = 81,

        // Token: 0x04002D4F RID: 11599
        NetModules = 82,

        // Token: 0x04002D50 RID: 11600
        NPCKillCountDeathTally = 83,

        // Token: 0x04002D51 RID: 11601
        PlayerStealth = 84,

        // Token: 0x04002D52 RID: 11602
        QuickStackChests = 85,

        // Token: 0x04002D53 RID: 11603
        TileEntitySharing = 86,

        // Token: 0x04002D54 RID: 11604
        TileEntityPlacement = 87,

        // Token: 0x04002D55 RID: 11605
        ItemTweaker = 88,

        // Token: 0x04002D56 RID: 11606
        ItemFrameTryPlacing = 89,

        // Token: 0x04002D57 RID: 11607
        InstancedItem = 90,

        // Token: 0x04002D58 RID: 11608
        SyncEmoteBubble = 91,

        // Token: 0x04002D59 RID: 11609
        SyncExtraValue = 92,

        // Token: 0x04002D5A RID: 11610
        SocialHandshake = 93,

        // Token: 0x04002D5B RID: 11611
        Unused94 = 94,

        // Token: 0x04002D5C RID: 11612
        MurderSomeoneElsesProjectile = 95,

        // Token: 0x04002D5D RID: 11613
        TeleportPlayerThroughPortal = 96,

        // Token: 0x04002D5E RID: 11614
        AchievementMessageNPCKilled = 97,

        // Token: 0x04002D5F RID: 11615
        AchievementMessageEventHappened = 98,

        // Token: 0x04002D60 RID: 11616
        MinionRestTargetUpdate = 99,

        // Token: 0x04002D61 RID: 11617
        TeleportNPCThroughPortal = 100,

        // Token: 0x04002D62 RID: 11618
        UpdateTowerShieldStrengths = 101,

        // Token: 0x04002D63 RID: 11619
        NebulaLevelupRequest = 102,

        // Token: 0x04002D64 RID: 11620
        MoonlordCountdown = 103,

        // Token: 0x04002D65 RID: 11621
        ShopOverride = 104,

        // Token: 0x04002D66 RID: 11622
        GemLockToggle = 105,

        // Token: 0x04002D67 RID: 11623
        PoofOfSmoke = 106,

        // Token: 0x04002D68 RID: 11624
        SmartTextMessage = 107,

        // Token: 0x04002D69 RID: 11625
        WiredCannonShot = 108,

        // Token: 0x04002D6A RID: 11626
        MassWireOperation = 109,

        // Token: 0x04002D6B RID: 11627
        MassWireOperationPay = 110,

        // Token: 0x04002D6C RID: 11628
        ToggleParty = 111,

        // Token: 0x04002D6D RID: 11629
        SpecialFX = 112,

        // Token: 0x04002D6E RID: 11630
        CrystalInvasionStart = 113,

        // Token: 0x04002D6F RID: 11631
        CrystalInvasionWipeAllTheThings = 114,

        // Token: 0x04002D70 RID: 11632
        MinionAttackTargetUpdate = 115,

        // Token: 0x04002D71 RID: 11633
        CrystalInvasionSendWaitTime = 116,

        // Token: 0x04002D72 RID: 11634
        PlayerHurtV2 = 117,

        // Token: 0x04002D73 RID: 11635
        PlayerDeathV2 = 118,

        // Token: 0x04002D74 RID: 11636
        CombatTextString = 119,

        // Token: 0x04003A79 RID: 14969
        Emoji = 120,

        // Token: 0x04003A7A RID: 14970
        TEDisplayDollItemSync = 121,

        // Token: 0x04003A7B RID: 14971
        RequestTileEntityInteraction = 122,

        // Token: 0x04003A7C RID: 14972
        WeaponsRackTryPlacing = 123,

        // Token: 0x04003A7D RID: 14973
        TEHatRackItemSync = 124,

        // Token: 0x04003A7E RID: 14974
        SyncTilePicking = 125,

        // Token: 0x04003A7F RID: 14975
        SyncRevengeMarker = 126,

        // Token: 0x04003A80 RID: 14976
        RemoveRevengeMarker = 127,

        // Token: 0x04003A81 RID: 14977
        LandGolfBallInCup = 128,

        // Token: 0x04003A82 RID: 14978
        FinishedConnectingToServer = 129,

        // Token: 0x04003A83 RID: 14979
        FishOutNPC = 130,

        // Token: 0x04003A84 RID: 14980
        TamperWithNPC = 131,

        // Token: 0x04003A85 RID: 14981
        PlayLegacySound = 132,

        // Token: 0x04003A86 RID: 14982
        FoodPlatterTryPlacing = 133,

        // Token: 0x04003A87 RID: 14983
        UpdatePlayerLuckFactors = 134,

        // Token: 0x04003A88 RID: 14984
        DeadPlayer = 135,

        // Token: 0x04003A89 RID: 14985
        SyncCavernMonsterType = 136,

        // Token: 0x04003A8A RID: 14986
        RequestNPCBuffRemoval = 137,

        // Token: 0x04003A8B RID: 14987
        ClientSyncedInventory = 138,

        // Token: 0x04003A8C RID: 14988
        SetCountsAsHostForGameplay = 139,

        // Token: 0x04003A8D RID: 14989
        SetMiscEventValues = 140,

        // Token: 0x04003A8E RID: 14990
        Count = 141
    }
}