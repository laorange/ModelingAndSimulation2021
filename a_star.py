import pandas as pd
import plotly
import plotly.express as px

# TODO: 地图大小
LENGTH = 100
WIDTH = 100
HEIGHT = 100

# TODO: 起点位置 的 x,y,z坐标
STARTING_POINT_X = 10
STARTING_POINT_Y = 10
STARTING_POINT_Z = 10

# TODO: 终点位置 的 x,y,z坐标
TERMINAL_POINT_X = 80
TERMINAL_POINT_Y = 80
TERMINAL_POINT_Z = 80

# TODO: 计算过的点将会添加到此处
computed_points = []
closed_points = []
obstacle_points = []


# TODO: 在此处设置障碍物的位置
def this_point_is_an_obstacle(x: int, y: int, z: int):
    FLAG = False
    if y < x - 30:
        FLAG = True
    if z < y - 30:
        FLAG = True
    if x < z - 30:
        FLAG = True
    return FLAG


class Point:
    def __init__(self, x: int, y: int, z: int, g: int = 0, t: int = 0):
        self.x = x
        self.y = y
        self.z = z

        # g: 步数
        self.g = g

        # h: 距离终点的Manhattan distance: h(n) = D ∗ (dx + dy + dz)
        self.h = int(abs(TERMINAL_POINT_X - self.x) + abs(TERMINAL_POINT_Y - self.y) + abs(TERMINAL_POINT_Z - self.z))

        # f: f = g + h
        self.f = self.g + self.h

        # t: 默认值为g, 数值越大颜色越鲜艳
        self.t = g if t == 0 else t


class OperationalPoint(Point):
    def __init__(self, x: int, y: int, z: int, g: int = 0, t: int = 0):
        super(OperationalPoint, self).__init__(x, y, z, g, t)
        self.iterate_funcs = [self.move_x, self.move_y, self.move_z]

    def move_x(self, forward=True):
        if forward:
            x_new = self.x + 1
        else:
            x_new = self.x - 1
        if x_new > LENGTH or x_new < 0:
            obstacle_points.append(Point(x_new, self.y, self.z))
            raise Exception(f"当前坐标：({self.x}, {self.y}, {self.z})，向x轴{'正' if forward else '负'}方向移动时超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(x_new, self.y, self.z):
                obstacle_points.append(Point(x_new, self.y, self.z))
                raise Exception(f"当前坐标：({self.x}, {self.y}, {self.z})，向x轴{'正' if forward else '负'}方向移动时遇到障碍物")
            return OperationalPoint(x_new, self.y, self.z, g=g_new)

    def move_y(self, forward=True):
        if forward:
            y_new = self.y + 1
        else:
            y_new = self.y - 1
        if y_new > WIDTH or y_new < 0:
            obstacle_points.append(Point(self.x, y_new, self.z))
            raise Exception(f"当前坐标：({self.x}, {self.y}, {self.z})，向y轴{'正' if forward else '负'}方向移动时超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(self.x, y_new, self.z):
                obstacle_points.append(Point(self.x, y_new, self.z))
                raise Exception(f"当前坐标：({self.x}, {self.y}, {self.z})，向y轴{'正' if forward else '负'}方向移动时遇到障碍物")
            return OperationalPoint(self.x, y_new, self.z, g=g_new)

    def move_z(self, forward=True):
        if forward:
            z_new = self.z + 1
        else:
            z_new = self.z - 1
        if z_new > HEIGHT or z_new < 0:
            obstacle_points.append(Point(self.x, self.y, z_new))
            raise Exception(f"当前坐标：({self.x}, {self.y}, {self.z})，向z轴{'正' if forward else '负'}方向移动时超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(self.x, self.y, z_new):
                obstacle_points.append(Point(self.x, self.y, z_new))
                raise Exception(f"当前坐标：({self.x}, {self.y}, {self.z})，向z轴{'正' if forward else '负'}方向移动时遇到障碍物")
            return OperationalPoint(self.x, self.y, z_new, g=g_new)

    def iterate_one_time(self):
        for if_forward in [True, False]:
            for method in self.iterate_funcs:
                try:
                    new_point = method(forward=if_forward)
                    computed_points.append(new_point)
                except Exception as e:
                    print(e)
                    continue

    # def compute_ghf(self) -> Point:
    #     self.g += 1
    #     self.h = int(abs(TERMINAL_POINT_X - self.x) + abs(TERMINAL_POINT_Y - self.y) + abs(TERMINAL_POINT_Z - self.z))
    #     self.z = self.g + self.h
    #     return Point(self.x, self.y, self.z, self.t, self.g)


# for x in range(TERMINAL_POINT_X):
#     for y in range(TERMINAL_POINT_Y):
#         for z in range(TERMINAL_POINT_Z):
#             if this_point_is_an_obstacle(x, y, z):
#                 obstacle_points.append(Point(x, y, z))

# 是否到达终点
REACH_THE_DESTINATION = False


def determine_best_point():
    global REACH_THE_DESTINATION
    if computed_points:
        best_point = computed_points[0]
        for computed_point in computed_points:
            if computed_point not in closed_points:
                if computed_point.f < best_point.f:
                    best_point = computed_point
                elif computed_point.f == best_point.f:
                    if computed_point.h < best_point.h:
                        best_point = computed_point

        if best_point.x == TERMINAL_POINT_X and best_point.y == TERMINAL_POINT_Y and best_point.z == TERMINAL_POINT_Z:
            REACH_THE_DESTINATION = True
        if best_point not in closed_points:
            closed_points.append(best_point)
        return best_point


def visualize():
    t_ls = []
    x_ls = []
    y_ls = []
    z_ls = []
    for closed_point in closed_points:
        t_ls.append(10 * closed_point.t + 1000)  # closed_point 的 t 额外 + 400
        x_ls.append(closed_point.x)
        y_ls.append(closed_point.y)
        z_ls.append(closed_point.z)
    # for computed_point in computed_points:
    #     if computed_point not in closed_points:
    #         t_ls.append(300)
    #         x_ls.append(computed_point.x)
    #         y_ls.append(computed_point.y)
    #         z_ls.append(computed_point.z)
    for obstacle_point in obstacle_points:
        t_ls.append(0)
        x_ls.append(obstacle_point.x)
        y_ls.append(obstacle_point.y)
        z_ls.append(obstacle_point.z)
    data = {"t": t_ls, "x": x_ls, "y": y_ls, "z": z_ls}
    my_frame = pd.DataFrame(data)

    fig = px.scatter_3d(my_frame, x='x', y='y', z='z', color='t')
    plotly.offline.plot(fig, filename=f"{1}.html")


if __name__ == '__main__':
    starting_point = OperationalPoint(STARTING_POINT_X, STARTING_POINT_Y, STARTING_POINT_Z)
    starting_point.iterate_one_time()

    while not REACH_THE_DESTINATION:
        best_point = determine_best_point()
        new_operational_point = OperationalPoint(best_point.x, best_point.y, best_point.z, best_point.g)
        new_operational_point.iterate_one_time()

    # print(closed_points)
    visualize()
