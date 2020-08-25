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
            "Onyxia",
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
        }
        self.loot_tables = {} # map from boss name to array of loot items
        self.upgrade_per_boss = {} # map from boss name to arrray of ep upgrade values for a given raid
        # init
        for boss in self.bosses:
            self.loot_tables[boss] = []
            self.upgrade_per_boss[boss] = np.array()

    def addLoot(self,boss,loot_name,slot,drop_chance,ep_map):
        loot = Loot(loot_name,slot,drop_chance)

        for spec_class in ep_map:
            loot.addEP(spec_class,ep_map[spec_class])

        self.loot_tables[boss].append(loot)
    
    def calc_upgrades(self,raid_data):
        # calculate upgrade for a given raid
        for boss in self.bosses:
            for loot in loot_tables[boss]:
                x = 1
                upgrade_per_boss[boss] = 1
        return

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

# instantiate RaidData
rd = RaidData()

# add character to raid data
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

# scan all bosses and collect average ep upgrade for raid
bd.calc_upgrades(rd)