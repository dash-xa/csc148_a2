"""CSC148 Assignment 2

=== CSC148 Winter 2020 ===
Department of Computer Science,
University of Toronto

This code is provided solely for the personal and private use of
students taking the CSC148 course at the University of Toronto.
Copying for purposes other than this use is expressly prohibited.
All forms of distribution of this code, whether as given or with
any changes, are expressly prohibited.

Authors: Diane Horton, David Liu, Mario Badr, Sophia Huynh, Misha Schwartz,
and Jaisie Sin

All of the files in this directory and all subdirectories are:
Copyright (c) Diane Horton, David Liu, Mario Badr, Sophia Huynh,
Misha Schwartz, and Jaisie Sin.

=== Module Description ===

This file contains the hierarchy of player classes.
"""
from __future__ import annotations
from typing import List, Optional, Tuple
import random
import pygame

from block import Block
from goal import Goal, generate_goals

from actions import KEY_ACTION, ROTATE_CLOCKWISE, ROTATE_COUNTER_CLOCKWISE, \
    SWAP_HORIZONTAL, SWAP_VERTICAL, SMASH, PASS, PAINT, COMBINE


def create_players(num_human: int, num_random: int, smart_players: List[int]) \
        -> List[Player]:
    """Return a new list of Player objects.

    <num_human> is the number of human player, <num_random> is the number of
    random players, and <smart_players> is a list of difficulty levels for each
    SmartPlayer that is to be created.

    The list should contain <num_human> HumanPlayer objects first, then
    <num_random> RandomPlayer objects, then the same number of SmartPlayer
    objects as the length of <smart_players>. The difficulty levels in
    <smart_players> should be applied to each SmartPlayer object, in order.
    """
    n = num_human + num_random + len(smart_players)
    goals = generate_goals(n)
    offset_smarts = num_human + num_random
    humans = [HumanPlayer(i, goals[i]) for i in range(num_human)]
    rands = [RandomPlayer(i, goals[i]) for i in range(num_human, offset_smarts)]
    smarts = [SmartPlayer(i, goals[i], smart_players[i - offset_smarts]) for i
              in range(offset_smarts, n)]
    return humans + rands + smarts


def _get_block(block: Block, location: Tuple[int, int], level: int) -> \
        Optional[Block]:
    """Return the Block within <block> that is at <level> and includes
    <location>. <location> is a coordinate-pair (x, y).

    A block includes all locations that are strictly inside of it, as well as
    locations on the top and left edges. A block does not include locations that
    are on the bottom or right edge.

    If a Block includes <location>, then so do its ancestors. <level> specifies
    which of these blocks to return. If <level> is greater than the level of
    the deepest block that includes <location>, then return that deepest block.

    If no Block can be found at <location>, return None.

    Preconditions:
        - 0 <= level <= max_depth
    """
    # base case: unit block or a level block
    if not block.children or block.level == level:
        if _in_range(location, block):
            return block
        else:
            return None
    else:
        for child in block.children:
            if _in_range(location, child):
                return _get_block(child, location, level)


def _in_range(pos: Tuple[int, int], block: Block) -> bool:
    """Returns whether <pos>=(x,y) is in this block."""
    x, y = pos
    b_pos_x, b_pos_y = block.position
    b_pos_x_max = b_pos_x + block.size
    b_pos_y_max = b_pos_y + block.size
    return (b_pos_x <= x < b_pos_x_max) and (b_pos_y <= y < b_pos_y_max)


class Player:
    """A player in the Blocky game.

    This is an abstract class. Only child classes should be instantiated.

    === Public Attributes ===
    id:
        This player's number.
    goal:
        This player's assigned goal for the game.
    """
    id: int
    goal: Goal

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this Player.
        """
        self.goal = goal
        self.id = player_id

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player.

        If no block is selected by the player, return None.
        """
        raise NotImplementedError

    def process_event(self, event: pygame.event.Event) -> None:
        """Update this player based on the pygame event.
        """
        raise NotImplementedError

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a potential move to make on the game board.

        The move is a tuple consisting of a string, an optional integer, and
        a block. The string indicates the move being made (i.e., rotate, swap,
        or smash). The integer indicates the direction (i.e., for rotate and
        swap). And the block indicates which block is being acted on.

        Return None if no move can be made, yet.
        """
        raise NotImplementedError


def _create_move(action: Tuple[str, Optional[int]], block: Block) -> \
        Tuple[str, Optional[int], Block]:
    return action[0], action[1], block


class HumanPlayer(Player):
    """A human player."""
    # === Private Attributes ===
    # _level:
    #     The level of the Block that the user selected most recently.
    # _desired_action:
    #     The most recent action that the user is attempting to do.
    #
    # == Representation Invariants concerning the private attributes ==
    #     _level >= 0
    _level: int
    _desired_action: Optional[Tuple[str, Optional[int]]]

    def __init__(self, player_id: int, goal: Goal) -> None:
        """Initialize this HumanPlayer with the given <renderer>, <player_id>
        and <goal>.
        """
        Player.__init__(self, player_id, goal)

        # This HumanPlayer has not yet selected a block, so set _level to 0
        # and _selected_block to None.
        self._level = 0
        self._desired_action = None

    def get_selected_block(self, board: Block) -> Optional[Block]:
        """Return the block that is currently selected by the player based on
        the position of the mouse on the screen and the player's desired level.

        If no block is selected by the player, return None.
        """
        mouse_pos = pygame.mouse.get_pos()
        block = _get_block(board, mouse_pos, self._level)

        return block

    def process_event(self, event: pygame.event.Event) -> None:
        """Respond to the relevant keyboard events made by the player based on
        the mapping in KEY_ACTION, as well as the W and S keys for changing
        the level.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in KEY_ACTION:
                self._desired_action = KEY_ACTION[event.key]
            elif event.key == pygame.K_w:
                self._level = max(0, self._level - 1)
                self._desired_action = None
            elif event.key == pygame.K_s:
                self._level += 1
                self._desired_action = None

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return the move that the player would like to perform. The move may
        not be valid.

        Return None if the player is not currently selecting a block.
        """
        block = self.get_selected_block(board)

        if block is None or self._desired_action is None:
            return None
        else:
            move = _create_move(self._desired_action, block)

            self._desired_action = None
            return move


class RandomPlayer(Player):
    """ A Random Player.
    === Public Attributes ===
    id:
    This player's number.
    goal:
    This player's assigned goal for the game.
    """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    id: int
    goal: Goal
    _proceed: bool

    def __init__(self, player_id: int, goal: Goal) -> None:
        Player.__init__(self, player_id, goal)
        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid, randomly generated move.

        A valid move is a move other than PASS that can be successfully
        performed on the <board>.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove
        if board is None:
            return None
        # Board is okay to be analyzed
        # s0 horiz swap, s1 is vert swap, r1 is cw rot, r3 is ccw rot
        mov_lst = [SMASH, SWAP_HORIZONTAL,SWAP_VERTICAL,
                   ROTATE_COUNTER_CLOCKWISE, ROTATE_CLOCKWISE,
                   PAINT, COMBINE]
        # While there is still something left to analyze
        while len(mov_lst) != 0:
            rnd_mov = random.choice(mov_lst)
            cp = board.create_copy()  # To not mutate original board
            if rnd_mov == SMASH:
                if cp.smashable():
                    self._proceed = False
                    return _create_move(SMASH, board)
                else:
                    mov_lst.remove(SMASH)
            elif rnd_mov in [SWAP_HORIZONTAL, SWAP_VERTICAL,
                             ROTATE_COUNTER_CLOCKWISE, ROTATE_CLOCKWISE]:
                if len(cp.children) != 0:
                    self._proceed = False
                    return _create_move(rnd_mov, board)
                else:
                    mov_lst.remove(rnd_mov)
            elif rnd_mov == COMBINE:
                if cp.combine():
                    self._proceed = False
                    return _create_move(COMBINE, board)
                else:
                    mov_lst.remove(rnd_mov)
            else:
                if cp.paint(self.goal.colour):
                    self._proceed = False
                    return _create_move(PAINT, board)
                else:
                    mov_lst.remove(rnd_mov)


class SmartPlayer(Player):
    """ A Smart Player.
    === Public Attributes ===
    id:
    This player's number.
    goal:
    This player's assigned goal for the game.
    """
    # === Private Attributes ===
    # _proceed:
    #   True when the player should make a move, False when the player should
    #   wait.
    player_id: int
    goal: Goal
    _proceed: bool
    difficulty: int

    def __init__(self, player_id: int, goal: Goal, difficulty: int) -> None:
        Player.__init__(self, player_id, goal)

        self._proceed = False

    def get_selected_block(self, board: Block) -> Optional[Block]:
        return None

    def process_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._proceed = True

    def generate_move(self, board: Block) -> \
            Optional[Tuple[str, Optional[int], Block]]:
        """Return a valid move by assessing multiple valid moves and choosing
        the move that results in the highest score for this player's goal (i.e.,
        disregarding penalties).

        A valid move is a move other than PASS that can be successfully
        performed on the <board>. If no move can be found that is better than
        the current score, this player will pass.

        This function does not mutate <board>.
        """
        if not self._proceed:
            return None  # Do not remove
        if board is None:
            return None
        # Board is okay to be analyzed
        mov_lst = [SMASH, SWAP_HORIZONTAL, SWAP_VERTICAL,
                   ROTATE_COUNTER_CLOCKWISE, ROTATE_CLOCKWISE,
                   PAINT, COMBINE]
        valid_movs = []  # Contains tuple (move, score)
        # find list of valid moves and compute their score
        while len(mov_lst) != 0:
            rnd_mov = random.choice(mov_lst)
            cp = board.create_copy()  # To not mutate original board
            if rnd_mov == SMASH:
                if cp.smashable():
                    cp.smash()
                    valid_movs.append((SMASH, self.goal.score(cp)))
                    mov_lst.remove(SMASH)
                else:
                    mov_lst.remove(SMASH)
            elif rnd_mov in [SWAP_HORIZONTAL, SWAP_VERTICAL,
                             ROTATE_COUNTER_CLOCKWISE, ROTATE_CLOCKWISE]:
                if len(cp.children) != 0:
                    if rnd_mov == SWAP_HORIZONTAL:
                        cp.swap(0)
                        valid_movs.append((SWAP_HORIZONTAL,
                                          self.goal.score(cp)))
                        mov_lst.remove(SWAP_HORIZONTAL)
                    elif rnd_mov == SWAP_VERTICAL:
                        cp.swap(1)
                        valid_movs.append((SWAP_VERTICAL,
                                          self.goal.score(cp)))
                        mov_lst.remove(SWAP_VERTICAL)
                    elif rnd_mov == ROTATE_CLOCKWISE:
                        cp.rotate(1)
                        valid_movs.append((ROTATE_CLOCKWISE,
                                          self.goal.score(cp)))
                        mov_lst.remove(ROTATE_CLOCKWISE)
                    else:
                        cp.rotate(3)
                        valid_movs.append((ROTATE_COUNTER_CLOCKWISE,
                                           self.goal.score(cp)))
                        mov_lst.remove(ROTATE_COUNTER_CLOCKWISE)
                else:
                    mov_lst.remove(rnd_mov)
            elif rnd_mov == COMBINE:
                if cp.combine():
                    valid_movs.append((COMBINE, self.goal.score(cp)))
                    mov_lst.remove(COMBINE)
                else:
                    mov_lst.remove(rnd_mov)
            else:
                if cp.paint(self.goal.colour):
                    valid_movs.append((PAINT, self.goal.score(cp)))
                    mov_lst.remove(PAINT)
                else:
                    mov_lst.remove(rnd_mov)
        # Pick max score
        if len(valid_movs) != 0:
            max_score = 0
            ind = 0
            for i in range(len(valid_movs)):
                if valid_movs[i][1] > max_score:
                    ind = i
                    max_score = valid_movs[i][1]
            if self.goal.score(board) < max_score:
                self._proceed = False
                return _create_move(valid_movs[ind][0], board)


if __name__ == '__main__':
    import python_ta

    python_ta.check_all(config={
        'allowed-io': ['process_event'],
        'allowed-import-modules': [
            'doctest', 'python_ta', 'random', 'typing', 'actions', 'block',
            'goal', 'pygame', '__future__'
        ],
        'max-attributes': 10,
        'generated-members': 'pygame.*'
    })
