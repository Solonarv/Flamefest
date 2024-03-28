# Flamefest

A Rift Wizard mod full of extra fire options, because there clearly aren't enough of those yet ;)

## Installing

This mod requires [AAA_Loader](https://github.com/DaedalusGame/AAA_Loader). Install that first.

Download a zip from the [Releases](https://github.com/Solonarv/Flamefest/releases) page and unzip it as a directory in Rift Wizard's `mods` folder.

You should end up with a folder structure like this:
```
mods/
    AAA_Loader/
        AAA_Loader.py
    Flamefest/
        Flamefest.py
```

## Content

### Spells

#### Flame Wave

> Unleash a slow-moving wave of fire that deals 23 fire damage to units in a 12 tile cone. Max 1 flamewave at a time.

- 3 SP: +4 range
- 3 SP: +17 damage
- 4 SP: Firestorm - The wave leaves damaging firestorms behind.

Wave is two tiles thick and moves 1 tile per turn. Firestorms are created in the 'back' half of the wave, and deal
damage equal to half the wave's spell damage stat.

#### Flame Wave End

> End an ongoing Flame Wave spell.

### Skills

#### Ash Beast

> You are the Ash Beast.
> 
> Immune to firestorms and ash clouds.
> 
> Each turn, spawn a firestorm and an ash cloud nearby.

Firestorms are clouds that deal 6 fire damage each turn. Ash clouds deal 2 dark damage each turn, and have
a 50% chance to blind units within for 1 turn.