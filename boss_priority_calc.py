from enum import IntEnum
import numpy as np
import matplotlib as plt

class SpecClass(IntEnum):
    NONE = 0
    RESTO_DRUID = 1
    FERAL_DRUID = 2
    ANY_HUNTER = 3
    ANY_MAGE = 4
    HOLY_PALADIN = 5
    HOLY_PRIEST = 6
    ANY_ROGUE = 7
    RESTO_SHAMAN = 8
    ANY_WARLOCK = 9
    PROT_WARRIOR = 10
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
    FINGERS_1 = 10
    FINGERS_2 = 11
    TRINKET_1 = 12
    TRINKET_2 = 13
    BACK = 14
    MAIN_HAND = 15
    OFF_HAND = 16
    TWO_HAND = 17
    RANGED = 18
    HEAD_ENCHANT = 19
    LEGS_ENCHANT = 20
    SIZE = 21

class CharacterData:

    def __init__(self,name,spec_class,head,neck,shoulder,chest,waist,legs,feet,wrist,hands,finger_1,finger_2,trinket_1,trinket_2,back,mh,oh,th,ranged,head_enchant,legs_enchant):
        # character name
        self.name = name
        # character SpecClass
        self.spec_class = spec_class
        # map from slot to name of item that character has
        self.gear = []
        self.gear[Slot.HEAD] = head
        self.gear[Slot.NECK] = neck
        self.gear[Slot.SHOULDER] = shoulder
        self.gear[Slot.CHEST] = chest
        self.gear[Slot.WAIST] = waist
        self.gear[Slot.LEGS] = legs
        self.gear[Slot.FEET] = feet
        self.gear[Slot.WRISTS] = wrist
        self.gear[Slot.HANDS] = hands
        self.gear[Slot.FINGERS_1] = finger_1
        self.gear[Slot.FINGERS_2] = finger_2
        self.gear[Slot.TRINKET_1] = trinket_1
        self.gear[Slot.TRINKET_2] = trinket_2
        self.gear[Slot.BACK] = back
        self.gear[Slot.MAIN_HAND] = mh
        self.gear[Slot.OFF_HAND] = oh
        self.gear[Slot.TWO_HAND] = th
        self.gear[Slot.RANGED] = ranged
        self.gear[Slot.HEAD_ENCHANT] = head_enchant
        self.gear[Slot.LEGS_ENCHANT] = legs_enchant

class RaidData:

    def __init__(self):
        self.raid = [] # list of CharacterData
    
    def addChar(self,name,spec_class,head,neck,shoulder,chest,waist,legs,feet,wrist,hands,finger_1,finger_2,trinket_1,trinket_2,back,mh,oh,th,ranged,head_enchant,legs_enchant):
        self.raid.append(CharacterData(name,spec_class,head,neck,shoulder,chest,waist,legs,feet,wrist,hands,finger_1,finger_2,trinket_1,trinket_2,back,mh,oh,th,ranged,head_enchant,legs_enchant))

class Loot:

    def __init__(self,name,slot,drop_chance):
        self.name = None
        self.slot = slot
        self.drop_chance = drop_chance
        self.ep_map = [SpecClass.SIZE]*0 # map from SpecClass to ep value

    def addEP(self,spec_class,ep):
        self.ep_map[spec_class] = ep

class BossData:

    def __init__(self):
        self.bosses = {
            # ONY
            "Onyxia",
            # MC
            "Lucifron",
            "Magmadar",
            "Gehennas",
            "Garr",
            "Baron Geddon",
            "Shazzrah",
            "Golemagg the Incinerator",
            "Sulfuron Harbinger",
            "Majordomo Executus",
            "Ragnaros",
            # BWL
            "Razorgore the Untamed",
            "Vaelastrasz the Corrupt",
            "Broodlord Lashlayer",
            "Firemaw",
            "Ebonroc",
            "Flamegor",
            "Chromaggus",
            "Nefarian",
            # ZG
            "High Priest Venoxis",
            "High Priestess Jeklik",
            "High Priestess Mar'li",
            "High Priest Thekal",
            "High Priestess Arlokk",
            "Hakkar",
            "Bloodlord Mandokir",
            "Gahz'ranka",
            "Jin'do the Hexxer",
            "Edge of Madness",
            # AQ20
            "Kurinnaxx",
            "General Rajaxx",
            "Moam",
            "Buru the Gorger",
            "Ayamiss the Hunter",
            "Ossirian the Unscarred",
            # AQ40
            "The Prophet Skeram",
            "Lord Kri",
            "Princess Yauj",
            "Vem",
            "Battleguard Sartura",
            "Fankriss the Unyielding",
            "Viscidus",
            "Princess Huhuran",
            "Twin Emperors",
            "Ouro",
            "C'Thun",
        }
        self.clear_time = {} # map from boss name to expected time to clear boss in minutes
        self.loot_tables = {} # map from boss name to array of loot names
        self.loot_db = {} # map from item name to loot item
        self.expected_upgrade_per_boss = {} # map from boss name to map of expected ep upgrade values for each character in a raid
        # init
        for boss in self.bosses:
            self.clear_time[boss] = None
            self.loot_tables[boss] = []
            self.expected_upgrade_per_boss[boss] = {}

    def addClearTime(self,boss,clear_time):
        self.clear_time[boss] = clear_time

    def addLoot(self,boss,loot_name,slot,drop_chance,ep_map):
        self.loot_tables[boss] = loot_name

        loot = Loot(loot_name,slot,drop_chance)
        for spec_class in ep_map:
            loot.addEP(spec_class,ep_map[spec_class])

        self.loot_db[loot_name] = loot
        
    def calc_expected_upgrades(self,raid_data):
        # calculate expected upgrade for a given raid of characters
        for boss in self.bosses:
            for char in raid_data.raid:
                char_name = char.name
                char_sc = char.spec_class
                # init total expected upgrade
                self.expected_upgrade_per_boss[boss][char_name] = 0
                for loot_name in loot_tables[boss]:
                    # fetch new loot
                    loot_new = self.loot_db[loot_name]
                    slot = loot_new.slot
                    drop_chance = loot_new.drop_chance
                    ep_new = loot_new.ep_map[char_sc]
                    # fetch current loot
                    loot_current = self.loot_db[char.gear[slot]]
                    ep_current = loot_current.ep_map[char_sc]
                    # calculate ep upgrade
                    if ep_new > ep_current:
                        self.expected_upgrade_per_boss[boss][char_name] += (ep_new - ep_current)*drop_chance               
        return
    
    def calc_mean_eupm(self):
        # calculates mean expected upgrade per minute per boss
        mean_eupm = {}
        for boss in self.bosses:
            mean_eupm[boss] = 0.0
            for char_name in self.expected_upgrade_per_boss[boss]:
                mean_eupm[boss] += self.expected_upgrade_per_boss[boss][char_name]
            mean_eupm[boss] /= len(self.expected_upgrade_per_boss[boss])
            mean_eupm[boss] /= len(self.clear_time[boss])
        return(OrderedDict(sorted(mean_eupm.items(), key=lambda t: t[1])))

# instantiate RaidData
rd = RaidData()

# add character to raid data
# Druid
rd.addChar(
    name=,
    spec_class=,
    head=,
    neck=,
    shoulder=,
    chest=,
    waist=,
    legs=,
    feet=,
    wrist=,
    hands=,
    finger_1=,
    finger_2=,
    trinket_1=,
    trinket_2=,
    back=,
    mh=,
    oh=,
    th=,
    ranged=,
    head_enchant=,
    legs_enchant=,
    )
# Hunter
# Mage

# instantiate BossData
bd = BossData()

# add loot items to boss loot tables
bd.addLoot(
    boss=,
    loot_name=,
    slot=,
    drop_chance=,
    ep_map=,
    )

# add clear times per boss
bd.addClearTime(
    boss=,
    clear_time=,
    )

# calculate raid upgrades
bd.calc_upgrades(rd)

# get map of boss to mean expected upgrade per minute
mean_eupm = bd.calc_mean_eupm()

# plot
plt.bar(mean_eupm.keys(),mean_eupm.values())