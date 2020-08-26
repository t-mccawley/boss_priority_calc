from enum import IntEnum
import collections
import matplotlib.pyplot as plt
import numpy as np

verbose = True

class SpecClass(IntEnum):
    NONE = 0
    RESTO_DRUID = 1
    FERAL_DRUID = 2
    MARKS_HUNTER = 3
    FIRE_MAGE = 4
    HOLY_PALADIN = 5
    HOLY_PRIEST = 6
    COMBAT_ROGUE = 7
    RESTO_SHAMAN = 8
    ANY_WARLOCK = 9
    PROT_THREAT_WARRIOR = 10
    FURY_WARRIOR = 11
    SIZE = 12

class Slot(IntEnum):
    NONE = 0
    HEAD = 1
    NECK = 2
    SHOULDER = 3
    CHEST = 4
    WAIST = 5
    LEGS = 6
    FEET = 7
    WRISTS = 8
    HANDS = 9
    FINGER = 10
    TRINKET = 11
    BACK = 12
    MAIN_HAND = 13
    OFF_HAND = 14
    TWO_HAND = 15
    RANGED = 16
    ZG_ENCHANTS = 17
    SIZE = 19

class Raid(IntEnum):
    ONY = 0
    MC = 1
    BWL = 2
    ZG = 3
    AQ20 = 4
    AQ40 = 5
    SIZE = 6

RaidToBossMap = [[]]*Raid.SIZE
RaidToBossMap[Raid.ONY] = ["Onyxia"]
RaidToBossMap[Raid.MC] = ["Lucifron","Magmadar","Gehennas","Garr","Baron Geddon","Shazzrah","Golemagg the Incinerator","Sulfuron Harbinger","Majordomo Executus","Ragnaros","MC Trash"]
RaidToBossMap[Raid.BWL] = ["Razorgore the Untamed","Vaelastrasz the Corrupt","Broodlord Lashlayer","Firemaw","Ebonroc","Flamegor","Chromaggus","Nefarian","BWL Trash"]
RaidToBossMap[Raid.ZG] = ["Jin'do the Hexxer","High Priest Thekal","Bloodlord Mandokir","High Priestess Mar'li","High Priest Venoxis","High Priestess Jeklik","Edge of Madness","High Priestess Arlokk","Hakkar","Gahz'ranka"]
RaidToBossMap[Raid.AQ20] = ["Kurinnaxx","General Rajaxx","Moam","Buru the Gorger","Ayamiss the Hunter","Ossirian the Unscarred","AQ20 Trash"]
RaidToBossMap[Raid.AQ40] = ["The Prophet Skeram","Vem","Princess Yauj","Lord Kri","Battleguard Sartura","Fankriss the Unyielding","Viscidus","Princess Huhuran","Twin Emperors","Ouro","C'Thun","AQ40 Trash"]

class Character:

    def __init__(self,name,spec_class,head,neck,shoulder,chest,waist,legs,feet,wrist,hands,fingers,trinkets,back,mh,oh,th,ranged,zg_enchants):
        # character name
        self.name = name
        # character SpecClass
        self.spec_class = spec_class
        # map from slot to list of names of items that character has
        self.gear = [[]]*Slot.SIZE
        self.gear[Slot.HEAD] = head
        self.gear[Slot.NECK] = neck
        self.gear[Slot.SHOULDER] = shoulder
        self.gear[Slot.CHEST] = chest
        self.gear[Slot.WAIST] = waist
        self.gear[Slot.LEGS] = legs
        self.gear[Slot.FEET] = feet
        self.gear[Slot.WRISTS] = wrist
        self.gear[Slot.HANDS] = hands
        self.gear[Slot.FINGER] = fingers
        self.gear[Slot.TRINKET] = trinkets
        self.gear[Slot.BACK] = back
        self.gear[Slot.MAIN_HAND] = mh
        self.gear[Slot.OFF_HAND] = oh
        self.gear[Slot.TWO_HAND] = th
        self.gear[Slot.RANGED] = ranged
        self.gear[Slot.ZG_ENCHANTS] = zg_enchants #count
        
class Loot:

    def __init__(self,name,slot):
        self.name = None # string name
        self.slot = slot # Slot enum
        self.ep_map = [0]*SpecClass.SIZE # map from SpecClass to ep value

    def addEP(self,spec_class,ep):
        self.ep_map[spec_class] = ep

class Boss:

    def __init__(self,name,raid,clear_time):
        self.name = name # boss name
        self.raid = raid # Raid enum
        self.clear_time = clear_time # minutes to clear boss from start of dungeon
        self.loot_table = [] # array of names of items dropped by this boss
        self.loot_drop_chance = {} # map from loot name to drop chance of the item in %
        self.enu = {} # expected normalized upgrade for a raid from this boss (map from character name to enu)
        self.mean_enupm = 0 # mean expected normalized upgrade per minute minute for boss

class BossPrioCalc:

    def __init__(self):
        self.loot_db = {} # map of loot name to Loot object
        self.bosses = {} # map of boss names to Boss object
        self.raid = {} # map of character names to Character object 
        self.ep_bis = { # map from SpecClass enum to BiS ep possible in P6 for that SpecClass
            SpecClass.RESTO_DRUID:1685,
            SpecClass.FERAL_DRUID:3586,
            SpecClass.MARKS_HUNTER:3267,
            SpecClass.FIRE_MAGE:1149,
            SpecClass.HOLY_PALADIN:0,
            SpecClass.HOLY_PRIEST:2135,
            SpecClass.COMBAT_ROGUE:4054,
            SpecClass.RESTO_SHAMAN:2220,
            SpecClass.ANY_WARLOCK:1226,
            SpecClass.PROT_THREAT_WARRIOR:2858,
            SpecClass.FURY_WARRIOR:3873,
        }

    def addBoss(self,name,raid,clear_time):
        self.bosses[name] = Boss(name,raid,clear_time)

    def addLoot(self,boss_list,loot_name,slot,drop_chance_list,ep_map):
        # add actual object to loot_db
        loot = Loot(loot_name,slot)
        # construct ep_map
        for spec_class in ep_map:
            loot.addEP(spec_class,ep_map[spec_class])

        # check if loot already exists
        if loot_name in self.loot_db:
            print("{} is already in loot_db".format(loot_name))
            raise RuntimeError("Duplicate loot_name found")

        self.loot_db[loot_name] = loot

        # add to bosses
        # check that same length arrays
        if len(boss_list) != len(drop_chance_list):
            print("{} has inconsistent length arrays".format(loot_name))
            raise RuntimeError("Array lengths")

        for i in range(len(boss_list)):
            boss = boss_list[i]
            drop_chance = drop_chance_list[i]
            if boss != "CURRENT":
                # add data to boss
                self.bosses[boss].loot_drop_chance[loot_name] = drop_chance
                self.bosses[boss].loot_table.append(loot_name)
        
    def addChar(self,name,spec_class,head,neck,shoulder,chest,waist,legs,feet,wrist,hands,fingers,trinkets,back,mh,oh,th,ranged,zg_enchants):
        if name in self.raid:
            print("{} is already in raid".format(name))
            raise RuntimeError("Duplicate name in raid")

        self.raid[name] = Character(name,spec_class,head,neck,shoulder,chest,waist,legs,feet,wrist,hands,fingers,trinkets,back,mh,oh,th,ranged,zg_enchants)
    
    def _getCharBiS(self,char_name,spec_class,slot):
        # returns the BiS item for given slot that player has
        ep = 0
        item_name_print = "NONE"
        if slot == Slot.ZG_ENCHANTS:
            item_name = "Primal Hakkari Idol"
            item_name_print = item_name
            ep = self.loot_db[item_name].ep_map[spec_class]
        else:
            for item_name in self.raid[char_name].gear[slot]:
                if self.loot_db[item_name].ep_map[spec_class] >= ep:
                    ep = self.loot_db[item_name].ep_map[spec_class]
                    item_name_print = item_name
        return(item_name_print,ep)

    def calc(self):
        # calculate metrics and plot
        for boss_name in self.bosses:
            self.bosses[boss_name].mean_enupm = 0.0
            for char_name in self.raid:
                spec_class = self.raid[char_name].spec_class
                # init total expected upgrade
                self.bosses[boss_name].enu[char_name] = 0
                for loot_name in self.bosses[boss_name].loot_table:
                    # fetch loot
                    loot_new = self.loot_db[loot_name]
                    slot = loot_new.slot
                    drop_chance = self.bosses[boss_name].loot_drop_chance[loot_name]/100.0 # convert to fraction
                    item_new_print = loot_name
                    ep_new = self.loot_db[loot_name].ep_map[spec_class]
                    item_current_print , ep_current = self._getCharBiS(char_name,spec_class,slot)

                    # handle special cases
                    if slot == Slot.ZG_ENCHANTS:
                        # each character expected to get x enchants
                        ZG_ENCHANTS_TRGT = 2
                        item_new_print = "{}x {}".format(ZG_ENCHANTS_TRGT,loot_name)
                        current_cnt = self.raid[char_name].gear[slot]
                        item_current_print = "{}x {}".format(current_cnt,loot_name)
                        ep_new *= ZG_ENCHANTS_TRGT
                        ep_current *= current_cnt
                        
                    elif slot == Slot.MAIN_HAND or slot == Slot.OFF_HAND or slot == Slot.TWO_HAND:
                        # get current items / ep values for weapons
                        item_name_mh_curr , ep_mh_curr = self._getCharBiS(char_name,spec_class,Slot.MAIN_HAND)
                        item_name_oh_curr , ep_oh_curr = self._getCharBiS(char_name,spec_class,Slot.OFF_HAND)
                        item_name_2h_curr , ep_2h_curr = self._getCharBiS(char_name,spec_class,Slot.TWO_HAND)
                        # determine best current
                        if (ep_mh_curr + ep_oh_curr) >= ep_2h_curr:
                            ep_current = ep_mh_curr + ep_oh_curr
                            item_current_print = item_name_mh_curr + " + " + item_name_oh_curr
                        else:
                            ep_current = ep_2h_curr
                            item_current_print = item_name_2h_curr
                        # determine best new
                        if slot == Slot.MAIN_HAND:
                            ep_new += ep_oh_curr
                            item_new_print = item_new_print + " + " + item_name_oh_curr
                        elif slot == Slot.OFF_HAND:
                            ep_new += ep_mh_curr
                            item_new_print = item_name_mh_curr + " + " + item_new_print

                    # calculate ep upgrade
                    if ep_new > ep_current:
                        self.bosses[boss_name].enu[char_name] += ((ep_new - ep_current)*drop_chance)/self.ep_bis[spec_class]
                        if verbose:
                            print("{}: {} ({}) is a {} slot upgrade over {} ({}) for {}".format(boss_name,item_new_print,ep_new,slot.name,item_current_print,ep_current,char_name))
                    
                    if ep_current == 0 and item_current_print != "NONE" and slot != slot.ZG_ENCHANTS:
                        print("boss_name: {}, item_current_print: {}, char_name: {}".format(boss_name,item_current_print,char_name))
                        raise RuntimeError("Current EP should not be 0 for item ")


                self.bosses[boss_name].mean_enupm += self.bosses[boss_name].enu[char_name]

            self.bosses[boss_name].mean_enupm /= len(self.raid)
        
        # define raid color formatting
        raid_color_format = {
            Raid.ONY:"#b3b3b3",
            Raid.MC:"#ff9933",
            Raid.BWL:"#ff3300",
            Raid.ZG:"#009933",
            Raid.AQ20:"#cccc00",
            Raid.AQ40:"#3366ff",
        }
        # plot
        plt.figure()
        y_ticks = []
        y_labels = []
        idx = 1
        for raid in range(Raid.SIZE):
            boss_list = RaidToBossMap[raid]
            color_format = raid_color_format[raid]
            # construct temp ordered dictionary
            d = collections.OrderedDict()
            for boss_name in boss_list:
                 d[boss_name] = self.bosses[boss_name].mean_enupm

            # plot given raid
            plt_range = np.arange(idx,idx+len(d))
            plt.barh(y=plt_range,width=d.values(),color=color_format)
            y_ticks.extend(plt_range)
            y_labels.extend(d.keys())
            idx = plt_range[-1]+1
        
        # format
        # plt.xticks(rotation=90)
        plt.grid(axis='x')
        plt.yticks(ticks=y_ticks,labels=y_labels)
        plt.show()

        return

# instantiate BossPrioCalc
bpc = BossPrioCalc()

# add bosses
# ONY
bpc.addBoss(
    name="Onyxia",
    raid=Raid.ONY,
    clear_time=20,
    )
# MC
MC_clear_time = 75
bpc.addBoss(
    name="Lucifron",
    raid=Raid.MC,
    clear_time=1*MC_clear_time/10,
    )
bpc.addBoss(
    name="Magmadar",
    raid=Raid.MC,
    clear_time=2*MC_clear_time/10,
    )
bpc.addBoss(
    name="Gehennas",
    raid=Raid.MC,
    clear_time=3*MC_clear_time/10,
    )
bpc.addBoss(
    name="Garr",
    raid=Raid.MC,
    clear_time=4*MC_clear_time/10,
    )
bpc.addBoss(
    name="Baron Geddon",
    raid=Raid.MC,
    clear_time=5*MC_clear_time/10,
    )
bpc.addBoss(
    name="Shazzrah",
    raid=Raid.MC,
    clear_time=6*MC_clear_time/10,
    )
bpc.addBoss(
    name="Golemagg the Incinerator",
    raid=Raid.MC,
    clear_time=7*MC_clear_time/10,
    )
bpc.addBoss(
    name="Sulfuron Harbinger",
    raid=Raid.MC,
    clear_time=8*MC_clear_time/10,
    )
bpc.addBoss(
    name="Majordomo Executus",
    raid=Raid.MC,
    clear_time=9*MC_clear_time/10,
    )
bpc.addBoss(
    name="Ragnaros",
    raid=Raid.MC,
    clear_time=10*MC_clear_time/10,
    )
bpc.addBoss(
    name="MC Trash",
    raid=Raid.MC,
    clear_time=MC_clear_time,
    )
# BWL
BWL_clear_time = 60
bpc.addBoss(
    name="Razorgore the Untamed",
    raid=Raid.BWL,
    clear_time=1*BWL_clear_time/8,
    )
bpc.addBoss(
    name="Vaelastrasz the Corrupt",
    raid=Raid.BWL,
    clear_time=2*BWL_clear_time/8,
    )
bpc.addBoss(
    name="Broodlord Lashlayer",
    raid=Raid.BWL,
    clear_time=3*BWL_clear_time/8,
    )
bpc.addBoss(
    name="Firemaw",
    raid=Raid.BWL,
    clear_time=4*BWL_clear_time/8,
    )
bpc.addBoss(
    name="Flamegor",
    raid=Raid.BWL,
    clear_time=5*BWL_clear_time/8,
    )
bpc.addBoss(
    name="Ebonroc",
    raid=Raid.BWL,
    clear_time=6*BWL_clear_time/8,
    )
bpc.addBoss(
    name="Chromaggus",
    raid=Raid.BWL,
    clear_time=7*BWL_clear_time/8,
    )
bpc.addBoss(
    name="Nefarian",
    raid=Raid.BWL,
    clear_time=8*BWL_clear_time/8,
    )
bpc.addBoss(
    name="BWL Trash",
    raid=Raid.BWL,
    clear_time=BWL_clear_time,
    )
# ZG
ZG_clear_time = 90
bpc.addBoss(
    name="Jin'do the Hexxer",
    raid=Raid.ZG,
    clear_time=1*ZG_clear_time/10,
    )
bpc.addBoss(
    name="High Priest Thekal",
    raid=Raid.ZG,
    clear_time=2*ZG_clear_time/10,
    )
bpc.addBoss(
    name="Bloodlord Mandokir",
    raid=Raid.ZG,
    clear_time=3*ZG_clear_time/10,
    )
bpc.addBoss(
    name="High Priestess Mar'li",
    raid=Raid.ZG,
    clear_time=4*ZG_clear_time/10,
    )
bpc.addBoss(
    name="High Priest Venoxis",
    raid=Raid.ZG,
    clear_time=5*ZG_clear_time/10,
    )
bpc.addBoss(
    name="High Priestess Jeklik",
    raid=Raid.ZG,
    clear_time=6*ZG_clear_time/10,
    )
bpc.addBoss(
    name="Edge of Madness",
    raid=Raid.ZG,
    clear_time=7*ZG_clear_time/10,
    )
bpc.addBoss(
    name="High Priestess Arlokk",
    raid=Raid.ZG,
    clear_time=8*ZG_clear_time/10,
    )
bpc.addBoss(
    name="Hakkar",
    raid=Raid.ZG,
    clear_time=9*ZG_clear_time/10,
    )
bpc.addBoss(
    name="Gahz'ranka",
    raid=Raid.ZG,
    clear_time=10*ZG_clear_time/10,
    )
# AQ20
AQ20_clear_time = 90
bpc.addBoss(
    name="Kurinnaxx",
    raid=Raid.AQ20,
    clear_time=1*AQ20_clear_time/6,
    )
bpc.addBoss(
    name="General Rajaxx",
    raid=Raid.AQ20,
    clear_time=2*AQ20_clear_time/6,
    )
bpc.addBoss(
    name="Moam",
    raid=Raid.AQ20,
    clear_time=3*AQ20_clear_time/6,
    )
bpc.addBoss(
    name="Buru the Gorger",
    raid=Raid.AQ20,
    clear_time=4*AQ20_clear_time/6,
    )
bpc.addBoss(
    name="Ayamiss the Hunter",
    raid=Raid.AQ20,
    clear_time=5*AQ20_clear_time/6,
    )
bpc.addBoss(
    name="Ossirian the Unscarred",
    raid=Raid.AQ20,
    clear_time=6*AQ20_clear_time/6,
    )
bpc.addBoss(
    name="AQ20 Trash",
    raid=Raid.AQ20,
    clear_time=AQ20_clear_time,
    )

# AQ40
AQ40_clear_time = 240
bpc.addBoss(
    name="The Prophet Skeram",
    raid=Raid.AQ40,
    clear_time=1*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Lord Kri",
    raid=Raid.AQ40,
    clear_time=2*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Princess Yauj",
    raid=Raid.AQ40,
    clear_time=2*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Vem",
    raid=Raid.AQ40,
    clear_time=2*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Battleguard Sartura",
    raid=Raid.AQ40,
    clear_time=3*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Fankriss the Unyielding",
    raid=Raid.AQ40,
    clear_time=4*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Viscidus",
    raid=Raid.AQ40,
    clear_time=5*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Princess Huhuran",
    raid=Raid.AQ40,
    clear_time=6*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Twin Emperors",
    raid=Raid.AQ40,
    clear_time=7*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="Ouro",
    raid=Raid.AQ40,
    clear_time=8*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="C'Thun",
    raid=Raid.AQ40,
    clear_time=9*AQ40_clear_time/9,
    )
bpc.addBoss(
    name="AQ40 Trash",
    raid=Raid.AQ40,
    clear_time=AQ40_clear_time,
    )

# add character to raid data
# Druid
bpc.addChar(
    name="Milku",
    spec_class=SpecClass.RESTO_DRUID,
    head=["Stormrage Cover"],
    neck=["Choker of the Fire Lord"],
    shoulder=["Stormrage Pauldrons"],
    chest=["Stormrage Chestguard"],
    waist=["Stormrage Belt"],
    legs=["Stormrage Legguards"],
    feet=["Stormrage Boots"],
    wrist=["Stormrage Bracers"],
    hands=["Stormrage Handguards"],
    fingers=["Seal of the Archmagus","Band of Sulfuras"],
    trinkets=["Zandalarian Hero Charm","Royal Seal of Eldre'Thalas"],
    back=["Hide of the Wild"],
    mh=["Lok'amir il Romathis"],
    oh=["Fire Runed Grimoire"],
    th=[],
    ranged=["Idol of the Moon"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Eighchbar",
    spec_class=SpecClass.RESTO_DRUID,
    head=["Stormrage Cover"],
    neck=["Jin'do's Evil Eye"],
    shoulder=["Wild Growth Spaulders"],
    chest=["Robes of the Exalted"],
    waist=["Stormrage Belt"],
    legs=["Empowered Leggings"],
    feet=["Cenarion Boots"],
    wrist=["Stormrage Bracers"],
    hands=["Stormrage Handguards"],
    fingers=["Pure Elementium Band","Fordring's Seal"],
    trinkets=["Zandalarian Hero Charm","Rejuvenating Gem"],
    back=["Hakkari Loa Cloak"],
    mh=["Jin'do's Hexxer"],
    oh=["Lei of the Lifegiver"],
    th=[],
    ranged=[],
    zg_enchants=1,
    )
bpc.addChar(
    name="Slecht",
    spec_class=SpecClass.RESTO_DRUID,
    head=["Stormrage Cover"],
    neck=["Amulet of the Shifting Sands"],
    shoulder=["Wild Growth Spaulders"],
    chest=["Stormrage Chestguard"],
    waist=["Corehound Belt"],
    legs=["Stormrage Legguards"],
    feet=["Verdant Footpads"],
    wrist=["Stormrage Bracers"],
    hands=["Stormrage Handguards"],
    fingers=["Primalist's Seal","Primalist's Band"],
    trinkets=["Royal Seal of Eldre'Thalas","Rejuvenating Gem"],
    back=["Hide of the Wild"],
    mh=["Lok'amir il Romathis"],
    oh=["Lei of the Lifegiver"],
    th=[],
    ranged=[],
    zg_enchants=2,
    )
# Hunter
bpc.addChar(
    name="Jiero",
    spec_class=SpecClass.MARKS_HUNTER,
    head=["Dragonstalker's Helm"],
    neck=["Prestor's Talisman of Connivery"],
    shoulder=["Dragonstalker's Spaulders"],
    chest=["Dragonstalker's Breastplate"],
    waist=["Dragonstalker's Belt"],
    legs=["Dragonstalker's Legguards"],
    feet=["Dragonstalker's Greaves"],
    wrist=["Dragonstalker's Bracers"],
    hands=["Dragonstalker's Gauntlets"],
    fingers=["Quick Strike Ring","Master Dragonslayer's Ring"],
    trinkets=["Devilsaur Eye","Blackhand's Breadth"],
    back=["Cloak of the Shrouded Mists"],
    mh=["Warblade of the Hakkari"],
    oh=["Fang of the Faceless"],
    th=[],
    ranged=["Ashjre'thul, Crossbow of Smiting"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Ishney",
    spec_class=SpecClass.MARKS_HUNTER,
    head=["Dragonstalker's Helm"],
    neck=["Prestor's Talisman of Connivery"],
    shoulder=["Dragonstalker's Spaulders"],
    chest=["Dragonstalker's Breastplate"],
    waist=["Dragonstalker's Belt"],
    legs=["Dragonstalker's Legguards"],
    feet=["Dragonstalker's Greaves"],
    wrist=["Dragonstalker's Bracers"],
    hands=["Dragonstalker's Gauntlets"],
    fingers=["Don Julio's Band","Master Dragonslayer's Ring"],
    trinkets=["Royal Seal of Eldre'Thalas","Blackhand's Breadth"],
    back=["Zulian Tigerhide Cloak"],
    mh=[],
    oh=[],
    th=["Lok'delar, Stave of the Ancient Keepers"],
    ranged=["Ashjre'thul, Crossbow of Smiting"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Irisviiel",
    spec_class=SpecClass.MARKS_HUNTER,
    head=["Dragonstalker's Helm"],
    neck=["Prestor's Talisman of Connivery"],
    shoulder=["Dragonstalker's Spaulders"],
    chest=["Dragonstalker's Breastplate"],
    waist=["Dragonstalker's Belt"],
    legs=["Dragonstalker's Legguards"],
    feet=["Dragonstalker's Greaves"],
    wrist=["Dragonstalker's Bracers"],
    hands=["Dragonstalker's Gauntlets"],
    fingers=["Don Julio's Band","Band of Accuria"],
    trinkets=["Royal Seal of Eldre'Thalas","Blackhand's Breadth"],
    back=["Cape of the Black Baron"],
    mh=[],
    oh=[],
    th=["Ashkandi, Greatsword of the Brotherhood"],
    ranged=["Mandokir's Sting"],
    zg_enchants=2,
    )
# Mage
bpc.addChar(
    name="Jax",
    spec_class=SpecClass.FIRE_MAGE,
    head=["Arcanist Crown"],
    neck=["Choker of Enlightenment"],
    shoulder=["Mantle of the Blackwing Cabal"],
    chest=["Bloodvine Vest"],
    waist=["Arcanist Belt"],
    legs=["Bloodvine Leggings"],
    feet=["Bloodvine Boots"],
    wrist=["Netherwind Bindings"],
    hands=["Arcanist Gloves"],
    fingers=["Ring of Spell Power","Band of Rumination"],
    trinkets=["Talisman of Ephemeral Power","Mind Quickening Gem"],
    back=["Cloak of the Brood Lord"],
    mh=[],
    oh=[],
    th=["Staff of Dominance"],
    ranged=["Stormrager"],
    zg_enchants=0,
    )
bpc.addChar(
    name="Duhd",
    spec_class=SpecClass.FIRE_MAGE,
    head=["Netherwind Crown"],
    neck=["Choker of the Fire Lord"],
    shoulder=["Mantle of the Blackwing Cabal"],
    chest=["Bloodvine Vest"],
    waist=["Mana Igniting Cord"],
    legs=["Bloodvine Leggings"],
    feet=["Bloodvine Boots"],
    wrist=["Bracers of Arcane Accuracy"],
    hands=["Bloodtinged Gloves"],
    fingers=["Ring of Spell Power","Ring of Spell Power"],
    trinkets=["Talisman of Ephemeral Power","Mind Quickening Gem"],
    back=["Cloak of Consumption"],
    mh=["Claw of Chromaggus"],
    oh=["Jin'do's Bag of Whammies"],
    th=[],
    ranged=["Bonecreeper Stylus"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Parisshelton",
    spec_class=SpecClass.FIRE_MAGE,
    head=["Netherwind Crown"],
    neck=["Jeklik's Opaline Talisman"],
    shoulder=["Mantle of the Blackwing Cabal"],
    chest=["Bloodvine Vest"],
    waist=["Mana Igniting Cord"],
    legs=["Bloodvine Leggings"],
    feet=["Bloodvine Boots"],
    wrist=["Netherwind Bindings"],
    hands=["Netherwind Gloves"],
    fingers=["Band of Servitude","Zanzil's Seal"],
    trinkets=["Talisman of Ephemeral Power","Neltharion's Tear"],
    back=["Cloak of Consumption"],
    mh=["Bloodcaller"],
    oh=["Jin'do's Bag of Whammies"],
    th=[],
    ranged=["Touch of Chaos"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Dryrun",
    spec_class=SpecClass.FIRE_MAGE,
    head=["Champion's Silk Cowl"],
    neck=["Choker of the Fire Lord"],
    shoulder=["Champion's Silk Mantle"],
    chest=["Bloodvine Vest"],
    waist=["Belt of Untapped Power"],
    legs=["Bloodvine Leggings"],
    feet=["Bloodvine Boots"],
    wrist=["Bracers of Arcane Accuracy"],
    hands=["Arcanist Gloves"],
    fingers=["Band of Servitude","Dragonslayer's Signet"],
    trinkets=["Eye of the Beast","Zandalarian Hero Charm"],
    back=["Sapphiron Drape"],
    mh=["Bloodcaller"],
    oh=["Tome of Fiery Arcana"],
    th=[],
    ranged=["Touch of Chaos"],
    zg_enchants=2,
    )
# Priest
bpc.addChar(
    name="Enders",
    spec_class=SpecClass.HOLY_PRIEST,
    head=["Halo of Transcendence"],
    neck=["Amulet of the Shifting Sands"],
    shoulder=["Pauldrons of Transcendence"],
    chest=["Robes of Transcendence"],
    waist=["Belt of Transcendence"],
    legs=["Leggings of Transcendence"],
    feet=["Boots of Transcendence"],
    wrist=["Bindings of Transcendence"],
    hands=["Handguards of Transcendence"],
    fingers=["Fordring's Seal","Cauterizing Band"],
    trinkets=["Royal Seal of Eldre'Thalas","Rejuvenating Gem"],
    back=["Hide of the Wild"],
    mh=[],
    oh=[],
    th=["Benediction"],
    ranged=["Essence Gatherer"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Necrohealya",
    spec_class=SpecClass.HOLY_PRIEST,
    head=["Halo of Transcendence"],
    neck=["Jin'do's Evil Eye"],
    shoulder=["Pauldrons of Transcendence"],
    chest=["Robes of Transcendence"],
    waist=["Belt of Transcendence"],
    legs=["Leggings of Transcendence"],
    feet=["Boots of Transcendence"],
    wrist=["Bindings of Transcendence"],
    hands=["Handguards of Transcendence"],
    fingers=["Pure Elementium Band","Ring of Blackrock"],
    trinkets=["Zandalarian Hero Charm","Darkmoon Card: Blue Dragon"],
    back=["Hide of the Wild"],
    mh=["Gavel of Infinite Wisdom"],
    oh=["Lei of the Lifegiver"],
    th=[],
    ranged=["Essence Gatherer"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Pythagorean",
    spec_class=SpecClass.HOLY_PRIEST,
    head=["Halo of Transcendence"],
    neck=["Animated Chain Necklace"],
    shoulder=["Pauldrons of Transcendence"],
    chest=["Robes of Transcendence"],
    waist=["Belt of Transcendence"],
    legs=["Leggings of Transcendence"],
    feet=["Boots of Transcendence"],
    wrist=["Bindings of Transcendence"],
    hands=["Handguards of Transcendence"],
    fingers=["Pure Elementium Band","Cauterizing Band"],
    trinkets=["Zandalarian Hero Charm","Shard of the Scale"],
    back=["Hide of the Wild"],
    mh=[],
    oh=["Lei of the Lifegiver"],
    th=["Benediction"],
    ranged=["Glowstar Rod of Healing"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Wangcake",
    spec_class=SpecClass.HOLY_PRIEST,
    head=["Halo of Transcendence"],
    neck=["Jin'do's Evil Eye"],
    shoulder=["Pauldrons of Transcendence"],
    chest=["Robes of Transcendence"],
    waist=["Belt of Transcendence"],
    legs=["Leggings of Transcendence"],
    feet=["Boots of Transcendence"],
    wrist=["Bindings of Transcendence"],
    hands=["Handguards of Transcendence"],
    fingers=["Ring of Blackrock","Cauterizing Band"],
    trinkets=["Zandalarian Hero Charm","Rejuvenating Gem"],
    back=["Hide of the Wild"],
    mh=[],
    oh=["Lei of the Lifegiver"],
    th=["Benediction"],
    ranged=["Essence Gatherer"],
    zg_enchants=2,
    )
# Rogue
bpc.addChar(
    name="Deadstrike",
    spec_class=SpecClass.COMBAT_ROGUE,
    head=["Bloodfang Hood"],
    neck=["Onyxia Tooth Pendant"],
    shoulder=["Bloodfang Spaulders"],
    chest=["Nightslayer Chestpiece"],
    waist=["Nightslayer Belt"],
    legs=["Bloodfang Pants"],
    feet=["Bloodfang Boots"],
    wrist=["Nightslayer Bracelets"],
    hands=["Bloodfang Gloves"],
    fingers=["Don Julio's Band","Master Dragonslayer's Ring"],
    trinkets=["Hand of Justice","Royal Seal of Eldre'Thalas"],
    back=["Cape of the Black Baron"],
    mh=["Vis'kag the Bloodletter"],
    oh=["Brutality Blade"],
    th=[],
    ranged=["Heartstriker"],
    zg_enchants=0,
    )
bpc.addChar(
    name="Kirilov",
    spec_class=SpecClass.COMBAT_ROGUE,
    head=["Bloodfang Hood"],
    neck=["Prestor's Talisman of Connivery"],
    shoulder=["Bloodfang Spaulders"],
    chest=["Bloodfang Chestpiece"],
    waist=["Bloodfang Belt"],
    legs=["Bloodfang Pants"],
    feet=["Bloodfang Boots"],
    wrist=["Bloodfang Bracers"],
    hands=["Bloodfang Gloves"],
    fingers=["Seal of the Gurubashi Berserker","Master Dragonslayer's Ring"],
    trinkets=["Hand of Justice","Blackhand's Breadth"],
    back=["Cloak of Firemaw"],
    mh=["Chromatically Tempered Sword"],
    oh=["Maladath, Runed Blade of the Black Flight"],
    th=[],
    ranged=["Striker's Mark"],
    zg_enchants=0,
    )
bpc.addChar(
    name="Stankdik",
    spec_class=SpecClass.COMBAT_ROGUE,
    head=["Bloodfang Hood"],
    neck=["Onyxia Tooth Pendant"],
    shoulder=["Bloodfang Spaulders"],
    chest=["Zandalar Madcap's Tunic"],
    waist=["Bloodfang Belt"],
    legs=["Bloodfang Pants"],
    feet=["Boots of the Shadow Flame"],
    wrist=["Bloodfang Bracers"],
    hands=["Aged Core Leather Gloves"],
    fingers=["Quick Strike Ring","Master Dragonslayer's Ring"],
    trinkets=["Hand of Justice","Blackhand's Breadth"],
    back=["Cloak of Firemaw"],
    mh=["Gutgore Ripper"],
    oh=["Fang of the Faceless"],
    th=[],
    ranged=["Gurubashi Dwarf Destroyer"],
    zg_enchants=2,
    )
# Shaman
bpc.addChar(
    name="Deyn",
    spec_class=SpecClass.RESTO_SHAMAN,
    head=["Helmet of Ten Storms"],
    neck=["Jin'do's Evil Eye"],
    shoulder=["Wild Growth Spaulders"],
    chest=["Robes of the Exalted"],
    waist=["Belt of Ten Storms"],
    legs=["Empowered Leggings"],
    feet=["Greaves of Ten Storms"],
    wrist=["Bracers of Ten Storms"],
    hands=["Gauntlets of Ten Storms"],
    fingers=["Pure Elementium Band","Fordring's Seal"],
    trinkets=["Briarwood Reed","Zandalarian Hero Charm"],
    back=["Hide of the Wild"],
    mh=["Jin'do's Hexxer"],
    oh=["Lei of the Lifegiver"],
    th=[],
    ranged=[],
    zg_enchants=2,
    )
bpc.addChar(
    name="Ghazan",
    spec_class=SpecClass.RESTO_SHAMAN,
    head=["Helmet of Ten Storms"],
    neck=["Choker of the Fire Lord"],
    shoulder=["Wild Growth Spaulders"],
    chest=["Breastplate of Ten Storms"],
    waist=["Belt of Ten Storms"],
    legs=["Salamander Scale Pants"],
    feet=["Greaves of Ten Storms"],
    wrist=["Bracers of Ten Storms"],
    hands=["Gauntlets of Ten Storms"],
    fingers=["Cauterizing Band","Primalist's Band"],
    trinkets=["Mindtap Talisman","Zandalarian Hero Charm"],
    back=["Shroud of Pure Thought"],
    mh=["Aurastone Hammer"],
    oh=["Malistar's Defender"],
    th=[],
    ranged=[],
    zg_enchants=0,
    )
# Warlock
bpc.addChar(
    name="Dietolive",
    spec_class=SpecClass.ANY_WARLOCK,
    head=["Mish'undare, Circlet of the Mind Flayer"],
    neck=["Choker of the Fire Lord"],
    shoulder=["Nemesis Spaulders"],
    chest=["Bloodvine Vest"],
    waist=["Sash of Whispered Secrets"],
    legs=["Bloodvine Leggings"],
    feet=["Bloodvine Boots"],
    wrist=["Nemesis Bracers"],
    hands=["Felcloth Gloves"],
    fingers=["Band of Forced Concentration","Band of Dark Dominion"],
    trinkets=["Neltharion's Tear","Zandalarian Hero Charm"],
    back=["Cloak of Consumption"],
    mh=["Azuresong Mageblade"],
    oh=["Tome of Shadow Force"],
    th=[],
    ranged=["Wizard's Hand of Wrath"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Ultimecia",
    spec_class=SpecClass.ANY_WARLOCK,
    head=["Mish'undare, Circlet of the Mind Flayer"],
    neck=["Choker of the Fire Lord"],
    shoulder=["Nemesis Spaulders"],
    chest=["Bloodvine Vest"],
    waist=["Nemesis Belt"],
    legs=["Bloodvine Leggings"],
    feet=["Bloodvine Boots"],
    wrist=["Nemesis Bracers"],
    hands=["Ebony Flame Gloves"],
    fingers=["Ring of Spell Power","Dragonslayer's Signet"],
    trinkets=["Neltharion's Tear","Zandalarian Hero Charm"],
    back=["Cloak of the Brood Lord"],
    mh=[],
    oh=[],
    th=["Staff of Dominance"],
    ranged=["Touch of Chaos"],
    zg_enchants=2,
    )
bpc.addChar(
    name="Gaunz",
    spec_class=SpecClass.ANY_WARLOCK,
    head=["Nemesis Skullcap"],
    neck=["Choker of Enlightenment"],
    shoulder=["Nemesis Spaulders"],
    chest=["Bloodvine Vest"],
    waist=["Nemesis Belt"],
    legs=["Bloodvine Leggings"],
    feet=["Bloodvine Boots"],
    wrist=["Bracers of Arcane Accuracy"],
    hands=["Ebony Flame Gloves"],
    fingers=["Band of Forced Concentration","Band of Dark Dominion"],
    trinkets=["Neltharion's Tear","Zandalarian Hero Charm"],
    back=["Cloak of Consumption"],
    mh=["Azuresong Mageblade"],
    oh=["Jin'do's Bag of Whammies"],
    th=[],
    ranged=["Skul's Ghastly Touch"],
    zg_enchants=2,
    )
# DPS Warrior
# bpc.addChar(
#     name="Akecheta",
#     spec_class=SpecClass.FURY_WARRIOR,
#     head=["Lionheart Helm"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Drake Talon Pauldrons"],
#     chest=["Malfurion's Blessed Bulwark"],
#     waist=["Onslaught Girdle"],
#     legs=["Abyssal Plate Legplates of Striking"],
#     feet=["Chromatic Boots"],
#     wrist=["Wristguards of Stability"],
#     hands=["Edgemaster's Handguards"],
#     fingers=["Quick Strike Ring","Seal of the Gurubashi Berserker"],
#     trinkets=["Hand of Justice","Drake Fang Talisman"],
#     back=["Might of the Tribe"],
#     mh=["Crul'shorukh, Edge of Chaos"],
#     oh=["Brutality Blade"],
#     th=[],
#     ranged=["Striker's Mark"],
#     zg_enchants=0,
#     )
# bpc.addChar(
#     name="Flatzz",
#     spec_class=SpecClass.FURY_WARRIOR,
#     head=["Lionheart Helm"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Drake Talon Pauldrons"],
#     chest=["Savage Gladiator Chain"],
#     waist=["Zandalar Vindicator's Belt"],
#     legs=["Eldritch Reinforced Legplates"],
#     feet=["Chromatic Boots"],
#     wrist=["Zandalar Vindicator's Armguards"],
#     hands=["Edgemaster's Handguards"],
#     fingers=["Quick Strike Ring","Don Julio's Band"],
#     trinkets=["Hand of Justice","Blackhand's Breadth"],
#     back=["Cloak of Draconic Might"],
#     mh=["Deathbringer"],
#     oh=["Core Hound Tooth"],
#     th=[],
#     ranged=["Striker's Mark"],
#     zg_enchants=0,
#     )
# bpc.addChar(
#     name="Chango",
#     spec_class=SpecClass.FURY_WARRIOR,
#     head=["Lionheart Helm"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Drake Talon Pauldrons"],
#     chest=["Savage Gladiator Chain"],
#     waist=["Onslaught Girdle"],
#     legs=["Legionnaire's Plate Leggings"],
#     feet=["Chromatic Boots"],
#     wrist=["Zandalar Vindicator's Armguards"],
#     hands=["Flameguard Gauntlets"],
#     fingers=["Quick Strike Ring","Don Julio's Band"],
#     trinkets=["Hand of Justice","Drake Fang Talisman"],
#     back=["Cape of the Black Baron"],
#     mh=["Crul'shorukh, Edge of Chaos"],
#     oh=["Doom's Edge"],
#     th=[],
#     ranged=["Blastershot Launcher"],
#     zg_enchants=0,
#     )
# bpc.addChar(
#     name="Dohvyk",
#     spec_class=SpecClass.FURY_WARRIOR,
#     head=["Lionheart Helm"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Drake Talon Pauldrons"],
#     chest=["Savage Gladiator Chain"],
#     waist=["Zandalar Vindicator's Belt"],
#     legs=["Bloodsoaked Legplates"],
#     feet=["Boots of the Shadow Flame"],
#     wrist=["Battleborn Armbraces"],
#     hands=["Flameguard Gauntlets"],
#     fingers=["Quick Strike Ring","Master Dragonslayer's Ring"],
#     trinkets=["Hand of Justice","Blackhand's Breadth"],
#     back=["Zulian Tigerhide Cloak"],
#     mh=[],
#     oh=[],
#     th=["Bonereaver's Edge"],
#     ranged=["Satyr's Bow"],
#     zg_enchants=0,
#     )
# bpc.addChar(
#     name="Furckinstein",
#     spec_class=SpecClass.FURY_WARRIOR,
#     head=["Crown of Destruction"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Champion's Plate Shoulders"],
#     chest=["Runed Bloodstained Hauberk"],
#     waist=["Mugger's Belt"],
#     legs=["Legionnaire's Plate Leggings"],
#     feet=["Bloodmail Boots"],
#     wrist=["Zandalar Vindicator's Armguards"],
#     hands=["Sacrificial Gauntlets"],
#     fingers=["Quick Strike Ring","Don Julio's Band"],
#     trinkets=["Drake Fang Talisman","Blackhand's Breadth"],
#     back=["Cloak of Firemaw"],
#     mh=["Gutgore Ripper"],
#     oh=["Bonescraper"],
#     th=[],
#     ranged=["Gurubashi Dwarf Destroyer"],
#     zg_enchants=0,
#     )
# bpc.addChar(
#     name="Dirty",
#     spec_class=SpecClass.FURY_WARRIOR,
#     head=["Lionheart Helm"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Black Dragonscale Shoulders"],
#     chest=["Black Dragonscale Breastplate"],
#     waist=["Zandalar Vindicator's Belt"],
#     legs=["Black Dragonscale Leggings"],
#     feet=["Black Dragonscale Boots"],
#     wrist=["Zandalar Vindicator's Armguards"],
#     hands=["Flameguard Gauntlets"],
#     fingers=["Quick Strike Ring","Don Julio's Band"],
#     trinkets=["Blackhand's Breadth","Diamond Flask"],
#     back=["Zulian Tigerhide Cloak"],
#     mh=["Warblade of the Hakkari"],
#     oh=["Warblade of the Hakkari"],
#     th=[],
#     ranged=["Blastershot Launcher"],
#     zg_enchants=0,
#     )
# # Tank
# bpc.addChar(
#     name="Crox",
#     spec_class=SpecClass.PROT_THREAT_WARRIOR,
#     head=["Helm of Endless Rage"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Drake Talon Pauldrons"],
#     chest=["Savage Gladiator Chain"],
#     waist=["Zandalar Vindicator's Belt"],
#     legs=["Legplates of Wrath"],
#     feet=["Core Forged Greaves"],
#     wrist=["Wristguards of True Flight"],
#     hands=["Edgemaster's Handguards"],
#     fingers=["Master Dragonslayer's Ring","Band of Accuria"],
#     trinkets=["Drake Fang Talisman","Ramstein's Lightning Bolts"],
#     back=["Elementium Threaded Cloak"],
#     mh=["Thunderfury, Blessed Blade of the Windseeker"],
#     oh=["Elementium Reinforced Bulwark"],
#     th=[],
#     ranged=["Striker's Mark"],
#     zg_enchants=0,
#     )
# bpc.addChar(
#     name="Bandakar",
#     spec_class=SpecClass.PROT_THREAT_WARRIOR,
#     head=["Helm of Wrath"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Warlord's Plate Shoulders"],
#     chest=["Warlord's Plate Armo"],
#     waist=["Waistband of Wrath"],
#     legs=["General's Plate Leggings"],
#     feet=["General's Plate Boots"],
#     wrist=["Wristguards of True Flight"],
#     hands=["General's Plate Gauntlets"],
#     fingers=["Quick Strike Ring","Band of Accuria"],
#     trinkets=["Blackhand's Breadth","Hand of Justice"],
#     back=["Dragon's Blood Cape"],
#     mh=["Crul'shorukh, Edge of Chaos"],
#     oh=["Elementium Reinforced Bulwark"],
#     th=[],
#     ranged=["Striker's Mark"],
#     zg_enchants=2,
#     )
# bpc.addChar(
#     name="Guliveris",
#     spec_class=SpecClass.PROT_THREAT_WARRIOR,
#     head=["Helm of Wrath"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Warlord's Plate Shoulders"],
#     chest=["Warlord's Plate Armo"],
#     waist=["Waistband of Wrath"],
#     legs=["Legplates of Wrath"],
#     feet=["Dark Iron Boots"],
#     wrist=["Wristguards of True Flight"],
#     hands=["Gauntlets of Might"],
#     fingers=["Master Dragonslayer's Ring","Don Julio's Band"],
#     trinkets=["Blackhand's Breadth","Lifegiving Gem"],
#     back=["Shifting Cloak"],
#     mh=["Perdition's Blade"],
#     oh=["Doom's Edge"],
#     th=[],
#     ranged=["Satyr's Bow"],
#     zg_enchants=2,
#     )
# bpc.addChar(
#     name="Pemberstone",
#     spec_class=SpecClass.PROT_THREAT_WARRIOR,
#     head=["Foror's Eyepatch"],
#     neck=["Onyxia Tooth Pendant"],
#     shoulder=["Abyssal Leather Shoulders"],
#     chest=["Malfurion's Blessed Bulwark"],
#     waist=["Belt of Preserved Heads"],
#     legs=["Abyssal Leather Leggings"],
#     feet=["Boots of the Shadow Flame"],
#     wrist=["Wristguards of Stability"],
#     hands=["Aged Core Leather Gloves"],
#     fingers=["Circle of Applied Force","Band of Accuria"],
#     trinkets=["Mark of Tyranny","Rune of the Guard Captain"],
#     back=["Dragon's Blood Cape"],
#     mh=[],
#     oh=[],
#     th=["Draconic Maul"],
#     ranged=["Idol of Brutality"],
#     zg_enchants=0,
#     )

# add loot items to boss loot tables
# Onyxia
boss_name = "Onyxia"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Onyxia Tooth Pendant",
    slot=Slot.NECK,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:64,
        SpecClass.FURY_WARRIOR:52,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonslayer's Signet",
    slot=Slot.FINGER,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.ANY_WARLOCK:16,
        SpecClass.FIRE_MAGE:14,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Stormrage Cover",
    slot=Slot.HEAD,
    drop_chance_list=[18.55],
    ep_map={
        SpecClass.RESTO_DRUID:62,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nemesis Skullcap",
    slot=Slot.HEAD,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.ANY_WARLOCK:36,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Helmet of Ten Storms",
    slot=Slot.HEAD,
    drop_chance_list=[15.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:56,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Halo of Transcendence",
    slot=Slot.HEAD,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.HOLY_PRIEST:105,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Shard of the Scale",
    slot=Slot.TRINKET,
    drop_chance_list=[5.71],
    ep_map={
        SpecClass.RESTO_DRUID:48,
        SpecClass.HOLY_PRIEST:56,
        SpecClass.RESTO_SHAMAN:96,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Deathbringer",
    slot=Slot.OFF_HAND,
    drop_chance_list=[5.86],
    ep_map={
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Vis'kag the Bloodletter",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[5.70],
    ep_map={
        SpecClass.COMBAT_ROGUE:903,

    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonstalker's Helm",
    slot=Slot.HEAD,
    drop_chance_list=[29.0],
    ep_map={
        SpecClass.MARKS_HUNTER:104,
    },
    )  
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Netherwind Crown",
    slot=Slot.HEAD,
    drop_chance_list=[19.55],
    ep_map={
        SpecClass.FIRE_MAGE:37,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Sapphiron Drape",
    slot=Slot.BACK,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.FIRE_MAGE:17,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodfang Hood",
    slot=Slot.HEAD,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:95,
    },
    )

# Lucifron
boss_name = "Lucifron"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cenarion Boots",
    slot=Slot.FEET,
    drop_chance_list=[22.0],
    ep_map={
        SpecClass.RESTO_DRUID:38,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Choker of Enlightenment",
    slot=Slot.NECK,
    drop_chance_list=[23.0],
    ep_map={
        SpecClass.FIRE_MAGE:20,
        SpecClass.ANY_WARLOCK:21,
    },
    )

# Magmadar
boss_name = "Magmadar"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nightslayer Pants",
    slot=Slot.LEGS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:97,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Striker's Mark",
    slot=Slot.RANGED,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:40,
    },
    )

# Gehennas
boss_name = "Gehennas"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nightslayer Gloves",
    slot=Slot.HANDS,
    drop_chance_list=[32.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:65,
    },
    )

# Garr
boss_name = "Garr"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Aurastone Hammer",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.RESTO_DRUID:43,
        SpecClass.RESTO_SHAMAN:67,
        SpecClass.HOLY_PRIEST:54,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Earthfury Helmet",
    slot=Slot.HEAD,
    drop_chance_list=[9.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:86,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Arcanist Crown",
    slot=Slot.HEAD,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.FIRE_MAGE:38,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Brutality Blade",
    slot=Slot.OFF_HAND,
    drop_chance_list=[19.00],
    ep_map={
        SpecClass.COMBAT_ROGUE:897,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Gutgore Ripper",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[19.00],
    ep_map={
        SpecClass.COMBAT_ROGUE:798,
        SpecClass.FURY_WARRIOR:798,
    },
    )

# Golemagg the Incinerator
boss_name = "Golemagg the Incinerator"
bpc.addLoot(
    boss_list=["Golemagg the Incinerator","Garr","Magmadar"],
    loot_name="Fire Runed Grimoire",
    slot=Slot.OFF_HAND,
    drop_chance_list=[4.0,9.0,13.0],
    ep_map={
        SpecClass.RESTO_DRUID:17,
    },
    )
bpc.addLoot(
    boss_list=["Golemagg the Incinerator","Garr","Magmadar"],
    loot_name="Quick Strike Ring",
    slot=Slot.FINGER,
    drop_chance_list=[4.0,9.0,12.0],
    ep_map={
        SpecClass.MARKS_HUNTER:59,
        SpecClass.COMBAT_ROGUE:59,
    },
    )
bpc.addLoot(
    boss_list=["Golemagg the Incinerator","Garr","Magmadar"],
    loot_name="Talisman of Ephemeral Power",
    slot=Slot.TRINKET,
    drop_chance_list=[4.0,9.0,11.0],
    ep_map={
        SpecClass.FIRE_MAGE:29,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Staff of Dominance",
    slot=Slot.TWO_HAND,
    drop_chance_list=[20.00],
    ep_map={
        SpecClass.FIRE_MAGE:59,
        SpecClass.ANY_WARLOCK:63,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Azuresong Mageblade",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[20.00],
    ep_map={
        SpecClass.FIRE_MAGE:54,
        SpecClass.ANY_WARLOCK:56,
    },
    )
bpc.addLoot(
    boss_list=["Golemagg the Incinerator","Garr","Magmadar"],
    loot_name="Mana Igniting Cord",
    slot=Slot.WAIST,
    drop_chance_list=[4.0,9.0,11.0],
    ep_map={
        SpecClass.FIRE_MAGE:40,
        SpecClass.ANY_WARLOCK:42,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nightslayer Chestpiece",
    slot=Slot.CHEST,
    drop_chance_list=[20.00],
    ep_map={
        SpecClass.COMBAT_ROGUE:89,
    },
    )
bpc.addLoot(
    boss_list=["Golemagg the Incinerator","Garr","Magmadar"],
    loot_name="Aged Core Leather Gloves",
    slot=Slot.HANDS,
    drop_chance_list=[7.0,7.0,7.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:40,
    },
    )

# Baron Geddon
boss_name = "Baron Geddon"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Seal of the Archmagus",
    slot=Slot.FINGER,
    drop_chance_list=[32.21],
    ep_map={
        SpecClass.RESTO_DRUID:17,
    },
    )

# Shazzrah
boss_name = "Shazzrah"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Arcanist Gloves",
    slot=Slot.HANDS,
    drop_chance_list=[32.0],
    ep_map={
        SpecClass.FIRE_MAGE:17,
    },
    )

# Sulfuron Harbinger
boss_name = "Sulfuron Harbinger"
bpc.addLoot(
    boss_list=["Sulfuron Harbinger","Baron Geddon","Gehennas","Lucifron"],
    loot_name="Ring of Spell Power",
    slot=Slot.FINGER,
    drop_chance_list=[5.0,4.0,7.0,4.0],
    ep_map={
        SpecClass.FIRE_MAGE:33,
        SpecClass.ANY_WARLOCK:33,
    },
    )
bpc.addLoot(
    boss_list=["Sulfuron Harbinger","Shazzrah","Gehennas","Lucifron"],
    loot_name="Salamander Scale Pants",
    slot=Slot.LEGS,
    drop_chance_list=[5.0,5.0,5.0,5.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:122,
        SpecClass.RESTO_DRUID:82,
    },
    )

# Majordomo Executus
boss_name = "Majordomo Executus"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Wild Growth Spaulders",
    slot=Slot.SHOULDER,
    drop_chance_list=[5.0],
    ep_map={
        SpecClass.RESTO_DRUID:70,
        SpecClass.RESTO_SHAMAN:76,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Sash of Whispered Secrets",
    slot=Slot.WAIST,
    drop_chance_list=[5.0],
    ep_map={
        SpecClass.ANY_WARLOCK:33,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cauterizing Band",
    slot=Slot.FINGER,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_DRUID:50,
        SpecClass.HOLY_PRIEST:60,
        SpecClass.RESTO_SHAMAN:60,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Lok'delar, Stave of the Ancient Keepers",
    slot=Slot.TWO_HAND,
    drop_chance_list=[50.0],
    ep_map={
        SpecClass.MARKS_HUNTER:57,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Benediction",
    slot=Slot.TWO_HAND,
    drop_chance_list=[50.0],
    ep_map={
        SpecClass.HOLY_PRIEST:156,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Gloves of the Hypnotic Flame",
    slot=Slot.HANDS,
    drop_chance_list=[24.0],
    ep_map={
        SpecClass.FIRE_MAGE:36,
    },
    )

# Ragnaros
boss_name = "Ragnaros"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Choker of the Fire Lord",
    slot=Slot.NECK,
    drop_chance_list=[16.67],
    ep_map={
        SpecClass.RESTO_DRUID:36,
        SpecClass.FIRE_MAGE:35,
        SpecClass.RESTO_SHAMAN:42,
        SpecClass.ANY_WARLOCK:36,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Stormrage Legguards",
    slot=Slot.LEGS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_DRUID:81,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Crown of Destruction",
    slot=Slot.HEAD,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.FURY_WARRIOR:84,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodfang Pants",
    slot=Slot.LEGS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:105,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Band of Sulfuras",
    slot=Slot.FINGER,
    drop_chance_list=[19.05],
    ep_map={
        SpecClass.RESTO_DRUID:12,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonstalker's Legguards",
    slot=Slot.LEGS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.MARKS_HUNTER:137,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cloak of the Shrouded Mists",
    slot=Slot.BACK,
    drop_chance_list=[21.43],
    ep_map={
        SpecClass.MARKS_HUNTER:61,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Band of Accuria",
    slot=Slot.FINGER,
    drop_chance_list=[16.67],
    ep_map={
        SpecClass.MARKS_HUNTER:89,
        SpecClass.COMBAT_ROGUE:66,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Leggings of Transcendence",
    slot=Slot.LEGS,
    drop_chance_list=[14.0],
    ep_map={
        SpecClass.HOLY_PRIEST:120,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Perdition's Blade",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[13.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:906,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Malistar's Defender",
    slot=Slot.OFF_HAND,
    drop_chance_list=[7.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:68,
    },
    )

# MC Trash
boss_name = "MC Trash"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Arcanist Belt",
    slot=Slot.WAIST,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.FIRE_MAGE:18,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nightslayer Belt",
    slot=Slot.WAIST,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:65,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nightslayer Bracelets",
    slot=Slot.WRISTS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:38,
    },
    )

# Razorgore the Untamed
boss_name = "Razorgore the Untamed"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodfang Bracers",
    slot=Slot.WRISTS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:62,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nemesis Bracers",
    slot=Slot.WRISTS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.ANY_WARLOCK:18,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bracers of Ten Storms",
    slot=Slot.WRISTS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:55,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Stormrage Bracers",
    slot=Slot.WRISTS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_DRUID:43,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bindings of Transcendence",
    slot=Slot.WRISTS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.HOLY_PRIEST:67,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonstalker's Bracers",
    slot=Slot.WRISTS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.MARKS_HUNTER:64,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Mantle of the Blackwing Cabal",
    slot=Slot.SHOULDER,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.FIRE_MAGE:37,
        SpecClass.ANY_WARLOCK:38,

    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Netherwind Bindings",
    slot=Slot.WRISTS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.FIRE_MAGE:22,
    },
    )

# Vaelastrasz the Corrupt
boss_name = "Vaelastrasz the Corrupt"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Stormrage Belt",
    slot=Slot.WAIST,
    drop_chance_list=[20.38],
    ep_map={
        SpecClass.RESTO_DRUID:50,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nemesis Belt",
    slot=Slot.WAIST,
    drop_chance_list=[20.38],
    ep_map={
        SpecClass.ANY_WARLOCK:40,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodfang Belt",
    slot=Slot.WAIST,
    drop_chance_list=[23.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:75,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonstalker's Belt",
    slot=Slot.WAIST,
    drop_chance_list=[23.1],
    ep_map={
        SpecClass.MARKS_HUNTER:84,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Mind Quickening Gem",
    slot=Slot.TRINKET,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.FIRE_MAGE:30,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Belt of Transcendence",
    slot=Slot.WAIST,
    drop_chance_list=[23.0],
    ep_map={
        SpecClass.HOLY_PRIEST:67,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Belt of Ten Storms",
    slot=Slot.WAIST,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:48,
    },
    )

# Broodlord Lashlayer
boss_name = "Broodlord Lashlayer"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Stormrage Boots",
    slot=Slot.FEET,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_DRUID:46,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Greaves of Ten Storms",
    slot=Slot.FEET,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:39,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Heartstriker",
    slot=Slot.RANGED,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:24,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Boots of Transcendence",
    slot=Slot.FEET,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.HOLY_PRIEST:75,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonstalker's Greaves",
    slot=Slot.FEET,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.MARKS_HUNTER:84,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bracers of Arcane Accuracy",
    slot=Slot.WRISTS,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.FIRE_MAGE:36,
        SpecClass.ANY_WARLOCK:44,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Maladath, Runed Blade of the Black Flight",
    slot=Slot.OFF_HAND,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:900,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodfang Boots",
    slot=Slot.FEET,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:54,
    },
    )

# Firemaw
boss_name = "Firemaw"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Firemaw's Clutch",
    slot=Slot.WAIST,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.FIRE_MAGE:37,
        SpecClass.ANY_WARLOCK:38,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cloak of Firemaw",
    slot=Slot.BACK,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:50,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Claw of the Black Drake",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:955,
    },
    )

# Flamegor
boss_name = "Flamegor"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Shroud of Pure Thought",
    slot=Slot.BACK,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:82,
    },
    )

# Ebonroc
boss_name = "Ebonroc"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonbreath Hand Cannon",
    slot=Slot.RANGED,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:27,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Drake Fang Talisman",
    slot=Slot.TRINKET,
    drop_chance_list=[18.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:92,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Band of Forced Concentration",
    slot=Slot.FINGER,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.FIRE_MAGE:36,
        SpecClass.ANY_WARLOCK:44,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ebony Flame Gloves",
    slot=Slot.HANDS,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.ANY_WARLOCK:46,
    },
    )

# Three Drakes
bpc.addLoot(
    boss_list=["Ebonroc","Flamegor","Firemaw"],
    loot_name="Ring of Blackrock",
    slot=Slot.FINGER,
    drop_chance_list=[13.0,13.0,13.0],
    ep_map={
        SpecClass.HOLY_PRIEST:51,
        SpecClass.RESTO_DRUID:46,
        SpecClass.RESTO_SHAMAN:73,
    },
    )
bpc.addLoot(
    boss_list=["Ebonroc","Flamegor","Firemaw"],
    loot_name="Rejuvenating Gem",
    slot=Slot.TRINKET,
    drop_chance_list=[12.0,12.0,12.0],
    ep_map={
        SpecClass.RESTO_DRUID:93,
        SpecClass.HOLY_PRIEST:98,
        SpecClass.RESTO_SHAMAN:120,
    },
    )
bpc.addLoot(
    boss_list=["Firemaw","Flamegor","Ebonroc"],
    loot_name="Drake Talon Pauldrons",
    slot=Slot.SHOULDER,
    drop_chance_list=[13.0,13.0,13.0],
    ep_map={
        SpecClass.FURY_WARRIOR:60,
    },
    )
bpc.addLoot(
    boss_list=["Firemaw","Flamegor","Ebonroc"],
    loot_name="Stormrage Handguards",
    slot=Slot.HANDS,
    drop_chance_list=[13.0,13.0,13.0],
    ep_map={
        SpecClass.RESTO_DRUID:55,
    },
    )
bpc.addLoot(
    boss_list=["Firemaw","Flamegor","Ebonroc"],
    loot_name="Gauntlets of Ten Storms",
    slot=Slot.HANDS,
    drop_chance_list=[13.0,13.0,13.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:69,
    },
    )
bpc.addLoot(
    boss_list=["Firemaw","Flamegor","Ebonroc"],
    loot_name="Handguards of Transcendence",
    slot=Slot.HANDS,
    drop_chance_list=[13.0,13.0,13.0],
    ep_map={
        SpecClass.HOLY_PRIEST:68,
    },
    )
bpc.addLoot(
    boss_list=["Firemaw","Flamegor","Ebonroc"],
    loot_name="Dragonstalker's Gauntlets",
    slot=Slot.HANDS,
    drop_chance_list=[13.0,13.0,13.0],
    ep_map={
        SpecClass.MARKS_HUNTER:84,
    },
    )
bpc.addLoot(
    boss_list=["Firemaw","Flamegor","Ebonroc"],
    loot_name="Netherwind Gloves",
    slot=Slot.HANDS,
    drop_chance_list=[13.0,13.0,13.0],
    ep_map={
        SpecClass.FIRE_MAGE:35,
    },
    )
bpc.addLoot(
    boss_list=["Firemaw","Flamegor","Ebonroc"],
    loot_name="Bloodfang Gloves",
    slot=Slot.HANDS,
    drop_chance_list=[13.0,13.0,13.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:59,
    },
    )

# Chromaggus
boss_name = "Chromaggus"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Stormrage Pauldrons",
    slot=Slot.SHOULDER,
    drop_chance_list=[20.14],
    ep_map={
        SpecClass.RESTO_DRUID:52,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Nemesis Spaulders",
    slot=Slot.SHOULDER,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.ANY_WARLOCK:27,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Empowered Leggings",
    slot=Slot.LEGS,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_DRUID:102,
        SpecClass.HOLY_PRIEST:119,
        SpecClass.RESTO_SHAMAN:91,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonstalker's Spaulders",
    slot=Slot.SHOULDER,
    drop_chance_list=[22.0],
    ep_map={
        SpecClass.MARKS_HUNTER:86,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ashjre'thul, Crossbow of Smiting",
    slot=Slot.RANGED,
    drop_chance_list=[9.67],
    ep_map={
        SpecClass.MARKS_HUNTER:1014,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Claw of Chromaggus",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[9.8],
    ep_map={
        SpecClass.FIRE_MAGE:67,
        SpecClass.ANY_WARLOCK:69,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Angelista's Grasp",
    slot=Slot.WAIST,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.FIRE_MAGE:30,
        SpecClass.ANY_WARLOCK:45,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Pauldrons of Transcendence",
    slot=Slot.SHOULDER,
    drop_chance_list=[23.0],
    ep_map={
        SpecClass.HOLY_PRIEST:70,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Chromatically Tempered Sword",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[9.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:991,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodfang Spaulders",
    slot=Slot.SHOULDER,
    drop_chance_list=[23.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:54,
    },
    )

# Nefarian
boss_name = "Nefarian"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Stormrage Chestguard",
    slot=Slot.CHEST,
    drop_chance_list=[19.75],
    ep_map={
        SpecClass.RESTO_DRUID:67,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Breastplate of Ten Storms",
    slot=Slot.CHEST,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:60,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Mish'undare, Circlet of the Mind Flayer",
    slot=Slot.HEAD,
    drop_chance_list=[18.0],
    ep_map={
        SpecClass.ANY_WARLOCK:67,
        SpecClass.FIRE_MAGE:64,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Staff of the Shadow Flame",
    slot=Slot.TWO_HAND,
    drop_chance_list=[9.0],
    ep_map={
        SpecClass.ANY_WARLOCK:117,
        SpecClass.FIRE_MAGE:114,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Lok'amir il Romathis",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[8.86],
    ep_map={
        SpecClass.RESTO_DRUID:93,
        SpecClass.RESTO_SHAMAN:106,
        SpecClass.HOLY_PRIEST:114,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Pure Elementium Band",
    slot=Slot.FINGER,
    drop_chance_list=[18.74],
    ep_map={
        SpecClass.RESTO_DRUID:61,
        SpecClass.HOLY_PRIEST:76,
        SpecClass.RESTO_SHAMAN:65,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Prestor's Talisman of Connivery",
    slot=Slot.NECK,
    drop_chance_list=[18.94],
    ep_map={
        SpecClass.MARKS_HUNTER:106,
        SpecClass.COMBAT_ROGUE:75,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dragonstalker's Breastplate",
    slot=Slot.CHEST,
    drop_chance_list=[21.71],
    ep_map={
        SpecClass.MARKS_HUNTER:123,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Master Dragonslayer's Ring",
    slot=Slot.FINGER,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.MARKS_HUNTER:70,
        SpecClass.COMBAT_ROGUE:66,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ashkandi, Greatsword of the Brotherhood",
    slot=Slot.TWO_HAND,
    drop_chance_list=[9.11],
    ep_map={
        SpecClass.MARKS_HUNTER:86,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cloak of the Brood Lord",
    slot=Slot.BACK,
    drop_chance_list=[18.41],
    ep_map={
        SpecClass.FIRE_MAGE:31,
        SpecClass.ANY_WARLOCK:32,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Neltharion's Tear",
    slot=Slot.TRINKET,
    drop_chance_list=[18.25],
    ep_map={
        SpecClass.FIRE_MAGE:70,
        SpecClass.ANY_WARLOCK:83,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Robes of Transcendence",
    slot=Slot.CHEST,
    drop_chance_list=[21.0],
    ep_map={
        SpecClass.HOLY_PRIEST:107,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodfang Chestpiece",
    slot=Slot.CHEST,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:122,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Boots of the Shadow Flame",
    slot=Slot.FEET,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:80,
    },
    )

# BWL Trash
boss_name = "BWL Trash"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Essence Gatherer",
    slot=Slot.RANGED,
    drop_chance_list=[5.0],
    ep_map={
        SpecClass.HOLY_PRIEST:26,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Boots of Pure Thought",
    slot=Slot.FEET,
    drop_chance_list=[5.0],
    ep_map={
        SpecClass.HOLY_PRIEST:90,
        SpecClass.RESTO_SHAMAN:76,
        SpecClass.RESTO_DRUID:71,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Band of Dark Dominion",
    slot=Slot.FINGER,
    drop_chance_list=[5.0],
    ep_map={
        SpecClass.ANY_WARLOCK:35,
    },
    )

# Jin'do the Hexxer
boss_name = "Jin'do the Hexxer"
bpc.addLoot(
    boss_list=["Jin'do the Hexxer","Bloodlord Mandokir"],
    loot_name="Primal Hakkari Idol",
    slot=Slot.ZG_ENCHANTS,
    drop_chance_list=[100.0,100.0],
    ep_map={
        SpecClass.RESTO_DRUID:27,
        SpecClass.MARKS_HUNTER:46,
        SpecClass.FIRE_MAGE:31,
        SpecClass.HOLY_PRIEST:38,
        SpecClass.COMBAT_ROGUE:28,
        SpecClass.RESTO_SHAMAN:31,
        SpecClass.ANY_WARLOCK:18,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Jin'do's Evil Eye",
    slot=Slot.NECK,
    drop_chance_list=[14.4],
    ep_map={
        SpecClass.RESTO_DRUID:50,
        SpecClass.HOLY_PRIEST:64,
        SpecClass.RESTO_SHAMAN:57,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Jin'do's Hexxer",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[14.61],
    ep_map={
        SpecClass.RESTO_DRUID:64,
        SpecClass.RESTO_SHAMAN:62,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodtinged Gloves",
    slot=Slot.HANDS,
    drop_chance_list=[16.66],
    ep_map={
        SpecClass.FIRE_MAGE:34,
        SpecClass.ANY_WARLOCK:41,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Jin'do's Bag of Whammies",
    slot=Slot.OFF_HAND,
    drop_chance_list=[14.15],
    ep_map={
        SpecClass.FIRE_MAGE:33,
        SpecClass.ANY_WARLOCK:41,
    },
    )

# High Priestess Jeklik
boss_name = "High Priestess Jeklik"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Primalist's Band",
    slot=Slot.FINGER,
    drop_chance_list=[19.7],
    ep_map={
        SpecClass.RESTO_DRUID:21,
        SpecClass.HOLY_PRIEST:52,
        SpecClass.RESTO_SHAMAN:48,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Jeklik's Opaline Talisman",
    slot=Slot.NECK,
    drop_chance_list=[18.0],
    ep_map={
        SpecClass.FIRE_MAGE:22,
    },
    )

# High Priest Venoxis
boss_name = "High Priest Venoxis"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Zulian Tigerhide Cloak",
    slot=Slot.BACK,
    drop_chance_list=[18.41],
    ep_map={
        SpecClass.MARKS_HUNTER:58,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Blooddrenched Footpads",
    slot=Slot.FEET,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:58,
    },
    )

# High Priest Thekal
boss_name = "High Priest Thekal"

# High Priestess Mar'li
boss_name = "High Priestess Mar'li"

# High Priestess Arlokk
boss_name = "High Priestess Arlokk"

# Multiple
bpc.addLoot(
    boss_list=["High Priestess Arlokk","High Priestess Mar'li","High Priest Thekal","High Priest Venoxis","High Priestess Jeklik"],
    loot_name="Band of Servitude",
    slot=Slot.FINGER,
    drop_chance_list=[10.0,10.0,10.0,10.0,10.0],
    ep_map={
        SpecClass.FIRE_MAGE:25,
    },
    )
bpc.addLoot(
    boss_list=["High Priestess Arlokk","High Priestess Mar'li","High Priest Thekal","High Priest Venoxis","High Priestess Jeklik"],
    loot_name="Belt of Untapped Power",
    slot=Slot.WAIST,
    drop_chance_list=[9.0,9.0,9.0,9.0,9.0],
    ep_map={
        SpecClass.FIRE_MAGE:30,
        SpecClass.ANY_WARLOCK:31,
    },
    )

# Bloodlord Mandokir
boss_name = "Bloodlord Mandokir"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Hakkari Loa Cloak",
    slot=Slot.BACK,
    drop_chance_list=[17.69],
    ep_map={
        SpecClass.RESTO_DRUID:38,
        SpecClass.RESTO_SHAMAN:40,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Primalist's Seal",
    slot=Slot.FINGER,
    drop_chance_list=[18.85],
    ep_map={
        SpecClass.RESTO_DRUID:36,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Mandokir's Sting",
    slot=Slot.RANGED,
    drop_chance_list=[9.49],
    ep_map={
        SpecClass.MARKS_HUNTER:816,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Zanzil's Seal",
    slot=Slot.FINGER,
    drop_chance_list=[18.0],
    ep_map={
        SpecClass.FIRE_MAGE:26,
    },
    )

# Hakkar
boss_name = "Hakkar"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Zandalarian Hero Charm",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:34,
        SpecClass.HOLY_PRIEST:34,
        SpecClass.RESTO_SHAMAN:34,
        SpecClass.ANY_WARLOCK:17,
        SpecClass.FIRE_MAGE:17,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Gurubashi Dwarf Destroyer",
    slot=Slot.RANGED,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:30,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Warblade of the Hakkari",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.MARKS_HUNTER:57,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Fang of the Faceless",
    slot=Slot.OFF_HAND,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.MARKS_HUNTER:57,
        SpecClass.COMBAT_ROGUE:842,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cloak of Consumption",
    slot=Slot.BACK,
    drop_chance_list=[20.0],
    ep_map={
        SpecClass.FIRE_MAGE:38,
        SpecClass.ANY_WARLOCK:45,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Touch of Chaos",
    slot=Slot.RANGED,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.FIRE_MAGE:18,
        SpecClass.ANY_WARLOCK:18,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bloodcaller",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.FIRE_MAGE:36,
        SpecClass.ANY_WARLOCK:37,
    },
    )

# Kurinnaxx
boss_name = "Kurinnaxx"

# General Rajaxx
boss_name = "General Rajaxx"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Boots of the Vanguard",
    slot=Slot.FEET,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:66,
    },
    )

# Moam
boss_name = "Moam"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Talon of Furious Concentration",
    slot=Slot.OFF_HAND,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.FIRE_MAGE:35,
        SpecClass.ANY_WARLOCK:36,
    },
    )

# Buru the Gorger
boss_name = "Buru the Gorger"

# Ayamiss the Hunter
boss_name = "Ayamiss the Hunter"

# Ossirian the Unscarred
boss_name = "Ossirian the Unscarred"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Amulet of the Shifting Sands",
    slot=Slot.NECK,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:64,
        SpecClass.HOLY_PRIEST:67,
        SpecClass.RESTO_SHAMAN:82,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Gloves of Dark Wisdom",
    slot=Slot.HANDS,
    drop_chance_list=[17.0],
    ep_map={
        SpecClass.RESTO_DRUID:56,
        SpecClass.HOLY_PRIEST:76,
        SpecClass.RESTO_SHAMAN:89,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Crossbow of Imminent Doom",
    slot=Slot.RANGED,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:37,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Shackles of the Unscarred",
    slot=Slot.WRISTS,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.FIRE_MAGE:23,
        SpecClass.ANY_WARLOCK:24,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Staff of the Ruins",
    slot=Slot.TWO_HAND,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.FIRE_MAGE:90,
        SpecClass.ANY_WARLOCK:99,
    },
    )

# Multiple
bpc.addLoot(
    boss_list=["Moam","Buru the Gorger","Ayamiss the Hunter","Ossirian the Unscarred"],
    loot_name="Gavel of Infinite Wisdom",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[70.0,22.0,16.0,64.0],
    ep_map={
        SpecClass.HOLY_PRIEST:117,
    },
    )
bpc.addLoot(
    boss_list=["Moam","Ossirian the Unscarred","Ayamiss the Hunter","Buru the Gorger"],
    loot_name="Blade of Vaulted Secrets",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[70.0,64.0,16.0,22.0],
    ep_map={
        SpecClass.FIRE_MAGE:56,
    },
    )
bpc.addLoot(
    boss_list=["Moam","Ossirian the Unscarred","Ayamiss the Hunter","Buru the Gorger"],
    loot_name="Kris of Unspoken Names",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[70.0,64.0,16.0,22.0],
    ep_map={
        SpecClass.ANY_WARLOCK:61,
    },
    )
bpc.addLoot(
    boss_list=["Kurinnaxx","General Rajaxx","Ayamiss the Hunter","Buru the Gorger"],
    loot_name="Cloak of Veiled Shadows",
    slot=Slot.BACK,
    drop_chance_list=[50.0,50.0,50.0,50.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:52,
    },
    )
bpc.addLoot(
    boss_list=["Ossirian the Unscarred","Ayamiss the Hunter","Buru the Gorger","Moam","General Rajaxx","Kurinnaxx"],
    loot_name="Ring of Unspoken Names",
    slot=Slot.FINGER,
    drop_chance_list=[17.0,50.0,50.0,17.0,17.0,17.0],
    ep_map={
        SpecClass.ANY_WARLOCK:46,
    },
    )
bpc.addLoot(
    boss_list=["Ossirian the Unscarred","Ayamiss the Hunter","Buru the Gorger","Moam","General Rajaxx","Kurinnaxx"],
    loot_name="Band of Vaulted Secrets",
    slot=Slot.FINGER,
    drop_chance_list=[17.0,50.0,50.0,17.0,17.0,17.0],
    ep_map={
        SpecClass.FIRE_MAGE:30,
    },
    )

# AQ20 Trash
boss_name = "AQ20 Trash"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Fury of the Forgotten Swarm",
    slot=Slot.NECK,
    drop_chance_list=[5.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:50,
        SpecClass.FURY_WARRIOR:56,
    },
    )

# The Prophet Skeram
boss_name = "The Prophet Skeram"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cloak of Concentrated Hatred",
    slot=Slot.BACK,
    drop_chance_list=[17.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:61,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Staff of the Qiraji Prophets",
    slot=Slot.TWO_HAND,
    drop_chance_list=[8.0],
    ep_map={
        SpecClass.FIRE_MAGE:61,
        SpecClass.ANY_WARLOCK:63,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Leggings of Immersion",
    slot=Slot.LEGS,
    drop_chance_list=[17.0],
    ep_map={
        SpecClass.RESTO_DRUID:64,
        SpecClass.RESTO_SHAMAN:101,
    },
    )

# Battleguard Sartura
boss_name = "Battleguard Sartura"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Creeping Vine Helm",
    slot=Slot.HEAD,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:87,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Silithid Claw",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[8.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:938,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Gloves of Enforcement",
    slot=Slot.HANDS,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:87,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Sartura's Might",
    slot=Slot.OFF_HAND,
    drop_chance_list=[9.0],
    ep_map={
        SpecClass.HOLY_PRIEST:75,
        SpecClass.RESTO_SHAMAN:88,
        SpecClass.RESTO_DRUID:68,
    },
    )

# Vem
boss_name = "Vem"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Angelista's Charm",
    slot=Slot.NECK,
    drop_chance_list=[25.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:84,
    },
    )

# Princess Yauj
boss_name = "Princess Yauj"

# Lord Kri
boss_name = "Lord Kri"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Vest of Swift Execution",
    slot=Slot.CHEST,
    drop_chance_list=[27.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:101,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ring of the Devoured",
    slot=Slot.FINGER,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.HOLY_PRIEST:58,
        SpecClass.RESTO_SHAMAN:79,
        SpecClass.RESTO_DRUID:43,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Wand of Qiraji Nobility",
    slot=Slot.RANGED,
    drop_chance_list=[14.0],
    ep_map={
        SpecClass.FIRE_MAGE:19,
        SpecClass.ANY_WARLOCK:19,
    },
    )

# Fankriss the Unyielding
boss_name = "Fankriss the Unyielding"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Barbed Choker",
    slot=Slot.NECK,
    drop_chance_list=[15.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:67,
        SpecClass.FURY_WARRIOR:64,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Mantle of Wicked Revenge",
    slot=Slot.NECK,
    drop_chance_list=[17.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:75,
        SpecClass.COMBAT_ROGUE:62,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ancient Qiraji Ripper",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:1001,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Robes of the Guardian Saint",
    slot=Slot.CHEST,
    drop_chance_list=[19.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:138,
        SpecClass.RESTO_DRUID:98,
        SpecClass.HOLY_PRIEST:120,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Totem of Life",
    slot=Slot.RANGED,
    drop_chance_list=[7.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:30,
    },
    )

# Viscidus
boss_name = "Viscidus"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ring of the Qiraji Fury",
    slot=Slot.FINGER,
    drop_chance_list=[13.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:63,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Sharpened Silithid Femur",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[14.0],
    ep_map={
        SpecClass.FIRE_MAGE:86,
        SpecClass.ANY_WARLOCK:87,
    },
    )

# Princess Huhuran
boss_name = "Princess Huhuran"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Huhuran's Stinger",
    slot=Slot.RANGED,
    drop_chance_list=[8.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:34,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Gloves of the Messiah",
    slot=Slot.HANDS,
    drop_chance_list=[18.0],
    ep_map={
        SpecClass.HOLY_PRIEST:81,
        SpecClass.RESTO_SHAMAN:106,
        SpecClass.RESTO_DRUID:61,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ring of the Martyr",
    slot=Slot.FINGER,
    drop_chance_list=[17.0],
    ep_map={
        SpecClass.HOLY_PRIEST:69,
        SpecClass.RESTO_SHAMAN:81,
        SpecClass.RESTO_DRUID:66,
    },
    )

# Twin Emperors
boss_name = "Twin Emperors"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Deathdealer's Helm",
    slot=Slot.HEAD,
    drop_chance_list=[80.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:124,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Doomcaller's Circlet",
    slot=Slot.HEAD,
    drop_chance_list=[80.0],
    ep_map={
        SpecClass.ANY_WARLOCK:72,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Enigma Circlet",
    slot=Slot.HEAD,
    drop_chance_list=[80.0],
    ep_map={
        SpecClass.FIRE_MAGE:77,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Amulet of Vek'nilash",
    slot=Slot.NECK,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.ANY_WARLOCK:41,
        SpecClass.FIRE_MAGE:40,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Qiraji Execution Bracers",
    slot=Slot.WRISTS,
    drop_chance_list=[15.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:65,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Gloves of the Hidden Temple",
    slot=Slot.HANDS,
    drop_chance_list=[14.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:60,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Bracelets of Royal Redemptione",
    slot=Slot.WRISTS,
    drop_chance_list=[14.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:65,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Royal Scepter of Vek'lor",
    slot=Slot.OFF_HAND,
    drop_chance_list=[10.0],
    ep_map={
        SpecClass.FIRE_MAGE:47,
        SpecClass.ANY_WARLOCK:55,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Boots of Epiphany",
    slot=Slot.FEET,
    drop_chance_list=[14.0],
    ep_map={
        SpecClass.FIRE_MAGE:38,
        SpecClass.ANY_WARLOCK:39,
    },
    )

# Ouro
boss_name = "Ouro"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Larvae of the Great Worm",
    slot=Slot.RANGED,
    drop_chance_list=[15.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:41,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Deathdealer's Leggings",
    slot=Slot.LEGS,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:115,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Don Rigoberto's Lost Hat",
    slot=Slot.HEAD,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:159,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Wormscale Blocker",
    slot=Slot.OFF_HAND,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:87,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Burrower Bracers",
    slot=Slot.WRISTS,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.FIRE_MAGE:31,
        SpecClass.ANY_WARLOCK:32,
    },
    )

# C'Thun
boss_name = "C'Thun"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cloak of the Fallen God",
    slot=Slot.BACK,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:62,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cloak of Clarity",
    slot=Slot.BACK,
    drop_chance_list=[32.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:102,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Deathdealer's Vest",
    slot=Slot.CHEST,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:132,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Amulet of the Fallen God",
    slot=Slot.NECK,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:93,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Death's Sting",
    slot=Slot.OFF_HAND,
    drop_chance_list=[8.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:1058,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Belt of Never-ending Agony",
    slot=Slot.WAIST,
    drop_chance_list=[17.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:105,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Scepter of the False Prophet",
    slot=Slot.MAIN_HAND,
    drop_chance_list=[6.0],
    ep_map={
        SpecClass.HOLY_PRIEST:220,
        SpecClass.RESTO_SHAMAN:228,
        SpecClass.RESTO_DRUID:202,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Grasp of the Old God",
    slot=Slot.WAIST,
    drop_chance_list=[16.0],
    ep_map={
        SpecClass.HOLY_PRIEST:106,
        SpecClass.RESTO_SHAMAN:124,
        SpecClass.RESTO_DRUID:86,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Cloak of the Devoured",
    slot=Slot.BACK,
    drop_chance_list=[12.0],
    ep_map={
        SpecClass.FIRE_MAGE:45,
        SpecClass.ANY_WARLOCK:52,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Eyestalk Waist Cord",
    slot=Slot.WAIST,
    drop_chance_list=[30.0],
    ep_map={
        SpecClass.FIRE_MAGE:55,
        SpecClass.ANY_WARLOCK:56,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Dark Storm Gauntlets",
    slot=Slot.HANDS,
    drop_chance_list=[22.0],
    ep_map={
        SpecClass.FIRE_MAGE:53,
        SpecClass.ANY_WARLOCK:61,
    },
    )
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ring of the Fallen God",
    slot=Slot.FINGER,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:51,
        SpecClass.ANY_WARLOCK:58,
    },
    )

# AQ40 Trash
boss_name = "AQ40 Trash"
bpc.addLoot(
    boss_list=[boss_name],
    loot_name="Ritssyn's Ring of Chaos",
    slot=Slot.FINGER,
    drop_chance_list=[5.0],
    ep_map={
        SpecClass.FIRE_MAGE:37,
        SpecClass.ANY_WARLOCK:38,
    },
    )

# Multiple
# Imperial Qiraji Regalia
bpc.addLoot(
    boss_list=["Battleguard Sartura","Vem","Princess Yauj","Fankriss the Unyielding","Viscidus","Princess Huhuran","Twin Emperors","Ouro"],
    loot_name="Blessed Qiraji Augur Staff",
    slot=Slot.TWO_HAND,
    drop_chance_list=[8.0,9.0,15.0,7.0,10.0,9.0,8.0,10.0],
    ep_map={
        SpecClass.HOLY_PRIEST:223,
        SpecClass.RESTO_SHAMAN:262,
        SpecClass.RESTO_DRUID:195,
    },
    )
bpc.addLoot(
    boss_list=["Battleguard Sartura","Vem","Princess Yauj","Fankriss the Unyielding","Viscidus","Princess Huhuran","Twin Emperors","Ouro"],
    loot_name="Blessed Qiraji Acolyte Staff",
    slot=Slot.TWO_HAND,
    drop_chance_list=[8.0,9.0,15.0,7.0,10.0,9.0,8.0,10.0],
    ep_map={
        SpecClass.FIRE_MAGE:121,
        SpecClass.ANY_WARLOCK:137,
    },
    )
bpc.addLoot(
    boss_list=["Battleguard Sartura","Vem","Princess Yauj","Fankriss the Unyielding","Viscidus","Princess Huhuran","Twin Emperors","Ouro"],
    loot_name="Blessed Qiraji War Hammer",
    slot=Slot.TWO_HAND,
    drop_chance_list=[8.0,9.0,15.0,7.0,10.0,9.0,8.0,10.0],
    ep_map={
        SpecClass.FERAL_DRUID:368,
    },
    )
# Imperial Qiraji Armaments
bpc.addLoot(
    boss_list=["Battleguard Sartura","Vem","Princess Yauj","Lord Kri","Fankriss the Unyielding","Viscidus","Princess Huhuran","Twin Emperors","Ouro"],
    loot_name="Blessed Qiraji Pugio",
    slot=Slot.OFF_HAND,
    drop_chance_list=[7.0,8.0,16.0,18.0,8.0,21.0,8.0,8.0,8.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:992,
    },
    )
# Qiraji Bindings of Command and Qiraji Bindings of Dominance
bpc.addLoot(
    boss_list=["Viscidus","Princess Huhuran"],
    loot_name="Deathdealer's Spaulders",
    slot=Slot.SHOULDER,
    drop_chance_list=[100.0,100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:89,
    },
    )
bpc.addLoot(
    boss_list=["Viscidus","Princess Huhuran"],
    loot_name="Conqueror's Spaulders",
    slot=Slot.SHOULDER,
    drop_chance_list=[100.0,100.0],
    ep_map={
        SpecClass.FURY_WARRIOR:76,
    },
    )
bpc.addLoot(
    boss_list=["Viscidus","Princess Huhuran"],
    loot_name="Doomcaller's Mantle",
    slot=Slot.SHOULDER,
    drop_chance_list=[100.0,100.0],
    ep_map={
        SpecClass.ANY_WARLOCK:51,
    },
    )
bpc.addLoot(
    boss_list=["Viscidus","Princess Huhuran"],
    loot_name="Enigma Shoulderpads",
    slot=Slot.SHOULDER,
    drop_chance_list=[100.0,100.0],
    ep_map={
        SpecClass.FIRE_MAGE:32,
    },
    )
bpc.addLoot(
    boss_list=["Viscidus","Princess Huhuran"],
    loot_name="Enigma Boots",
    slot=Slot.FEET,
    drop_chance_list=[100.0,100.0],
    ep_map={
        SpecClass.FIRE_MAGE:44,
    },
    )

# None
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Royal Seal of Eldre'Thalas",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:44,
        SpecClass.MARKS_HUNTER:48,
        SpecClass.HOLY_PRIEST:47,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Hide of the Wild",
    slot=Slot.BACK,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:45,
        SpecClass.HOLY_PRIEST:54,
        SpecClass.RESTO_SHAMAN:54,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Idol of the Moon",
    slot=Slot.RANGED,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:1,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Robes of the Exalted",
    slot=Slot.CHEST,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:75,
        SpecClass.RESTO_SHAMAN:74,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Fordring's Seal",
    slot=Slot.FINGER,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:39,
        SpecClass.HOLY_PRIEST:43,
        SpecClass.RESTO_SHAMAN:43,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Lei of the Lifegiver",
    slot=Slot.OFF_HAND,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:62,
        SpecClass.HOLY_PRIEST:64,
        SpecClass.RESTO_SHAMAN:71,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Verdant Footpads",
    slot=Slot.FEET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:37,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Corehound Belt",
    slot=Slot.WAIST,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:67,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Devilsaur Eye",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.MARKS_HUNTER:32,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Blackhand's Breadth",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.MARKS_HUNTER:57,
        SpecClass.COMBAT_ROGUE:46
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Don Julio's Band",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.MARKS_HUNTER:67,
        SpecClass.COMBAT_ROGUE:57,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Cape of the Black Baron",
    slot=Slot.BACK,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.MARKS_HUNTER:62,
        SpecClass.COMBAT_ROGUE:49,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Bloodvine Vest",
    slot=Slot.CHEST,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:56,
        SpecClass.ANY_WARLOCK:70,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Bloodvine Leggings",
    slot=Slot.LEGS,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:51,
        SpecClass.ANY_WARLOCK:58,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Bloodvine Boots",
    slot=Slot.FEET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:35,
        SpecClass.ANY_WARLOCK:43,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Band of Rumination",
    slot=Slot.FINGER,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:12,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Wand of Biting Cold",
    slot=Slot.RANGED,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:0,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Champion's Silk Cowl",
    slot=Slot.HEAD,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:37,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Champion's Silk Mantle",
    slot=Slot.SHOULDER,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:29,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Eye of the Beast",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:24,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Tome of Fiery Arcana",
    slot=Slot.OFF_HAND,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:40,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Tome of Shadow Force",
    slot=Slot.OFF_HAND,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.ANY_WARLOCK:34,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Darkmoon Card: Blue Dragon",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.HOLY_PRIEST:56,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Animated Chain Necklace",
    slot=Slot.NECK,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_DRUID:36,
        SpecClass.HOLY_PRIEST:40,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Glowstar Rod of Healing",
    slot=Slot.RANGED,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.HOLY_PRIEST:18,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Wizard's Hand of Wrath",
    slot=Slot.RANGED,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:10,
        SpecClass.ANY_WARLOCK:10,
    },
    )   
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Satyr's Bow",
    slot=Slot.RANGED,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:24,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Seal of the Gurubashi Berserker",
    slot=Slot.FINGER,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:40,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Hand of Justice",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:50,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Mindtap Talisman",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:66,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Briarwood Reed",
    slot=Slot.TRINKET,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.RESTO_SHAMAN:29,
        SpecClass.ANY_WARLOCK:29,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Stormrager",
    slot=Slot.RANGED,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:1,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Bonecreeper Stylus",
    slot=Slot.RANGED,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FIRE_MAGE:12,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Zandalar Madcap's Tunic",
    slot=Slot.CHEST,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.COMBAT_ROGUE:90,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Felcloth Gloves",
    slot=Slot.HANDS,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.ANY_WARLOCK:33,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Skul's Ghastly Touch",
    slot=Slot.RANGED,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.ANY_WARLOCK:14,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Lionheart Helm",
    slot=Slot.HEAD,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FURY_WARRIOR:116,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Abyssal Plate Legplates of Striking",
    slot=Slot.LEGS,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FURY_WARRIOR:65,
    },
    )
bpc.addLoot(
    boss_list=["CURRENT"],
    loot_name="Eldritch Reinforced Legplate",
    slot=Slot.LEGS,
    drop_chance_list=[100.0],
    ep_map={
        SpecClass.FURY_WARRIOR:59,
    },
    )

# do the thing
bpc.calc()
