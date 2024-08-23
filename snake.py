from random import randint

class Board:
    def __init__(self):
        self.board = [[None]*30 for _ in range(30)]
        self.count = 0
        self.gen_item()

    def add_snake(self, snake):
        idmap = {0: (0, 0), 1: (29, 0), 2: (0, 29), 3: (29, 29)}
        x, y = idmap[snake.id]
        snake.body.append((x, y))
        self.board[x][y] = snake.id

    def gen_item(self):
        if self.count == 0:
            while True:
                x, y = randint(0, 29), randint(0, 29)
                if self.board[x][y] is None:
                    self.board[x][y] = 4
                    self.count += 1
                    break

    def __str__(self):
        board_str = "_"*60 + "\n"
        for row in self.board:
            row_str = " ".join(f"{val if val is not None else '.'}" for val in row)
            board_str += row_str + "\n"
        return board_str

    def to_list(self):
        return [[cell for cell in row] for row in self.board]

class Snake:
    def __init__(self, id):
        self.id = id
        self.size = 1
        self.body = []
        self.alive = True
        if id % 2 == 0:
            self.direction = (0, 1) 
        else:
            self.direction = (0, -1) 


    def move(self, board):
        if not self.alive:
            raise Exception("dead")
        head_x, head_y = self.body[0]
        new_head_x = head_x + self.direction[0]
        new_head_y = head_y + self.direction[1]
        if 0 <= new_head_x < 30 and 0 <= new_head_y < 30:
            if board.board[new_head_x][new_head_y] == 4:
                self.size += 1
                board.count -= 1
                board.gen_item()
            elif board.board[new_head_x][new_head_y] != None:
                self.alive=False
                raise Exception("Eaten")
            else:
                tail = self.body.pop()
                board.board[tail[0]][tail[1]] = None
            self.body.insert(0, (new_head_x, new_head_y))
            board.board[new_head_x][new_head_y] = self.id
        else:
            self.alive=False
            raise Exception("L")

    def change_direction(self, new_direction):
        if (self.direction[0] + new_direction[0] != 0 or 
            self.direction[1] + new_direction[1] != 0):
            self.direction = new_direction
