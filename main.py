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

    def __init__(self, length: int, clues: list[int]):
        self.length = length
        self.clues = clues
        self.cells = [0] * length

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


class Game:

    def __init__(self, width: int, height: int, row_clues: list[list[int]], column_clues: list[list[int]]):
        self.width = width
        self.height = height
        self.row_clues = row_clues
        self.column_clues = column_clues
        self.rows = [Line(width, row_clue) for row_clue in row_clues]
        self.columns = [Line(height, column_clue) for column_clue in column_clues]
        self.board = [[0] * width for i in range(height)]
        self.lines = self.rows + self.columns

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
    game.print_board()
