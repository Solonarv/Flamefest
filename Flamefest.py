from Level import *
from Spells import *
from Upgrades import *
from CommonContent import *
import random

class Flamewave(Spell):

    def on_init(self):
        self.name = "Pyroclasm"
        self.tags = [Tags.Sorcery, Tags.Fire]
        self.level = 4
        self.damage = 23
        self.max_charges = 6
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
        return ("Unleash a slow-moving wave of fire that deals [{damage}:damage] [fire] damage to units in a [{range}_tile:range] cone. Max 1 pyroclasm at a time."
                ).format(**self.fmt_dict())
    
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
        self.name = "Pyroclasm End"
        # Not a "real" spell - no level, no tags
        # self.level = 1
        # self.tags = [Tags.Fire]
        self.can_target_self=True
        self.range = 0

    def get_description(self):
        return "End an ongoing Pyroclasm spell."

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


class ForgeStrike(Spell):
    def on_init(self):
        self.name = "Forge Strike"
        self.level = 2
        self.tags = [Tags.Sorcery, Tags.Metallic, Tags.Fire]
        self.max_charges = 16
        self.range = 1
        self.melee = True
        self.damage = 18
        self.radius = 5
        self.angle = math.pi / 6.0
        self.can_target_self = False
    
    def get_description(self):
        return ("Slam down a hammer strike onto the target tile dealing [{damage}_physical:physical] damage.\n"
                "Then a wave of forge fire washes out, burning all units in a [{radius}_tile:radius] cone for [{damage}_fire:fire] damage."
                ).format(**self.fmt_dict())
    
    def aoe(self, x, y):
        return Burst(self.caster.level, 
                     Point(self.caster.x, self.caster.y), 
                     self.get_stat('radius'), 
                     burst_cone_params=BurstConeParams(Point(x, y), self.angle), 
                     ignore_walls=self.get_stat('melt_walls'))
    
    def cast(self, x, y):
        self.owner.level.deal_damage(x, y, self.get_stat('damage'), Tags.Physical, self)
        yield

        for stage in self.aoe(x, y):
            for point in stage:
                self.owner.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Fire, self)
            yield

    def get_impacted_tiles(self, x, y):
        return [p for stage in self.aoe(x,y) for p in stage]


class ConjureBlade(Spell):
    def on_init(self):
        self.name = "Conjure Blade"
        self.level = 3
        self.tags = [Tags.Conjuration, Tags.Metallic]
        self.max_charges = 3
        self.duration = 12
        self.range = 0
        self.radius = 5
        self.damage = 29
        self.can_target_self = True

        self.active = False
    
    def get_description(self):
        return ("Conjure a magic greatsword that you can swing in great arcs dealing [{damage}_physical:physical] damage.\n"
                "The sword lasts for [{duration}_turns:duration]"
                ).format(**self.fmt_dict())
    
    def cast_instant(self, x, y):
        self.caster.apply_buff(ConjureBladeBuff(self), self.get_stat('duration'))

class ConjureBladeBuff(Buff):
    def __init__(self, spell):
        Buff.__init__(self)
        self.spell = spell
        self.name = spell.name

        self.color = Tags.Metallic.color
        self.buff_type = BUFF_TYPE_NONE
        self.stack_type = STACK_REPLACE

        # self.spells = [ConjureBladeSwing()] # have to do this manually
    
    def on_applied(self, owner):
        if self.spell not in owner.spells:
            return
        owner.add_spell(ConjureBladeSwing(self.spell))

class ConjureBladeSwing(Spell):
    own_stats = set(["max_charges", "range"])

    def __init__(self, parent):
        self.parent = parent
        super().__init__()
    
    def on_init(self):
        self.name = "Great Cleave"
        self.level = self.parent.level
        self.tags = self.parent.tags
        self.angle = math.pi / 3
    
    def get_stat(self, stat, base=None):
        if stat in ConjureBladeSwing.own_stats:
            return super().get_stat(stat, base)
        else:
            return self.parent.get_stat(stat, base)
    
    def aoe(self, x, y):
        origin = Point(self.owner.x, self.owner.y)
        dist = self.get_stat('radius')
        step_size = 0.4 / dist
        midline = get_line_angle(...) # TODO
        angle = midline - self.angle
        already_hit = set()
        while angle < midline + self.angle:
            dx = cos(angle)
            dy = sin(angle)
            r = 1
            stage = []
            last_p = None
            while r <= dist:
                p = Point(dx*r, dy*r)
                if not self.owner.level.can_walk(p.x, p.y):
                    break
                if p != last_p and p not in already_hit:
                    already_hit.insert(p)
                    stage.append(p)
            if stage:
                yield stage
            angle += step_size

    def cast(self, x, y):
        for stage in self.aoe(x, y):
            for point in stage:
                self.owner.level.deal_damage(point.x, point.y, self.get_stat('damage'), Tags.Physical, self)
            yield
        

        
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
        if unit.has_buff(AshBeast):
            return True
        return unit.resists[Tags.Dark] >= 100 and unit.resists[Tags.Fire] >= 100
        


all_player_spell_constructors.extend([Flamewave, ForgeStrike, ConjureBlade])
skill_constructors.extend([AshBeast])