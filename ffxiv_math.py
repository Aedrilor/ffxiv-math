# -*- coding: utf-8 -*-
"""
Created on Wed Feb 21 18:40:27 2024

Source for all formulas:
https://www.akhmorning.com/allagan-studies/

Inspiration for some implementation from:
https://github.com/Yurihaia/xivc/tree/master

@author: Phil S.
aka Xavrian Solain (Lamia)
"""

from dataclasses import dataclass
from enum import Enum
from math import floor, ceil
from random import random, randint

# Constants for stat scaling
DET_MOD = 140
TNC_MOD = 100
SPD_MOD = 130
CRT_RATE_MOD = 200
CRT_DMG_MOD = 200
DH_MOD = 550
PIE_MOD = 150

# Level modifiers
LEVEL_MOD_DATA = []
with open("ffxiv_allaganstudies_leveldata.csv", "r") as f:
    for line in f:
        if not line.startswith("#") and not line.isspace():
            LEVEL_MOD_DATA.append({})
            s = line[:-1].split(",")
            LEVEL_MOD_DATA[-1]["LEVEL"] = int(s[0])
            LEVEL_MOD_DATA[-1]["MAIN"] = int(s[1])
            LEVEL_MOD_DATA[-1]["SUB"] = int(s[2])
            LEVEL_MOD_DATA[-1]["DIV"] = int(s[3])
            LEVEL_MOD_DATA[-1]["HP"] = int(s[4])
            LEVEL_MOD_DATA[-1]["ELMT"] = int(s[5])
            LEVEL_MOD_DATA[-1]["THREAT"] = int(s[6])
LEVEL_MOD_DATA = list(sorted(LEVEL_MOD_DATA, key=lambda elem: elem["LEVEL"]))

# Job modifiers
JOB_DATA = {}
with open("ffxiv_allaganstudies_jobdata.csv", "r") as f:
    for line in f:
        if not line.startswith("#") and not line.isspace():
            s = line[:-1].split(",")
            JOB_DATA[s[0]] = {}
            JOB_DATA[s[0]]["JOB_ID"] = int(s[1])
            JOB_DATA[s[0]]["HP"] = int(s[2])
            JOB_DATA[s[0]]["STR"] = int(s[3])
            JOB_DATA[s[0]]["VIT"] = int(s[4])
            JOB_DATA[s[0]]["DEX"] = int(s[5])
            JOB_DATA[s[0]]["INT"] = int(s[6])
            JOB_DATA[s[0]]["MND"] = int(s[7])

# Clan stats
CLAN_STATS = {}
with open("ffxiv_allaganstudies_clandata.csv", "r") as f:
    for line in f:
        if not line.startswith("#") and not line.isspace():
            s = line[:-1].split(",")
            CLAN_STATS[s[0]] = {}
            CLAN_STATS[s[0]]["STR"] = int(s[1])
            CLAN_STATS[s[0]]["DEX"] = int(s[2])
            CLAN_STATS[s[0]]["VIT"] = int(s[3])
            CLAN_STATS[s[0]]["INT"] = int(s[4])
            CLAN_STATS[s[0]]["MND"] = int(s[5])

class CritType(Enum):
    Normal = 1
    Crit = 2
    ForcedCrit = 3
    Average = 4

class DHType(Enum):
    Normal = 1
    DirectHit = 2
    ForcedDirectHit = 3
    Average = 4

class DamageType(int, Enum):
    SLASHING = (0, True)
    PIERCING = (1, True)
    BLUNT = (2, True)
    MAGICAL = (3, False)
    SPECIAL = (4, False)
    def __new__(cls, value, is_physical):
        obj = int.__new__(cls, value)
        obj._value_ = value
        obj.is_physical = is_physical
        return obj

class DamageElement(Enum):
    NONE = 0
    FIRE = 1
    EARTH = 2
    ICE = 3
    WATER = 4
    WIND = 5
    LIGHTNING = 6

class ActionCategory(Enum):
    AUTO_ATTACK = (0, False)
    SPELL = (1, True)
    WEAPONSKILL = (2, True)
    ABILITY = (3, False)
    ITEM = (4, False)
    LIMIT_BREAK = (5, False)
    SYSTEM = (6, False)
    def __new__(cls, value, is_skill_or_spell):
        obj = object.__new__(cls)
        obj._value_ = value
        obj.is_skill_or_spell = is_skill_or_spell
        return obj

@dataclass
class WeaponInfo:
    damage: int = 100
    auto_attack: int = 100
    delay: int = 300

@dataclass
class PlayerStats:
    level: int = 90
    STR: int = LEVEL_MOD_DATA[level - 1]["MAIN"]
    VIT: int = LEVEL_MOD_DATA[level - 1]["MAIN"]
    DEX: int = LEVEL_MOD_DATA[level - 1]["MAIN"]
    INT: int = LEVEL_MOD_DATA[level - 1]["MAIN"]
    MND: int = LEVEL_MOD_DATA[level - 1]["MAIN"]
    DET: int = LEVEL_MOD_DATA[level - 1]["MAIN"]
    PIE: int = LEVEL_MOD_DATA[level - 1]["MAIN"]
    CRT: int = LEVEL_MOD_DATA[level - 1]["SUB"]
    DH: int = LEVEL_MOD_DATA[level - 1]["SUB"]
    SKS: int = LEVEL_MOD_DATA[level - 1]["SUB"]
    SPS: int = LEVEL_MOD_DATA[level - 1]["SUB"]
    TNC: int = LEVEL_MOD_DATA[level - 1]["SUB"]
    def speed(self, skilltype):
        if (skilltype is ActionCategory.WEAPONSKILL
            or skilltype is ActionCategory.AUTO_ATTACK):
            return self.SKS
        elif skilltype is ActionCategory.SPELL:
            return self.SPS
        else:
            return 0
    def set_stats_to_base(self, level):
        self.STR = LEVEL_MOD_DATA[level - 1]["MAIN"]
        self.VIT = LEVEL_MOD_DATA[level - 1]["MAIN"]
        self.DEX = LEVEL_MOD_DATA[level - 1]["MAIN"]
        self.INT = LEVEL_MOD_DATA[level - 1]["MAIN"]
        self.MND = LEVEL_MOD_DATA[level - 1]["MAIN"]
        self.DET = LEVEL_MOD_DATA[level - 1]["MAIN"]
        self.PIE = LEVEL_MOD_DATA[level - 1]["MAIN"]
        self.CRT = LEVEL_MOD_DATA[level - 1]["SUB"]
        self.DH = LEVEL_MOD_DATA[level - 1]["SUB"]
        self.SKS = LEVEL_MOD_DATA[level - 1]["SUB"]
        self.SPS = LEVEL_MOD_DATA[level - 1]["SUB"]
        self.TNC = LEVEL_MOD_DATA[level - 1]["SUB"]
    def get_stat_by_name(self, name):
        return self.__getattribute__(name)
    def copy(self):
        newstats = PlayerStats()
        newstats.STR = self.STR
        newstats.VIT = self.VIT
        newstats.DEX = self.DEX
        newstats.INT = self.INT
        newstats.MND = self.MND
        newstats.DET = self.DET
        newstats.PIE = self.PIE
        newstats.CRT = self.CRT
        newstats.DH = self.DH
        newstats.SKS = self.SKS
        newstats.SPS = self.SPS
        newstats.TNC = self.TNC
        return newstats

class Buff:
    def __init__(self, critbuff=0, dhbuff=0, damagebuff=0, statbuff=None):
        self.crit_chance_increase = critbuff
        self.dh_chance_increase = dhbuff
        self.damage_multiplier = damagebuff
        if statbuff is not None:
            self.apply_to_stats = statbuff

    def apply_to_stats(self, playerstats: PlayerStats):
        # The default is to do nothing.
        # Overwrite the method to have it do something for specific buffs
        pass

def is_tank(job):
    return (job == "GNB"
         or job == "PLD"
         or job == "WAR"
         or job == "DRK"
         or job == "GLA"
         or job == "MRD")

def is_healer(job):
    return (job == "CNJ"
         or job == "WHM"
         or job == "SCH"
         or job == "AST"
         or job == "SGE")

def is_caster(job):
    return (job == "THM"
         or job == "BLM"
         or job == "ACN"
         or job == "SMN"
         or job == "RDM"
         or job == "BLU")

def is_pranged(job):
    return (job == "ARC"
         or job == "BRD"
         or job == "MCH"
         or job == "DNC")

def is_melee(job):
    return (job == "LNC"
         or job == "PGL"
         or job == "ROG"
         or job == "DRG"
         or job == "MNK"
         or job == "NIN"
         or job == "SAM"
         or job == "RPR")

# Return the relevant physical attack stat
# DEX for NIN and the phys ranged, STR otherwise
def get_ap_stat(job):
    if (job == "ROG" or job == "NIN" or is_pranged(job)):
        return "DEX"
    else:
        return "STR"

# Return the relevant magical attack stat
# MND for healers, INT for casters
def get_map_stat(job):
    if is_healer(job):
        return "MND"
    else:
        return "INT"

# Return the relevant healing magic stat
# This is MND for healers and SMN (lol) and INT for others
def get_healing_stat(job):
    if is_healer(job) or job == "SMN":
        return "MND"
    else:
        return "INT"

# The base auto attack potency
# This is 80 for the non-DNC phys ranged, 90 otherwise
def get_aa_potency(job):
    if job == "ARC" or job == "BRD" or job == "MCH":
        return 80
    else:
        return 90

def fixed_random_variation():
    """ Returns an int between 9500 and 10500 inclusive. """
    return randint(9500, 10500)

# AKA p(crit)
def calc_critrate(crit_stat, level):
    sub = LEVEL_MOD_DATA[level - 1]["SUB"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    pcrit = floor(CRT_RATE_MOD * (crit_stat - sub)/div) + 50
    return pcrit / 1000

# AKA f(crit)
def calc_critmod(crit_stat, level):
    sub = LEVEL_MOD_DATA[level - 1]["SUB"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    fcrit = 1400 + floor(CRT_DMG_MOD * (crit_stat - sub)/div)
    return fcrit / 1000

# AKA p(DH)
def calc_dhrate(dh_stat, level):
    sub = LEVEL_MOD_DATA[level - 1]["SUB"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    pdh = floor(DH_MOD * (dh_stat - sub)/div)
    return pdh / 1000

# AKA f(DET)
def calc_detmod(det_stat, level):
    main = LEVEL_MOD_DATA[level - 1]["MAIN"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    fdet = floor(DET_MOD * (det_stat - main) / div) + 1000
    return fdet / 1000

# AKA f(SPD)
def calc_spdmod(spd_stat, level):
    sub = LEVEL_MOD_DATA[level - 1]["SUB"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    fspd = 1000 + floor(SPD_MOD * (spd_stat - sub)/div)
    return fspd / 1000

# AKA f(GCD)
# Note, input GCD in ms, i.e. 2.5s = 2500
def calc_gcdmod(spd_stat, gcd, level):
    sub = LEVEL_MOD_DATA[level - 1]["SUB"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    fgcd = floor(gcd * (1000 + ceil(130 * (sub - spd_stat)/div))/10000)/100
    return fgcd

# AKA f(TNC)
def calc_tenacitymod_dps(tnc_stat, level):
    sub = LEVEL_MOD_DATA[level - 1]["SUB"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    ftnc = 1000 + floor(TNC_MOD * (tnc_stat - sub)/div)
    return ftnc / 1000

# AKA f(TNC)
def calc_tenacitymod_mit(tnc_stat, level):
    sub = LEVEL_MOD_DATA[level - 1]["SUB"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    ftnc = 1000 - floor(100 * (tnc_stat - sub)/div)
    return ftnc / 1000

# AKA f(PIE)
# only affects MP regen now
def calc_piety_mp_regen(pie_stat, level):
    main = LEVEL_MOD_DATA[level - 1]["MAIN"]
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    fpie = floor(PIE_MOD * (pie_stat - main)/div)
    return fpie

# AKA f(DEF)
# returns the damage multiplier
def calc_defmod(def_stat, level):
    div = LEVEL_MOD_DATA[level - 1]["DIV"]
    fdef = 100 - floor(15 * (def_stat/div))
    return fdef / 100

# Weapon damage formula, f(WD)
# stat_used is the relevant attribute for the action,
# i.e. MND for Physick, STR for True Thrust, etc.
def calc_wepdamagemod(wd_stat, job, stat_used, level):
    main = LEVEL_MOD_DATA[level - 1]["MAIN"]
    attr = JOB_DATA[job][stat_used]
    fwd = floor((main * attr / 1000) + wd_stat)
    return fwd

# Attack Power: f(AP) and f(MAP), scaled by 100
# The ap_stat is job-dependent. STR for tanks and non-NIN melee,
# DEX for NIN and p.ranged, INT for casters and MND for healers.
# Note: the lower levels may be inaccurate for tanks. This is due to
# the level 1 trait "Tank Mastery", which applies a correction factor
# (not an increase!) to the coefficient of attack power.
# Only levels 80 and 90 have been verified to be correct.
def calc_atkpowermod(ap_stat, job, level):
    main = LEVEL_MOD_DATA[level - 1]["MAIN"]
    if is_tank(job):
        if level > 80:
            # Unconfirmed except level=80 and level=90
            # Returns linear scaled value between those
            mod = 115 + floor((level - 80)*41/10)
        elif level > 70:
            # Unconfirmed, returns level 80 value
            mod = 115
        elif level > 50:
            # Unconfirmed, should have a coefficient <1
            mod = 75
        else:
            # Unconfirmed, should have a coefficient <1
            mod = 75
    else:
        if level > 80:
            mod = 165 + floor((level - 80)*3)
        elif level > 70:
            mod = 125 + floor((level - 70)*4)
        elif level > 50:
            mod = 75 + floor((level - 50)*5 / 2)
        else:
            mod = 75
    fap = floor(mod * (ap_stat - main)/main) + 100
    return fap

# Auto attack modifier
# Similar to weapon damage f(WD) but includes weapon delay
def calc_aamod(wd_stat, weapon_delay, job, stat_used, level):
    main = LEVEL_MOD_DATA[level - 1]["MAIN"]
    attr = JOB_DATA[job][get_ap_stat(job)]
    fwd = floor((floor(main * attr / 1000) + wd_stat) * weapon_delay / 300)
    return fwd / 100

# Job trait modifier
def calc_jobtraitmod(job):
    if is_healer(job) or is_caster(job):
        return 130
    elif is_pranged(job):
        return 120
    else:
        return 100

# Apply buffs directly to player stats
# This would be things like the +5% full party buff, or potions
# Since I don't know exactly how they work, assume stat buffs are scaled
# by 1000 like most other things. So +20% int from a potion would be 200
def apply_stat_buffs(playerstats, buffs):
    buffedstats = playerstats.copy()
    for buff in buffs:
        buff.apply_to_stats(buffedstats)
    return buffedstats

# Apply buffs to crit chance (additive)
# Values scaled by 1000. I.e., a 5% increase to crit chance would be 50
def apply_critchance_buffs(base_chance, buffs):
    for buff in buffs:
        base_chance += buff.crit_chance_increase
    return base_chance

# Apply DH buffs (additive)
# Values scaled by 1000. I.e., a 5% increase to DH chance would be 50
def apply_dh_buffs(base_chance, buffs):
    for buff in buffs:
        base_chance += buff.dh_chance_increase
    return base_chance

# Apply damage buffs (multiplicative)
# Values scaled byy 1000. I.e., a 5% damage increase would be 50
def apply_damage_buffs(base_damage, buffs):
    new_damage = base_damage
    for buff in buffs:
        new_damage = floor(new_damage * (1000 + buff.damage_multiplier) / 1000)
    return new_damage

# Direct damage calculation for actions/spells/weaponskills
def calc_action_damage(potency: int,
                       job: str,
                       weaponinfo: WeaponInfo,
                       playerstats: PlayerStats,
                       buffs: list,
                       crittype: CritType = CritType.Normal,
                       dhtype: DHType = DHType.Normal,
                       randvar=None):
    """ Calculate damage dealt by a direct attack spell or weaponskill. """
    # Compute the buffed stats
    buffedstats = apply_stat_buffs(playerstats, buffs)
    # Get the relevant main stat for the attack
    if is_healer(job) or is_caster(job):
        mainstat = get_map_stat(job)
    else:
        mainstat = get_ap_stat(job)
    ap_stat = buffedstats.get_stat_by_name(mainstat)
    # Calculate the contribution from each stat
    fatk = calc_atkpowermod(ap_stat, job, playerstats.level)
    fdet = int(calc_detmod(buffedstats.DET, playerstats.level) * 1000)
    if dhtype is DHType.ForcedDirectHit:
        sub = LEVEL_MOD_DATA[buffedstats.level - 1]["SUB"]
        div = LEVEL_MOD_DATA[buffedstats.level - 1]["DIV"]
        fdet += floor(DET_MOD * (buffedstats.DH - sub)/div)
    if is_tank(job):
        ftnc = floor(1000 * calc_tenacitymod_dps(buffedstats.TNC, playerstats.level))
    else:
        ftnc = 1000
    fwd = calc_wepdamagemod(weaponinfo.damage, job, mainstat, playerstats.level)
    traitmod = calc_jobtraitmod(job)
    # Crit modifier based on crit type
    if crittype is CritType.Crit:
        critmod = 1000 * floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
    elif crittype is CritType.ForcedCrit:
        critmod = floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
        critchance = apply_critchance_buffs(0, buffs) # only buffs increase the base multiplier
        critmod *= 1000 + floor((critmod - 1000) * critchance / 1000)
    elif crittype is CritType.Average:
        critmod = floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
        critchance = floor(1000 * calc_critrate(buffedstats.CRT, playerstats.level))
        critchance = apply_critchance_buffs(critchance, buffs)
        critmod = 1000000 + floor((critmod - 1000) * critchance)
    else:
        critmod = 1000000
    # DH modifier based on DH type
    if dhtype is DHType.DirectHit:
        dhmod = 1250000
    elif dhtype is DHType.ForcedDirectHit:
        dhmod = 1250 * floor(1000 + 250 * apply_dh_buffs(0, buffs) / 1000)
    elif dhtype is DHType.Average:
        dhchance = floor(1000 * calc_dhrate(buffedstats.DH, playerstats.level))
        dhchance = apply_dh_buffs(dhchance, buffs)
        dhmod = 1000000 + floor(250 * dhchance)
    else:
        dhmod = 1000000
    if randvar is None:
        randvar = fixed_random_variation()
    # Pre-random components
    damage = floor(floor(floor(potency * fatk / 100) * fdet) / 1000)
    damage = floor(damage * ftnc / 1000)
    damage = floor(damage * fwd / 100)
    damage = floor(damage * traitmod / 100)
    # Now the random chance components
    damage = floor(damage * critmod / 1000000)
    damage = floor(damage * dhmod / 1000000)
    damage = floor(damage * randvar / 10000)
    # Apply buffs (These happen *after* the random variation!)
    # (But note they still increase overall variance, just not as much)
    damage = apply_damage_buffs(damage, buffs)
    return damage

def calc_dot_tick_damage(potency: int,
                         job: str,
                         weaponinfo: WeaponInfo,
                         playerstats: PlayerStats,
                         buffs: list,
                         crittype: CritType = CritType.Normal,
                         dhtype: DHType = DHType.Normal,
                         randvar=None):
    """ Calculate the damage of one DoT tick.
        Note that buffs are snapshot on application, but each tick
        rolls for crit, DH, and damage variance separately. """
    # Compute the buffed stats
    buffedstats = apply_stat_buffs(playerstats, buffs)
    # Get the relevant main stat for the attack
    if is_healer(job) or is_caster(job):
        mainstat = get_map_stat(job)
    else:
        mainstat = get_ap_stat(job)
    ap_stat = buffedstats.get_stat_by_name(mainstat)
    # Calculate the contribution from each stat
    fatk = calc_atkpowermod(ap_stat, job, playerstats.level)
    fdet = int(calc_detmod(buffedstats.DET, playerstats.level) * 1000)
    if dhtype is DHType.ForcedDirectHit:
        sub = LEVEL_MOD_DATA[buffedstats.level - 1]["SUB"]
        div = LEVEL_MOD_DATA[buffedstats.level - 1]["DIV"]
        fdet += floor(DET_MOD * (buffedstats.DH - sub)/div)
    # Select the skill vs spell speed to use.
    # afaik there's no job with DoTs that have both skill and spell speed?
    # So just choose based on job rather than based on a function argument
    # This may need to change if I think of an exception...
    if is_caster(job) or is_healer(job):
        actiontype = ActionCategory.SPELL
    else:
        actiontype = ActionCategory.WEAPONSKILL
    fspd = floor(1000 * calc_spdmod(buffedstats.speed(actiontype), playerstats.level))
    if is_tank(job):
        ftnc = floor(1000 * calc_tenacitymod_dps(buffedstats.TNC, playerstats.level))
    else:
        ftnc = 1000
    fwd = calc_wepdamagemod(weaponinfo.damage, job, mainstat, playerstats.level)
    traitmod = calc_jobtraitmod(job)
    # Crit modifier based on crit type
    if crittype is CritType.Crit:
        critmod = 1000 * floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
    elif crittype is CritType.ForcedCrit:
        critmod = floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
        critchance = apply_critchance_buffs(0, buffs) # only buffs increase the base multiplier
        critmod *= 1000 + floor((critmod - 1000) * critchance / 1000)
    elif crittype is CritType.Average:
        critmod = floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
        critchance = floor(1000 * calc_critrate(buffedstats.CRT, playerstats.level))
        critchance = apply_critchance_buffs(critchance, buffs)
        critmod = 1000000 + floor((critmod - 1000) * critchance)
    else:
        critmod = 1000000
    # DH modifier based on DH type
    if dhtype is DHType.DirectHit:
        dhmod = 1250000
    elif dhtype is DHType.ForcedDirectHit:
        dhmod = 1250 * floor(1000 + 250 * apply_dh_buffs(0, buffs) / 1000)
    elif dhtype is DHType.Average:
        dhchance = floor(1000 * calc_dhrate(buffedstats.DH, playerstats.level))
        dhchance = apply_dh_buffs(dhchance, buffs)
        dhmod = 1000000 + floor(250 * dhchance)
    else:
        dhmod = 1000000
    if randvar is None:
        randvar = fixed_random_variation()
    # Pre-random components
    if is_healer(job) or is_caster(job):
        damage = floor(potency * fwd / 100)
        damage = floor(damage * fatk / 100)
        damage = floor(damage * fspd / 1000)
        damage = floor(damage * fdet / 1000)
        damage = floor(damage * ftnc / 1000)
        damage = floor(damage * traitmod / 100)
        damage += int(potency < 100)
    else:
        damage = floor(potency * fatk / 100)
        damage = floor(damage * fdet / 1000)
        damage = floor(damage * ftnc / 1000)
        damage = floor(damage * fspd / 1000)
        damage = floor(damage * fwd / 100)
        damage = floor(damage * traitmod / 100)
        damage += int(potency < 100)
    # Random chance components
    damage = floor(damage * randvar / 10000)
    damage = floor(damage * critmod / 1000000)
    damage = floor(damage * dhmod / 1000000)
    # Apply damage buffs (these happen *after* the random variation)
    damage = apply_damage_buffs(damage, buffs)
    return damage

def calc_aa_damage(job: str,
                   weaponinfo: WeaponInfo,
                   playerstats: PlayerStats,
                   buffs: list,
                   crittype: CritType = CritType.Normal,
                   dhtype: DHType = DHType.Normal,
                   randvar=None):
    """ Calculate the potency of an auto-attack. """
    # Get the job-based potency
    potency = get_aa_potency(job)
    # Compute the buffed stats
    buffedstats = apply_stat_buffs(playerstats, buffs)
    # Get the relevant main stat for the attack
    if is_healer(job) or is_caster(job):
        mainstat = get_map_stat(job)
    else:
        mainstat = get_ap_stat(job)
    ap_stat = buffedstats.get_stat_by_name(mainstat)
    # Calculate the contribution from each stat
    fatk = calc_atkpowermod(ap_stat, job, playerstats.level)
    fdet = int(calc_detmod(buffedstats.DET, playerstats.level) * 1000)
    if dhtype is DHType.ForcedDirectHit:
        sub = LEVEL_MOD_DATA[buffedstats.level - 1]["SUB"]
        div = LEVEL_MOD_DATA[buffedstats.level - 1]["DIV"]
        fdet += floor(DET_MOD * (buffedstats.DH - sub)/div)
    if is_tank(job):
        ftnc = floor(1000 * calc_tenacitymod_dps(buffedstats.TNC, playerstats.level))
    else:
        ftnc = 1000
    fspd = calc_spdmod(buffedstats.SKS, playerstats.level) # autos always use SKS
    aa_mod = calc_aamod(weaponinfo.damage, weaponinfo.delay, job, mainstat, playerstats.level)
    traitmod = calc_jobtraitmod(job)
    # Crit modifier based on crit type
    if crittype is CritType.Crit:
        critmod = 1000 * floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
    elif crittype is CritType.ForcedCrit:
        critmod = floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
        critchance = apply_critchance_buffs(0, buffs) # only buffs increase the base multiplier
        critmod *= 1000 + floor((critmod - 1000) * critchance / 1000)
    elif crittype is CritType.Average:
        critmod = floor(1000 * calc_critmod(buffedstats.CRT, playerstats.level))
        critchance = floor(1000 * calc_critrate(buffedstats.CRT, playerstats.level))
        critchance = apply_critchance_buffs(critchance, buffs)
        critmod = 1000000 + floor((critmod - 1000) * critchance)
    else:
        critmod = 1000000
    # DH modifier based on DH type
    if dhtype is DHType.DirectHit:
        dhmod = 1250000
    elif dhtype is DHType.ForcedDirectHit:
        dhmod = 1250 * floor(1000 + 250 * apply_dh_buffs(0, buffs) / 1000)
    elif dhtype is DHType.Average:
        dhchance = floor(1000 * calc_dhrate(buffedstats.DH, playerstats.level))
        dhchance = apply_dh_buffs(dhchance, buffs)
        dhmod = 1000000 + floor(250 * dhchance)
    else:
        dhmod = 1000000
    if randvar is None:
        randvar = fixed_random_variation()
    # Pre-random components
    damage = floor(potency * fatk / 100)
    damage = floor(damage * fdet / 1000)
    damage = floor(damage * ftnc / 1000)
    damage = floor(damage * fspd / 1000)
    damage = floor(damage * aa_mod / 100)
    damage = floor(damage * traitmod / 100)
    damage += int(potency < 100)
    # Random chance components
    damage = floor(damage * critmod / 1000000)
    damage = floor(damage * dhmod / 1000000)
    damage = floor(damage * randvar / 10000)
    # Apply damage buffs (these happen *after* the random variation)
    damage = apply_damage_buffs(damage, buffs)
    return damage

#################################################################
# EXAMPLES AND TESTS                                            #
#################################################################

# Generate a sample of damage numbers for a given setup
# Determines whether each hit is a crit and/or dh individually
def generate_sample_hits(n: int,
                         potency: int,
                         job: str,
                         weaponinfo: WeaponInfo,
                         playerstats: PlayerStats,
                         buffs: list):
    hits = []
    buffedstats = apply_stat_buffs(playerstats, buffs)
    dhchance = floor(1000 * calc_dhrate(buffedstats.DH, playerstats.level))
    dhchance = apply_dh_buffs(dhchance, buffs)
    pdh = dhchance / 1000
    critchance = floor(1000 * calc_critrate(buffedstats.CRT, playerstats.level))
    critchance = apply_critchance_buffs(critchance, buffs)
    pcrit = critchance / 1000
    for i in range(n):
        if random() < pdh:
            isdh = DHType.DirectHit
        else:
            isdh = DHType.Normal
        if random() < pcrit:
            iscrit = CritType.Crit
        else:
            iscrit = CritType.Normal
        hits.append(calc_action_damage(potency,
                                       job,
                                       weaponinfo,
                                       playerstats,
                                       buffs,
                                       crittype=iscrit,
                                       dhtype=isdh))
    return hits

# Compendium of often-used buffs
class PartyBuffs:
    def __new__(cls):
        if not hasattr(cls, 'instance'):
            cls.instance = super(PartyBuffs, cls).__new__(cls)
        return cls.instance
    SearingLight = Buff(damagebuff=30)
    Embolden = Buff(damagebuff=50) # TODO: make this only applied to the source RDM's magic damage
    ChainStrategem = Buff(critbuff=100)
    AstCorrectCard = Buff(damagebuff=60)
    AstWrongCard = Buff(damagebuff=30)
    Divination = Buff(damagebuff=60)
    BattleLitany = Buff(critbuff=100)
    RightEye = Buff(damagebuff=100)
    LeftEye = Buff(damagebuff=50)
    LanceCharge = Buff(damagebuff=100)
    RiddleOfFire = Buff(damagebuff=150)
    Brotherhood = Buff(damagebuff=50)
    ArcaneCircle = Buff(damagebuff=30)
    SingleStandardFinish = Buff(damagebuff=20)
    DoubleStandardFinish = Buff(damagebuff=50)
    SingleTechnicalFinish = Buff(damagebuff=10)
    DoubleTechnicalFinish = Buff(damagebuff=20)
    TripleTechnicalFinish = Buff(damagebuff=30)
    QuadrupleTechnicalFinish = Buff(damagebuff=50)
    Devilment = Buff(critbuff=200, dhbuff=200)
    RagingStrikes = Buff(damagebuff=150)
    BattleVoice = Buff(dhbuff=200)
    MagesBallad = Buff(damagebuff=10)
    ArmysPaean = Buff(dhbuff=30)
    WanderersMinuet = Buff(critbuff=20)
    RadiantFinaleOne = Buff(damagebuff=20)
    RadiantFinaleTwo = Buff(damagebuff=40)
    RadiantFinaleThree = Buff(damagebuff=60)
    FightOrFlight = Buff(damagebuff=250)
    NoMercy = Buff(damagebuff=200)

# Generate an example player for a few different roles and levels
def get_example_playerstats_level90_sch():
    playerstats = PlayerStats()
    playerstats.MND = 3375
    playerstats.VIT = 3320
    playerstats.CRT = 2395
    playerstats.DET = 2076
    playerstats.DH = 580
    playerstats.SPS = 892
    playerstats.PIE = 607
    return playerstats

def get_example_playerstats_level90_blm():
    playerstats = PlayerStats()
    playerstats.INT = 3371
    playerstats.VIT = 3318
    playerstats.CRT = 2430
    playerstats.DET = 1174
    playerstats.DH = 1150
    playerstats.SPS = 1309
    return playerstats

def get_example_playerstats_level90_gnb():
    playerstats = PlayerStats()
    playerstats.STR = 3197
    playerstats.VIT = 3534
    playerstats.CRT = 2271
    playerstats.DET = 1921
    playerstats.DH = 400
    playerstats.SKS = 472
    playerstats.TNC = 725
    return playerstats

def get_example_weaponstats_level90():
    wepinfo = WeaponInfo()
    wepinfo.damage = 132
    wepinfo.auto_attack = 137
    wepinfo.delay = 312
    return wepinfo

def get_example_weaponstats_level80():
    wepinfo = WeaponInfo()
    wepinfo.damage = 100
    wepinfo.auto_attack = 120
    wepinfo.delay = 300
    return wepinfo

def get_example_playerstats_level80_sch():
    playerstats = PlayerStats()
    playerstats.level = 80
    playerstats.INT = 1707
    playerstats.VIT = 1694
    playerstats.CRT = 1380
    playerstats.DET = 1469
    playerstats.DH = 564
    playerstats.SPS = 756
    playerstats.PIE = 700
    return playerstats

def get_example_playerstats_level80_blm():
    playerstats = PlayerStats()
    playerstats.level = 80
    playerstats.INT = 1700
    playerstats.VIT = 1663
    playerstats.CRT = 1778
    playerstats.DET = 925
    playerstats.DH = 730
    playerstats.SPS = 1070
    return playerstats

def get_example_playerstats_level80_drg():
    playerstats = PlayerStats()
    playerstats.level = 80
    playerstats.STR = 1704
    playerstats.VIT = 1814
    playerstats.CRT = 1732
    playerstats.DET = 1241
    playerstats.DH = 1151
    playerstats.SKS = 380
    return playerstats

if __name__ == "__main__":
    # Only execute the following if we're running this as a script
    import numpy as np

    def make_damage_sample_histogram(potency: int,
                                     job: str,
                                     weaponinfo: WeaponInfo,
                                     playerstats: PlayerStats,
                                     buffs: list):
        """ Create a histogram using matplotlib of a damage sample """
        hits = generate_sample_hits(100000, potency, job, weaponinfo, playerstats, buffs)
        counts, bins = np.histogram(hits, bins=40)
        return counts, bins

    def multi_hit_damage_sample(n: int,
                                hit_potencies: list,
                                job: str,
                                weaponinfo: WeaponInfo,
                                playerstats: PlayerStats,
                                buffs: list):
        """ Generate a list of damage values for the given set of attacks. """
        hits = []
        buffedstats = apply_stat_buffs(playerstats, buffs)
        dhchance = floor(1000 * calc_dhrate(buffedstats.DH, playerstats.level))
        dhchance = apply_dh_buffs(dhchance, buffs)
        pdh = dhchance / 1000
        critchance = floor(1000 * calc_critrate(buffedstats.CRT, playerstats.level))
        critchance = apply_critchance_buffs(critchance, buffs)
        pcrit = critchance / 1000
        for i in range(n):
            hit = 0
            for potency in hit_potencies:
                if random() < pdh:
                    isdh = DHType.DirectHit
                else:
                    isdh = DHType.Normal
                if random() < pcrit:
                    iscrit = CritType.Crit
                else:
                    iscrit = CritType.Normal
                hit += (calc_action_damage(potency,
                                               job,
                                               weaponinfo,
                                               playerstats,
                                               buffs,
                                               crittype=iscrit,
                                               dhtype=isdh))
            hits.append(hit)
        return hits


