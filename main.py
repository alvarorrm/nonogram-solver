"""

This programs aims to solve a nonogram in the same way a human would.
I am trying to implement the logical steps I make when solving one myself.

"""
import copy
import json
import sys
import random

class Line:
    """ Class that represents a line of a nonogram

    Attributes:
        length (int): the length of the line
        cells (list[int]): the contents of the line (0: empty, 1: box, -1: cross)
        clues (list[int]): the groups of boxes in the line
        TO-DO: complete attributes

    Strategies:
        - Fill the beginning clues
        - Fill first and last clue if close to the edges
        - Surround a group with the same length as the longest clue with crosses
        - If there is only one clue and any box places, fill the rest of the row (that can't be reached) with crosses
        - If there is a group of the same length as the first/last clue touching an edge, add a cross at the end
        to add:
            - Match groups and clues
            - If there is any group matched to a clue, subdivide the line in the parts to the left and
                right of that clue (excluding any crosses) and solve those two individually

    """
    
    class Group:
        """ Class to store info about groups of cells """
        def __init__(self, start=None, end=None, length=None, cells=None):
            if length is None:
                self.start = start
                self.end = end
                self.length = end - start + 1
            elif start is None:
                self.start = end - length + 1
                self.end = end
                self.length = length
            elif end is None:
                self.start = start
                self.end = length - start - 1
                self.length = length
            self.cells = cells

        def __str__(self):
            group_string = (
                "Start: " + str(self.start) + ", "
                + "End: " + str(self.end) + ", "
                + "Length: " + str(self.length) + ", "
                + "Cells: " + str(self.cells)
            )
            return group_string

        def has_boxes(self):
            return any([cell == 1 for cell in self.cells])

        def has_crosses(self):
            return any([cell == -1 for cell in self.cells])

        def has_spaces(self):
            return any([cell == 0 for cell in self.cells])

        def is_full(self):
            return all([cell == 1 for cell in self.cells])

        def is_empty(self):
            return all([cell == 0 for cell in self.cells])

    def __init__(self, length: int, clues: list[int]):
        self.length = length
        self.cells = [0] * length
        self.clues = clues

    #### CELL MANAGEMENT METHODS ####
    def write_cells(self, cells):
        self.cells = cells

    def get_cell(self, i):
        return self.cells[i]

    def set_cell(self, i, value):
        self.cells[i] = value

    #### OTHER INFO METHODS ####
    def get_box_groups(self):
        groups = []
        group_len = 0
        for i, cell in enumerate(self.cells):
            if cell != 1 and group_len > 0:
                group = self.Group(end=i-1, length=group_len)
                groups.append(group)
                group_len = 0
            if cell == 1:
                group_len += 1
        if group_len > 0:
            group = self.Group(end=self.length-1, length=group_len)
            groups.append(group)
        return groups

    def is_solved(self):
        if [group.length for group in self.get_box_groups()] == self.clues:
            for i in range(len(self.cells)):
                if self.cells[i] == 0:
                    self.cells[i] = -1
            return True
        else:
            return False

    def fill_if_solved(self):
        if [group.length for group in self.get_box_groups()] == self.clues:
            for i in range(len(self.cells)):
                if self.cells[i] == 0:
                    self.cells[i] = -1

    def match_groups_and_clues(self):
        groups = self.get_box_groups()

    def get_groups_between_crosses(self):
        groups = []
        curr_group = []
        for i, cell in enumerate(self.cells):
            if cell == -1 and curr_group != []:
                group = self.Group(end=i - 1, length=len(curr_group), cells=curr_group)
                groups.append(group)
                curr_group = []
            if cell != -1:
                curr_group.append(cell)
        if curr_group != []:
            group = self.Group(end=self.length - 1, length=len(curr_group), cells=curr_group)
            groups.append(group)
        return groups

    #### STRATEGIES ####
    def solve_step(self):
        """ Try all the strategies once """
        if self.is_solved():
            return
        debug = False
        if debug: print("STARTING STATE:                                      ", self.cells, "Clues:", self.clues)
        self.fill_start_clues()
        if debug: print("After fill_start_clues:                              ", self.cells, "Clues:", self.clues)
        self.fill_edge_clues()
        if debug: print("After fill_edge_clues:                               ", self.cells, "Clues:", self.clues)
        self.add_crosses_at_edge_groups()
        if debug: print("After add_crosses_at_edge_groups:                    ", self.cells, "Clues:", self.clues)
        self.surround_single_clue_with_crosses()
        if debug: print("After surround_single_clue_with_crosses:             ", self.cells, "Clues:", self.clues)
        self.connect_boxes_if_one_clue()
        if debug: print("After connect_boxes_if_one_clue:                     ", self.cells, "Clues:", self.clues)
        self.surround_max_size_groups_with_crosses()
        if debug: print("After surround_max_size_groups_with_crosses:         ", self.cells, "Clues:", self.clues)
        self.fill_edge_spaces_with_crosses_if_close_to_clue()
        if debug: print("After fill_edge_spaces_with_crosses_if_close_to_clue:", self.cells, "Clues:", self.clues)
        self.fill_spaces_shorter_than_min_clue()
        if debug: print("After fill_spaces_shorter_than_min_clue:             ", self.cells, "Clues:", self.clues)
        self.fit_clues_in_holes()
        if debug: print("After fit_clues_in_holes:                            ", self.cells, "Clues:", self.clues)
        self.solve_sublines_if_clear_correspondence()
        if debug: print("After solve_sublines_if_clear_correspondence:        ", self.cells, "Clues:", self.clues)
        self.solve_subline_if_edge_clues_solved()
        if debug: print("After solve_subline_if_edge_clues_solved:            ", self.cells, "Clues:", self.clues)
        self.solve_subline_if_surrounded_by_crosses()
        if debug: print("After solve_subline_if_surrounded_by_crosses:        ", self.cells, "Clues:", self.clues)
        self.fill_edge_groups_if_clues_dont_fit()
        if debug: print("After fill_edge_groups_if_clues_dont_fit:            ", self.cells, "Clues:", self.clues)
        self.fill_if_solved()
        if debug: print("After fill_if_solved:                                ", self.cells, "Clues:", self.clues)
        self.solve_edge_groups_if_only_edge_clues_fit()
        if debug: print("After solve_edge_groups_if_only_edge_clues_fit:     ", self.cells, "Clues:", self.clues)
        # self.pad_edge_groups_if_only_two_clues_fit()
        # if debug: print("After pad_edge_groups_if_only_two_clues_fit:     ", self.cells, "Clues:", self.clues)


    def solve(self):
        """ Try to solve the line until there are no changes """
        prev_cells = self.cells.copy()
        self.solve_step()
        while prev_cells != self.cells:
            prev_cells = self.cells.copy()
            self.solve_step()

    def fill_start_clues(self):
        """ Fill the minimum cells that must have a box from the starting point (empty line)

        1st - The algorithm calculates the "wiggle room" of the row (which is the free spaces if you placed all the
        clues one after the other)
        2nd - The clues are places one after the other, but not filling in the first {wiggle_room} cells of each group

        Example:
            A line of length 15 with the clues [4, 3, 4]
            Clues placed one after the other:
            [X X X X 0 X X X 0 X X X X 0 0]
                                       ^ ^  -> wiggle room = 2
            [0 0 X X 0 0 0 X 0 0 0 X X 0 0]
             ^ ^       ^ ^     ^ ^          -> first {wiggle_room} cells not filled

        """
        min_line_length = sum(self.clues) + len(self.clues) - 1
        wiggle_room = self.length - min_line_length
        group = 0
        group_i = 0
        for line_i in range(min_line_length):
            if group_i >= self.clues[group]:
                group += 1
                group_i = 0
                continue
            if group_i >= wiggle_room:
                self.cells[line_i] = 1
            group_i += 1

    def fill_first_clue(self):
        """ Fills the boxes given by the first clue if there is a box sufficiently close to the starting edge

        Example:
            There is a line with the following content:
            [0 0 0 X 0 0 0 0 0 0 0 0 0 0 0]
            And the first clue (the leftmost) is a 6
            Then, the first cells up to the 6th and after the first filled cell must be boxes:
            [0 0 0 X X X 0 0 0 0 0 0 0 0 0]

        """
        first_clue = self.clues[0]
        if 1 in self.cells[:first_clue]:
            first_index = self.cells[:first_clue].index(1)
            self.cells[first_index:first_clue] = [1] * (first_clue - first_index)

    def fill_last_clue(self):
        self.clues.reverse()
        self.cells.reverse()
        self.fill_first_clue()
        self.clues.reverse()
        self.cells.reverse()

    def fill_edge_clues(self):
        self.fill_first_clue()
        self.fill_last_clue()

    def add_cross_at_beginning_group(self):
        """ If there is a group of the same length as the first clue touching the start edge, add a cross at the end"""
        box_at_beginning = self.cells[0] == 1
        first_clue_filled = all([self.cells[i] == 1 for i in range(self.clues[0])])
        if box_at_beginning and first_clue_filled:
            if self.clues[0] < self.length:
                self.cells[self.clues[0]] = -1

    def add_cross_at_end_group(self):
        self.cells.reverse()
        self.clues.reverse()
        self.add_cross_at_beginning_group()
        self.cells.reverse()
        self.clues.reverse()

    def add_crosses_at_edge_groups(self):
        self.add_cross_at_beginning_group()
        self.add_cross_at_end_group()

    def surround_single_clue_with_crosses(self):
        """ If the line only has one clue, fill the places that can't have boxes with crosses """
        if len(self.clues) != 1:
            return
        group_start = None
        group_end = None
        for i, cell in enumerate(self.cells):
            if cell == 1:
                group_end = i
                if group_start is None:
                    group_start = i
        if group_start is None:
            return
        group_len = group_end - group_start + 1
        padding = self.clues[0] - group_len
        for i in range(len(self.cells)):
            if group_start - i > padding or i - group_end > padding:
                self.cells[i] = -1

    def connect_boxes_if_one_clue(self):
        """ If the line only has one clue and there are boxes with spaces between them, connect them"""
        if len(self.clues) != 1:
            return
        start = None
        end = None
        for i in range(self.length):
            if self.cells[i] == 1:
                if start is None:
                    start = i
                end = i
        if start is None:
            return
        self.cells[start:end] = [1] * (end - start)

    def surround_max_size_groups_with_crosses(self):
        """ If there are any groups of the same size as the longest clue, surround them with crosses """
        groups = self.get_box_groups()
        max_len_clue = max(self.clues)
        for group in groups:
            if group.length == max_len_clue:
                if group.start-1 >= 0:
                    self.cells[group.start-1] = -1
                if group.end+1 < self.length:
                    self.cells[group.end+1] = -1

    def fill_beginning_spaces_with_crosses_if_close_to_clue(self):
        if not any([cell == 1 for cell in self.cells]):
            return
        spaces_at_start = 0
        for cell in self.cells:
            if cell != 1:
                spaces_at_start += 1
            else:
                break
        if spaces_at_start <= self.clues[0]:
            first_group_len = self.get_box_groups()[0].length
            spaces_to_fill = spaces_at_start - (self.clues[0] - first_group_len)
            self.cells[:spaces_to_fill] = [-1] * spaces_to_fill
            if first_group_len == self.clues[0] and spaces_to_fill + first_group_len < self.length:
                self.cells[spaces_to_fill + first_group_len] = -1

    def fill_end_spaces_with_crosses_if_close_to_clue(self):
        self.cells.reverse()
        self.clues.reverse()
        self.fill_beginning_spaces_with_crosses_if_close_to_clue()
        self.cells.reverse()
        self.clues.reverse()

    def fill_edge_spaces_with_crosses_if_close_to_clue(self):
        self.fill_beginning_spaces_with_crosses_if_close_to_clue()
        self.fill_end_spaces_with_crosses_if_close_to_clue()

    def solve_sublines_if_clear_correspondence(self):
        groups = self.get_groups_between_crosses()
        n_groups_with_boxes = sum([group.has_boxes() for group in groups])
        n_clues = len(self.clues)

        if n_groups_with_boxes == n_clues:
            clue_ix = 0
            for group in groups:
                if group.has_boxes():
                    subline = Line(length=group.length, clues=[self.clues[clue_ix]])
                    clue_ix += 1
                    subline.cells = self.cells[group.start:group.end+1]
                    if subline.length < self.length:
                        subline.solve()
                        self.cells[group.start:group.end+1] = subline.cells
                else:
                    self.cells[group.start:group.end+1] = [-1] * group.length

    def solve_sublines_if_first_clue_solved(self):
        groups = self.get_groups_between_crosses()
        if self.is_solved():
            return
        if groups[0].is_full():
            subline_length = self.length - groups[0].end - 2
            subline = Line(subline_length, self.clues[1:])
            subline.cells = self.cells[groups[0].end+2:]
            subline.solve()
            self.cells[groups[0].end+2:] = subline.cells

    def solve_subline_if_last_clue_solved(self):
        self.cells.reverse()
        self.clues.reverse()
        self.solve_sublines_if_first_clue_solved()
        self.cells.reverse()
        self.clues.reverse()

    def solve_subline_if_edge_clues_solved(self):
        self.solve_sublines_if_first_clue_solved()
        self.solve_subline_if_last_clue_solved()

    def solve_subline_if_surrounded_by_crosses(self):
        groups = self.get_groups_between_crosses()
        if groups[0].start != 0 or groups[-1].end != self.length-1:
            subline_length = groups[-1].end - groups[0].start + 1
            subline = Line(subline_length, self.clues)
            subline.cells = self.cells[groups[0].start:groups[-1].end+1]
            subline.solve()
            self.cells[groups[0].start:groups[-1].end+1] = subline.cells

    def fill_spaces_shorter_than_min_clue(self):
        groups = self.get_groups_between_crosses()
        min_clue = min(self.clues)
        for group in groups:
            if group.length < min_clue:
                self.cells[group.start:group.end+1] = [-1] * group.length

    def fit_clues_in_holes(self):
        # return
        groups = self.get_groups_between_crosses()
        if [group.length for group in groups] == self.clues:
            for group in groups:
                self.cells[group.start:group.end+1] = [1] * group.length

    def fill_first_group_if_clue_dont_fit(self):
        groups = self.get_groups_between_crosses()
        if groups[0].length < self.clues[0]:
            self.cells[groups[0].start:groups[0].end+1] = [-1] * groups[0].length

    def fill_last_group_if_clue_dont_fit(self):
        self.cells.reverse()
        self.clues.reverse()
        self.fill_first_group_if_clue_dont_fit()
        self.cells.reverse()
        self.clues.reverse()

    def fill_edge_groups_if_clues_dont_fit(self):
        self.fill_first_group_if_clue_dont_fit()
        self.fill_last_group_if_clue_dont_fit()

    def solve_first_group_if_only_first_clue_fits(self):
        groups = self.get_groups_between_crosses()
        if len(self.clues) < 2:
            return
        if groups[0].has_boxes():
            if self.clues[0] + self.clues[1] + 1 > groups[0].length:
                first_group = Line(groups[0].length, [self.clues[0]])
                first_group.cells = self.cells[groups[0].start:groups[0].end + 1]
                first_group.solve()
                self.cells[groups[0].start:groups[0].end+1] = first_group.cells
                if len(self.clues) >= 2 and groups[0].end + 2 < self.length:
                    rest_of_line = Line(self.length - groups[0].end - 2, self.clues[1:])
                    rest_of_line.cells = self.cells[groups[0].end + 2:]
                    rest_of_line.solve()
                    self.cells[groups[0].end + 2:] = rest_of_line.cells

    def solve_last_group_if_only_first_clue_fits(self):
        self.cells.reverse()
        self.clues.reverse()
        self.solve_first_group_if_only_first_clue_fits()
        self.cells.reverse()
        self.clues.reverse()

    def solve_edge_groups_if_only_edge_clues_fit(self):
        self.solve_first_group_if_only_first_clue_fits()
        self.solve_last_group_if_only_first_clue_fits()

    def pad_first_group_if_only_two_clues_fit(self):
        groups = self.get_groups_between_crosses()
        box_groups = self.get_box_groups()
        if not groups[0].has_boxes():
            return
        if len(self.clues) < 2:
            return
        if self.clues[0] + self.clues[1] + 1 <= groups[0].end:
            print("-"*20)
            print(self.cells, self.clues)
            for group in box_groups:
                if group.start <= groups[0].end and group.length == max(self.clues[0], self.clues[1]):
                    if group.start - 1 >= 0:
                        self.cells[group.start - 1] = -1
                    if group.end + 1 < self.length:
                        self.cells[group.end + 1] = -1
            print(self.cells)

    def pad_last_group_if_only_two_clues_fit(self):
        self.cells.reverse()
        self.clues.reverse()
        self.pad_first_group_if_only_two_clues_fit()
        self.cells.reverse()
        self.clues.reverse()

    def pad_edge_groups_if_only_two_clues_fit(self):
        self.pad_first_group_if_only_two_clues_fit()
        self.pad_last_group_if_only_two_clues_fit()



class Game:

    def __init__(self, row_clues: list[list[int]], column_clues: list[list[int]], width: int=None, height: int=None):
        if width != len(column_clues) and width is not None:
            raise ValueError("The number of column clues must be equal to the width")
        if height != len(row_clues) and height is not None:
            raise ValueError("The number of row clues must be equal to the height")
        if width is None:
            width = len(column_clues)
        if height is None:
            height = len(row_clues)
        self.width = width
        self.height = height
        self.row_clues = row_clues
        self.column_clues = column_clues
        self.rows = [Line(width, row_clue) for row_clue in row_clues]
        self.columns = [Line(height, column_clue) for column_clue in column_clues]
        self.board = [[0] * width for _ in range(height)]
        self.lines = self.rows + self.columns

    def get_row(self, n):
        return self.rows[n]

    def get_column(self, n):
        return self.columns[n]

    @staticmethod
    def print_board(board):
        pieces = {
            0: "\u25A1",  # empty cell
            1: "\u25A0",  # box
            -1: "\u2717"  # cross
        }
        for row in board:
            print(" ".join(pieces[val] for val in row))

    def print_game(self, show_clues=True):

        if not show_clues:
            self.print_board(self.board)
            return
        max_len_row_clue = max([len(" ".join([str(clue) for clue in row_clue])) for row_clue in self.row_clues])
        max_len_column_clue = max([len(column_clue) for column_clue in self.column_clues])
        pieces = {
            0: "\u25A1",  # empty cell
            1: "\u25A0",  # box
            -1: "\u2717"  # cross
        }
        for i in range(max_len_column_clue):
            str_line = " " * (max_len_row_clue + 2)
            for column_clue in self.column_clues:
                clue_ix = i + len(column_clue) - max_len_column_clue
                if 0 <= clue_ix < len(column_clue):
                    if len(str(column_clue[clue_ix])) > 1:
                        str_line = str_line[:-1]
                    str_line += str(column_clue[clue_ix])
                else:
                    str_line += " "
                str_line += "  "
            str_line = str_line[:-1]
            print(str_line)
        for i, row in enumerate(self.board):
            clue_string = " ".join(str(clue) for clue in self.row_clues[i]).rjust(max_len_row_clue)
            print(clue_string + "  " + "  ".join(pieces[val] for val in row))

    def print_rows(self):
        row_board = [row.cells for row in self.rows]
        self.print_board(row_board)

    def print_columns(self):
        column_board = []
        for i in range(self.height):
            row = []
            for j in range(self.width):
                row.append(self.columns[j].get_cell(i))
            column_board.append(row)
        self.print_board(column_board)

    def update_board(self):
        for i in range(self.height):
            for j in range(self.width):
                row_value = self.rows[i].get_cell(j)
                column_value = self.columns[j].get_cell(i)
                if row_value == 0 and column_value == 0:
                    self.board[i][j] = 0
                elif row_value == 0:
                    self.board[i][j] = column_value
                elif column_value == 0:
                    self.board[i][j] = row_value
                else:  # both values are != 0
                    if row_value != column_value:
                        raise ValueError(
                            "There is a conflict between the row and column values at position [{}], [{}]".format(i, j))
                    self.board[i][j] = row_value

    def update_lines(self):
        for i in range(self.height):
            for j in range(self.width):
                self.rows[i].set_cell(j, self.board[i][j])
                self.columns[j].set_cell(i, self.board[i][j])

    def update(self):
        self.update_board()
        self.update_lines()

    def fill_start_clues(self):
        for line in self.lines:
            line.fill_start_clues()
        self.update()

    def fill_edge_clues(self):
        for i, line in enumerate(self.lines):
            line.fill_edge_clues()
        self.update()

    def add_crosses_at_edge_groups(self):
        for line in self.lines:
            line.add_crosses_at_edge_groups()
        self.update()

    def surround_single_clues_with_crosses(self):
        for line in self.lines:
            line.surround_single_clue_with_crosses()
        self.update()

    def surround_max_size_groups_with_crosses(self):
        for line in self.lines:
            line.surround_max_size_groups_with_crosses()
        self.update()

    def solve_step(self):
        for line in self.lines:
            line.solve()
        self.update()

    def solve(self):
        prev_board = copy.deepcopy(self.board)
        self.solve_step()
        while prev_board != self.board:
            prev_board = copy.deepcopy(self.board)
            self.solve_step()

    def is_solved(self):
        for i, row in enumerate(self.rows):
            if not row.is_solved():
                print("Error in row", i)
                return False
        for i, column in enumerate(self.columns):
            if not column.is_solved():
                print("Error in column", i)
                return False
        return True

def run_game_history(game_history_path):
    # game_history_path = "game_history.json"

    def read_clue(clue_str):
        clues = []
        curr_num = ""
        for char in clue_str:
            if char.isdigit():
                curr_num += char
            elif curr_num != "":
                clues.append(int(curr_num))
                curr_num = ""
        if curr_num != "":
            clues.append(int(curr_num))
        return clues

    try:
        with open(game_history_path, 'r') as json_file:
            game_history = json.load(json_file)
        game_number = len(game_history) + 1
    except FileNotFoundError:
        with open(game_history_path, 'w') as json_file:
            json.dump([], json_file, indent=2)
        game_history = []
        game_number = 1

    game_loaded = False
    if len(game_history) > 0:
        history_input = input("Load game from history? (Y/N/P): ")
        if history_input == "P":
            game_loaded = True
            row_clues = game_history[0]["row"]
            column_clues = game_history[0]["column"]
        elif history_input == "Y":
            game_loaded = True
            print(str(len(game_history)) + " games in history")
            game_to_load = input("Load game number ")
            game_to_load = int(game_to_load)
            row_clues = game_history[game_to_load]["row"]
            column_clues = game_history[game_to_load]["column"]

    if not game_loaded:
        row_clues = []
        row = 0
        while row < height:
            clue_str = input("Row " + str(row) + ": ")
            if clue_str == "-":
                row = max(row - 1, 0)
            clue = read_clue(clue_str)
            row_clues.append(clue)
            row += 1

        column_clues = []
        column = 0
        while column < width:
            clue_str = input("Column " + str(column) + ": ")
            if clue_str == "-":
                column = max(column - 1, 0)
                continue
            clue = read_clue(clue_str)
            column_clues.append(clue)
            column += 1

    game = Game(row_clues, column_clues)
    game.print_game()

    edit = True
    while edit:
        try:
            edit_str = input("Edit: ")
            index = int(edit_str[1:]) - 1
            if index < 0:
                print("The index must be >= 1")
                continue
            if edit_str[0] in "Cc":
                orientation = "column"
                current_clue = column_clues[index]
            elif edit_str[0] in "Rr":
                orientation = "row"
                current_clue = row_clues[index]
            else:
                break
            print("Current clue in " + orientation + " " + str(index + 1) + ": " + str(current_clue))
            new_clue = input("New clue: ")
            new_clue = read_clue(new_clue)
            current_clue[:] = new_clue
            game = Game(row_clues, column_clues)
            game.print_game()
            print("New clue in " + orientation + " " + str(index + 1) + ": " + str(new_clue))

        except ValueError:
            break

    with open(game_history_path, 'w') as json_file:
        game_history.insert(0, {"row": row_clues, "column": column_clues})
        json.dump(game_history, json_file, indent=2)

    return row_clues, column_clues

def generate_random_clues(width, height):
    board = [[random.random()<0.3 for j in range(width)] for i in range(height)]
    row_clues = []
    for i in range(height):
        line = Line(width, [])
        line.cells = board[i]
        groups = line.get_box_groups()
        clue = [group.length for group in groups]
        row_clues.append(clue)

    column_clues = []
    for j in range(width):
        line = Line(width, [])
        column = [board[i][j] for i in range(height)]
        line.cells = column
        groups = line.get_box_groups()
        clue = [group.length for group in groups]
        column_clues.append(clue)

    return row_clues, column_clues, board

if __name__ == "__main__":

    width = 15
    height = 20

    # row_clues, column_clues, solution = generate_random_clues(width, height)

    row_clues = [
        [7],
        [7],
        [1, 1, 1, 1],
        [3, 3],
        [3, 3],
        [2, 1, 1, 2],
        [3, 3],
        [9],
        [7],
        [2, 2],
        [2, 3],
        [6, 1],
        [2, 2, 3],
        [4, 3, 1],
        [2, 3, 1, 3],
        [3, 1, 5],
        [4, 5],
        [4, 5],
        [1, 1, 1, 1],
        [1, 1, 1, 1]
    ]

    column_clues = [
        [4],
        [7],
        [3, 2, 3],
        [4, 1, 4, 4],
        [2, 2, 3, 2, 3],
        [3, 8, 1],
        [2, 4, 2],
        [2, 2, 2],
        [2, 6, 1],
        [3, 6, 3],
        [2, 2, 3, 3, 3],
        [4, 1, 1, 6],
        [3, 5],
        [6],
        [3]
    ]

    game = Game(row_clues, column_clues)
    # game.board = solution
    game.update_lines()
    if game.is_solved():
        print("THE PUZZLE HAS A SOLUTION")
    else:
        print("INCORRECT PUZZLE")
        game.print_game()
        sys.exit
    game = Game(row_clues, column_clues)
    game.solve()
    game.print_game()
    if game.is_solved():
        print("CORRECT")
    else:
        print("INCORRECT")



    # line = game.get_column(-2)
    # groups = line.get_groups_between_crosses()
    # for i, group in enumerate(groups):
    #     print("-"*20)
    #     print("Group", i)
    #     print(group)
    # row_clue = [1, 12, 1, 1]
    # print(len(" ".join([str(clue) for clue in row_clue])))
