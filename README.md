# Freecell

This implements the game of Freecell in Python3. It is a scrolling command line program. It allows players to input moves and prints the board out after every move. It was done as a programming exercise.

```
$ ./freecell-game.py 

*** Game #1 ***

a  b  c  d  ♣  ♦  ♥  ♠    
J♦ 2♦ 9♥ J♣ 5♦ 7♥ 7♣ 5♥   
K♦ K♣ 9♠ 5♠ A♦ Q♣ K♥ 3♥   
2♠ K♠ 9♦ Q♦ J♠ A♠ A♥ 3♣   
4♣ 5♣ T♠ Q♥ 4♥ A♣ 4♦ 7♠   
3♠ T♦ 4♠ T♥ 8♥ 2♣ J♥ 7♦   
6♦ 8♠ 8♦ Q♠ 6♣ 3♦ 8♣ T♣   
6♠ 9♣ 2♥ 6♥               
1  2  3  4  5  6  7  8    

Here is the help sheet:

$ ./freecell-game.py --help

usage: ./freecell-game.py [options]

Generate MS compatible Freecell deals and play them.

    Options:
       -f or --freecells n - set number of freecells (0-25 default: 4)
       -c or --cascades n - set number of cascades (1-35 default: 8)
       -p or --play-back n - play back game number n (e.g. 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 21, 63, 68, 76, 86, 92, 96, 110, 123, 169)
       -P - play back all available solved games in moves file.
       -g or --game n - play game n (default: 1)
       -F or --file <file> - take input from a file (default: keyboard)
       -i or --ignore-dependencies - make the auto-mover ignore dependencies on other cards on the board
       -A or --available-moves - show possible moves before waiting for user input
       -M or --moves-file - load moves from given file (default "fixed_moves.txt")
       -t or --tty - use tty printer (default line printer)
       --no-automoves - turn off automover
       -h or --help - print this help sheet
    Try e.g. "./freecell-game.py -p 1" to run with a builtin game

Game features:

 o Plays a standard MS freecell game, using the standard 2 character move syntax:
     <source><destination> where source is "1-9", "a-d" and destination adds "h" for home.
 o The character '#' when used as a destination indicates the first available freecell.
 o Use the single character "u" to undo a move and "r" to redo a previously undone move. Use "q" to quit the game.
 o The game logs all user moves to the file "moves.log". These can be played back with the
   option "-F moves.log".
```
