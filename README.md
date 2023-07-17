Python Tkinter Minesweeper
===========================

Minesweeper game written in Python using Tkinter GUI library.

This fork adds a probabilistic AI solver using recursive backtracking.

<img src="https://i.imgur.com/8JwCyAQ.png" alt="Screenshot on OSX" height="350"/>

Contents:
----------

- */minesweeper.py* - The actual python program with the solver
- */images/* - GIF Images ready for usage with Tkinter
- */images/original* - Original PNG images made with GraphicsGale

Solver:
----------

Solver works with two initial rules followed by the probabilistic AI:

- Rule A: If a tile has the same number of adjacent mines as the number of unclicked tiles adjacent to it, then all of those tiles are mines.
- Rule B: If a tile has the same number of adjacent squares that are flags, all of those tiles are safe.

The probabilistic AI is as follows: 

1. Find all exposed tiles.
2. Find all bordered tiles.
3. Generate all valid arrangements of mines in the bordered tiles.
4. Get the number of mines in each arrangement
5. Subtract the number of mines in a given arrangement from the total number of mines, then 
   perform a calculation where we choose the number of mines left from the 
   unbordered tiles. This is the total number of combinations where the mines are present
   in the given arrangement
6. Repeat for all arrangements.
7. Assign each cell the number of times it was determined as a mine
8. Divide each number in the cell by the total number of arrangements, which is about 2.7 x 10^102
9. Multiply result by 100 to get the probability of that cell being a mine.
10. Flag all cells with probability of 100, then click on the cell with the lowest probability.
