from Level import *
from Spells import *
from Upgrades import *
from CommonContent import *
import random

class Flamewave(Spell):

    def on_init(self):
        self.name = "Flame Wave"
        self.tags = [Tags.Sorcery, Tags.Fire]
        self.level = 4
        self.damage = 23
        self.max_charges = 9
        self.range = 12
        self.angle = math.pi / 4.0
        self.element = Tags.Fire
        self.can_target_self = False
        self.requires_los = False
        self.melt_walls = 0

        self.upgrades['range'] = (4, 3)
        self.upgrades['damage'] = (17, 3)
        self.upgrades['firestorm'] = (1, 4, "Firestorm", "The wave leaves damaging firestorms behind")
        #self.firestorm = 1 # just for testing

    def get_description(self):
        return "Unleash a slow-moving wave of fire that deals [{damage}:damage] [fire] damage to units in a [{range}_tile:range] cone. Max 1 flamewave at a time.".format(**self.fmt_dict())
    
    def aoe(self, target):
        origin = get_cast_point(self.caster.x, self.caster.y, target.x, target.y)
        return Burst(self.caster.level, 
                     Point(self.caster.x, self.caster.y), 
                     self.get_stat('range'), 
                     burst_cone_params=BurstConeParams(target, self.angle), 
                     ignore_walls=self.get_stat('melt_walls'))
    
    def cast(self, x, y):
        self.caster.apply_buff(FlamewaveBuff(self, x, y))
        yield

    def get_impacted_tiles(self, x, y):
        return [p for stage in self.aoe(Point(x,y)) for p in stage]

class FlamewaveEnd(Spell):
    
    def on_init(self):
        self.name = "Flame Wave End"
        # Not a "real" spell - no level, no tags
        # self.level = 1
        # self.tags = [Tags.Fire]
        self.can_target_self=True
        self.range = 0

    def get_description(self):
        return "End an ongoing Flame Wave spell."

    def cast_instant(self, x, y):
        self.caster.remove_buffs(FlamewaveBuff)

class FlamewaveBuff(Buff):
    def __init__(self, spell, x, y):
        Buff.__init__(self)
        self.spell = spell
        self.name = spell.name
        self.target = Point(x, y)
        self.stages = list(spell.aoe(self.target))
        self.cur_stage = -1

        self.color = Tags.Fire.color
        self.buff_type = BUFF_TYPE_NONE
        self.stack_type = STACK_REPLACE
        self.last_stage = None

        self.damage = spell.get_stat('damage')
        self.element = spell.element
        self.firestorm = spell.get_stat('firestorm')

        self.spells = [FlamewaveEnd()]
    
    def on_advance(self):
        self.do_blast(True)
        self.cur_stage += 1
        self.do_blast()

    def do_blast(self, is_last=False):
        if self.cur_stage < 0:
            return
        if self.cur_stage >= len(self.stages):
            self.owner.remove_buff(self)
            return
        for point in self.stages[self.cur_stage]:
            self.owner.level.deal_damage(point.x, point.y, self.spell.get_stat('damage'), self.spell.element, self)
            if self.firestorm and is_last:
                self.owner.level.add_obj(FireCloud(self.owner, self.damage//2), point.x, point.y)


        
class FireCloudPatch:
    def __init__(self, owner, damage=6):
        Cloud.__init__(self)
        self.owner = owner
        self.duration = 4
        self.damage = damage
        self.color = Tags.Fire.color
        self.strikechance = 1
        self.name = "Firestorm"
        self.description = "Every turn, deals [%d_fire:fire] damage to any creature standing within." % self.damage
        self.asset_name = 'fire_cloud'
        self.source = None
    
    def on_advance(self):
        unit = self.level.get_unit_at(self.x, self.y)
        if unit and AshBeast.is_ash_beast(unit):
            return
        self.level.deal_damage(self.x, self.y, self.damage, Tags.Fire, self.source or self)

    FireCloud.__init__ = __init__
    _old_on_advance = FireCloud.on_advance



class AshCloud(Cloud):
    def __init__(self, owner, damage=2):
        Cloud.__init__(self)
        self.owner = owner
        self.duration = 4
        self.damage = damage
        self.color = Tags.Dark.color
        self.strikechance = 0.5
        self.name = "Ash Cloud"
        self.description = ("Every turn, deals [%d_dark:dark] damage to any creature standing within"
                    "and has a %d%% chance of blinding it for 1 turn" % (self.damage, int(100*self.strikechance)))
        self.source = None
        self.asset_name = 'fire_cloud' # TODO fix asset
    
    def on_advance(self):
        unit = self.level.get_unit_at(self.x, self.y)
        if unit and AshBeast.is_ash_beast(unit):
            return
        self.level.deal_damage(self.x, self.y, self.damage, Tags.Dark, self.source or self)
        if unit:
            if random.random() > self.strikechance:
                unit.apply_buff(BlindBuff(), 1)


class AshBeast(Upgrade):
    def on_init(self):
        self.name = "Ash Beast"
        self.tags = [Tags.Dark, Tags.Fire]
        self.level = 5
        self.global_bonuses['ash_beast'] = 1
    
    def get_description(self):
        return ("You are the Ash Beast.\n"
            "Immune to firestorms and ash clouds.\n"
            "Each turn, spawn a firestorm and an ash cloud nearby.")
    
    def on_advance(self):
        if not any(are_hostile(self.owner, u) for u in self.owner.level.units):
            return
        candidates = [Point(x + self.owner.x, y + self.owner.y)
            for x in [-1, 0, 1]
            for y in [-1, 0, 1]
            if (x != 0 or y != 0)
                and self.owner.level.can_walk(x + self.owner.x, y + self.owner.y)]
        candidates = random.sample(candidates, 2)
        clouds = [AshCloud(self.owner), FireCloud(self.owner)]
        random.shuffle(clouds)
        for point, cloud in zip(candidates, clouds):
            cloud.source = self
            self.owner.level.add_obj(cloud, point.x, point.y)
    
    @classmethod
    def is_ash_beast(cls, unit):
        if unit.get_stat('ash_beast'):
            return True
        return unit.resists[Tags.Dark] >= 100 and unit.resists[Tags.Fire] >= 100
        


all_player_spell_constructors.extend([Flamewave])
skill_constructors.extend([AshBeast])