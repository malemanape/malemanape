"""dodge.exe's pixel art, ported as is from the portfolio (src/scripts/dodge-sprites.ts): one character per
pixel, drawn in four shades: w lightest, l light, m mid, # darkest (the cyan ramp; the dark theme flips it).
El faces right; the bugs face left, toward him. Keep the two in step: change a sprite there, change it here."""
from __future__ import annotations

# El: headphones (h band and cup, b the cup's shine), o his eye
EL_TOP = [
    "....#..#....",
    "....##.##.#.",
    "...hhhhhh##.",
    "..h#######..",
    "..hbh###o##.",
    "..hhh###o##.",
    "..hhh######.",
    "...#######..",
    ".....###....",
    "....#####...",
    "...#######..",
    "...######.#.",
    "...#####....",
    "....####....",
]
# legs: two running frames, then tucked for a jump
EL_LEGS = [
    ["...##..##...", "..##....##..", "..#......#..", ".##......##."],
    ["....####....", ".....##.....", ".....##.....", "....###....."],
    ["...######...", "...##..##...", "....#...#...", "............"],
]
# the cape, flowing back from his shoulders: two running frames, then streaming up for a jump
CAPE = [
    [".......c", ".....ccc", "...ccccc", ".cccccc.", "ccccccc.", ".ccccc..", "...cc..."],
    [".......c", "......cc", "....cccc", "..ccccc.", ".cccccc.", "cccccc..", ".cc.cc.."],
    ["cccc....", ".ccccc.c", "...ccccc", ".....ccc", "........", "........", "........"],
]

WALKERS = ["ladybug", "caterpillar", "slime", "snail"]
# w, h: size in pixels; lift: how far off the ground (moth low, fly just over his head); label: drawn on it
BUGS = {
    "ladybug": {"w": 15, "h": 11, "lift": 0, "frames": [
        ["......#####....", "....##mmmmm##..", "...#mlmm#mmmm#.", "..##llmmmmm#mm#", ".#ww#mm#mmmmmm#", "#www#mmmmmm#mm#", "#w#w#mm#mmmmmm#", "#####mmmmm#mmm#", ".##############", "..#..#...#..#..", ".#..#...#..#..."],
        ["......#####....", "....##mmmmm##..", "...#mlmm#mmmm#.", "..##llmmmmm#mm#", ".#ww#mm#mmmmmm#", "#www#mmmmmm#mm#", "#w#w#mm#mmmmmm#", "#####mmmmm#mmm#", ".##############", "..#..#...#..#..", "...#..#...#..#."],
    ]},
    "caterpillar": {"w": 34, "h": 10, "lift": 0},
    "slime": {"w": 15, "h": 11, "lift": 0, "label": "ERR", "frames": [
        ["....#######....", "..##mmmmmmm##..", ".#mmwwmmmwwmm#.", ".#mmw#mmmw#mm#.", "#mmmmmmmmmmmmm#", "#mmmmmmmmmmmmm#", "#mmmmmmmmmmmmm#", "#mmmmmmmmmmmmm#", "#mmmmmmmmmmmmm#", "#lmmmmmmmmmmml#", ".#############."],
        ["...............", "...#########...", ".##mwwmmmwwm##.", "#mmmw#mmmw#mmm#", "#mmmmmmmmmmmmm#", "#mmmmmmmmmmmmm#", "#mmmmmmmmmmmmm#", "#mmmmmmmmmmmmm#", "#mmmmmmmmmmmmm#", "#lmmmmmmmmmmml#", "###############"],
    ]},
    "snail": {"w": 18, "h": 13, "lift": 0},
    "moth": {"w": 15, "h": 10, "lift": 6, "frames": [
        [".##.........##.", "#ll#..#.#..#ll#", "#lll#..#..#lll#", "#llml#.#.#lmll#", "#lmmll###llmml#", "#lllll#w#lllll#", ".#llll###llll#.", "..#lll###lll#..", "...###.#.###...", ".......#......."],
        ["...............", "......#.#......", "...##..#..##...", "..#ll#.#.#ll#..", "..#lml###lml#..", "..#lll#w#lll#..", "...#ll###ll#...", "....##.#.##....", ".......#.......", "..............."],
    ]},
    "fly": {"w": 13, "h": 9, "lift": 21, "frames": [
        [".....mmm.mmm.", "....m...m...m", ".....mmm.mmm.", "...#######...", "..#ww#####m#.", ".#www######m#", ".#w#######mm#", "..#########..", "...#.#.#.#..."],
        [".............", ".............", ".....mmmmmm..", "...#######mmm", "..#ww#####mm.", ".#www######m#", ".#w#######mm#", "..#########..", "..#.#.#.#...."],
    ]},
}

CATERPILLAR_HEAD = [
    ".#...#...",
    "..#.#....",
    "..####...",
    ".#mmmm#..",
    "#wwmmmm#.",
    "#w#mmmm#.",
    "#mmmmmm#.",
    "#m##mmm#.",
    ".#mmmm#..",
    "..####...",
]
CATERPILLAR_SEG = [
    "...###...",
    ".##lll##.",
    ".#lllll#.",
    "#lllllll#",
    "#lllllll#",
    "#lllllll#",
    ".#lllll#.",
    ".##lll##.",
    "...###...",
]
SNAIL_BODY = [
    ".w..w.............",
    "#w#.#w#...........",
    ".#...#............",
    ".#...#............",
    "..#.#.............",
    "..###.............",
    ".#mmm#............",
    "#mwmmm#...........",
    "#m#mmmm#..........",
    "#mmmmmmmmmmmmmmmm#",
    "#mmmmmmmmmmmmmmmmm",
    "#lmmmmmmmmmmmmmmm#",
    ".#################",
]
SNAIL_SHELL = [
    "...#####...",
    "..#lllll#..",
    ".#lllllll#.",
    "#lllllllll#",
    "#lllllllll#",
    "#lllllllll#",
    "#lllllllll#",
    "#lllllllll#",
    ".#lllllll#.",
    "..#lllll#..",
    "...#####...",
]

# a 3x5 pixel font: just the letters the screen says
FONT = {
    "0": "111101101101111", "1": "010110010010111", "2": "110001010100111", "3": "110001010001110", "4": "101101111001001", "5": "111100110001110",
    "6": "011100111101111", "7": "111001010010010", "8": "111101111101111", "9": "111101111001110", "A": "010101111101101", "B": "110101110101110",
    "C": "011100100100011", "D": "110101101101110", "E": "111100110100111", "F": "111100110100100", "G": "011100101101011", "H": "101101111101101",
    "I": "111010010010111", "J": "001001001101010", "K": "101101110101101", "L": "100100100100111", "M": "101111111101101", "N": "110101101101101",
    "O": "010101101101010", "P": "110101110100100", "R": "110101110101101", "S": "011100010001110", "T": "111010010010010", "U": "101101101101111",
    "V": "101101101101010", "W": "101101111111101", "Y": "101101010010010", "!": "010010010000010", " ": "000000000000000",
}
