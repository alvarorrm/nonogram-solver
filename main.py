"""

This programs aims to solve a nonogram in the same way a human would.
I am trying to implement the logical steps I make when solving one myself.

"""


class Line:
    """ Class that represents a line of a nonogram

    Attributes:
        length (int): the length of the line
        cells (list[int]): the contents of the line (0: empty, 1: box, -1: cross)
        clues (list[int]): the groups of boxes in the line

    """

    class Group:
        def __init__(self, start=None, end=None, length=None, clue=None):
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
            self.clue = clue

    def __init__(self, length: int, clues: list[int]):
        self.length = length
        self.cells = [0] * length
        self.clues = clues
        self.groups = []
        self.solved_clues = [False * len(clues)]

    def write_cells(self, cells):
        self.cells = cells

    def get_cell(self, i):
        return self.cells[i]

    def set_cell(self, i, value):
        self.cells[i] = value

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
        box_at_beginning = self.cells[0] == 1
        first_clue_filled = all([self.cells[i] == 1 for i in range(self.clues[0])])
        if box_at_beginning and first_clue_filled:
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
        if len(self.clues) > 1:
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

    def get_box_groups(self):
        groups = []
        group_len = 0
        for i, cell in enumerate(self.cells):
            if cell == 0 and group_len > 0:
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

    def surround_max_size_groups_with_crosses(self):
        groups = self.get_box_groups()
        max_len_clue = max(self.clues)
        for group in groups:
            if group.length == max_len_clue:
                if group.start-1 >= 0:
                    self.cells[group.start-1] = -1
                if group.end+1 < self.length:
                    self.cells[group.end+1] = -1



class Game:

    def __init__(self, width: int, height: int, row_clues: list[list[int]], column_clues: list[list[int]]):
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

    def print_board(self):
        pieces = {
            0: "\u25A1",  # empty cell
            1: "\u25A0",  # box
            -1: "\u2717"  # cross
        }
        for row in self.board:
            print(" ".join(pieces[val] for val in row))

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


if __name__ == "__main__":
    n = 15
    row_clues = [
        [1, 3, 2],
        [4, 6, 1],
        [3, 7, 1],
        [2, 8, 1],
        [1, 8, 2],
        [6, 2],
        [4, 5, 2],
        [5, 4, 2],
        [5, 3, 2],
        [4, 4, 2],
        [4, 2],
        [5, 2],
        [3, 3, 1, 2],
        [3, 3, 2],
        [3, 1, 2]
    ]
    column_clues = [
        [4, 4, 1],
        [3, 4, 1, 1],
        [2, 4, 1, 1],
        [2, 4, 1, 2],
        [1, 2, 4],
        [3, 5],
        [11],
        [12],
        [10],
        [8, 1],
        [6, 3],
        [4, 1],
        [4],
        [1, 11],
        [14]
    ]

    game = Game(n, n, row_clues, column_clues)
    game.fill_start_clues()
    game.fill_edge_clues()
    game.add_crosses_at_edge_groups()
    game.surround_single_clues_with_crosses()
    game.surround_max_size_groups_with_crosses()
    game.print_board()
