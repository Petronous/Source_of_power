# Source_of_power
Simple tabletop style turn-based strategy game. (**!Heavy WIP!**)

(AI does not exist yet so you'll have to play local multiplayer with other humans or with yourself)

Conquer your assigned region by seizing all sources of materials for your overlords!

The game features three unique unit types made to counter each other naturally:
- Tank: High hp, good for seizing bases and defending the artillery
- Artillery: Low hp, but two tiles of range so it can destroy enemies from afar
- Infantry: Low hp, but double movement speed and dropoff ability to let it sneak behind enemy lines and destroy weaker targets



Pyglet is needed to run the game (`pip install pyglet` in the console/terminal)  
The "packages" folder only contains my own scripts for the base program.
 

I may make a proper documentation if any interest is expressed


Illustrative screenshot:
![Three player game where the purple one almost lost](assets/Screenshot.png)


#### Quick manual:
Main map settings (only side lengths and win/lose conditions) are currently always defined at around line 300 (starting with `Map = MapHex( `).

The map can be navigated by dragging with the mouse wheel (press and hold). You can zoom in and out by rotating the mouse wheel.

You can modify your map in setup phase (turn 0) by pressing **u** for **upgrade**, **p** for **player's starting base** or **s** for **source** (currently looks like a village) to set the tile feature that you want to place and then left-click on a tile to place it. Tile features can be removed with right-clicking.

Placing/removing a starting base will automatically create/delete a player. You can use that to make a new color for yourself if you don't like it.
