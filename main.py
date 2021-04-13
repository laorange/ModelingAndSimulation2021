from time import perf_counter
import random
from threading import Thread
import pandas as pd
import plotly
import plotly.express as px

# TODO: 地图大小
LENGTH = 100
WIDTH = 100
HEIGHT = 100

# TODO: 起点位置 的 x,y,z坐标
STARTING_POINT_X = 0
STARTING_POINT_Y = 0
STARTING_POINT_Z = 0

# TODO: 终点位置 的 x,y,z坐标
TERMINAL_POINT_X = 80  # 10  # 10  # 66  # 45  # 66  # 35  # 60
TERMINAL_POINT_Y = 80  # 90  # 90  # 56  # 60  # 56  # 20  # 90
TERMINAL_POINT_Z = 80

# TODO: 维度是否为3维
IF_3D = True

if not IF_3D and STARTING_POINT_Z != TERMINAL_POINT_Z:
    TERMINAL_POINT_Z = STARTING_POINT_Z
    print("2维模式下，起点和终点的Z轴坐标必须相同，已自动将终点位置的z轴坐标设为与起点相同")

# TODO: 计算过的点将会添加到此处
computed_points = []
computed_points_lists = []
closed_points_lists = []
obstacle_points = []

# TODO: 是否已到达终点 (提示：可以先设置该项为True来查看障碍物的形状)
REACH_THE_DESTINATION = False
if REACH_THE_DESTINATION:
    print("当前为障碍物调试模式，如需开始计算请将REACH_THE_DESTINATION设为False")
    closed_points_lists.append([TERMINAL_POINT_X, TERMINAL_POINT_Y, TERMINAL_POINT_Z])


# TODO: 在此处设置障碍物的位置
def this_point_is_an_obstacle(x: int, y: int, z: int):
    OBSTACLE = False
    # 2d obstacle
    if not IF_3D:
        if x > 10 and y == 50 - x:
            OBSTACLE = True
        if x < 50 and y == 60 - x:
            OBSTACLE = True
        if x > 40 and y == 70 - x:
            OBSTACLE = True
        if x == 50 and y > 40:
            OBSTACLE = True
        if x == 40 and 30 <= y < 80:
            OBSTACLE = True
        if 60 <= x <= 70 and y == 120 - x:
            OBSTACLE = True
        if 50 <= x <= 70 and y == 140 - x:
            OBSTACLE = True
        if x == 70 and 50 <= y <= 70:
            OBSTACLE = True
    # 3d obstacle
    else:
        if y == 20 - x and z < 60:
            OBSTACLE = True
        if y == 60 - x and 70 <= z <= 90:
            OBSTACLE = True
        if x + y + z == 160 and 40 <= x <= 60 and 40 <= y <= 60 and 40 <= z <= 80:
            OBSTACLE = True
    return OBSTACLE


class Point:
    def __init__(self, x: int, y: int, z: int, g: int = 0, route=None, t: int = 0):
        self.x = x
        self.y = y
        self.z = z
        self.g = g  # g: 步数

        # h: 距离终点的Manhattan distance: h(n) = D ∗ (dx + dy + dz)
        if IF_3D:
            self.h = abs(TERMINAL_POINT_X - self.x) + abs(TERMINAL_POINT_Y - self.y) + abs(TERMINAL_POINT_Z - self.z)
        else:
            self.h = int(abs(TERMINAL_POINT_X - self.x) + abs(TERMINAL_POINT_Y - self.y))

        self.f = self.g + self.h

        self.t = g if t == 0 else t  # t: 默认值为g, 数值越大颜色越鲜艳

        self.route = route if route is not None else []  # 从终点到该点的路径

        self.close = False  # 是否close

    def to_list(self):
        return [self.x, self.y, self.z]

    def be_closed(self):
        self.close = True


# 在图中画出障碍物(点过多可能会导致图像加载失败)
def record_all_obstacle_on_the_map():
    global obstacle_points
    for x in range(LENGTH):
        for y in range(WIDTH):
            if IF_3D:
                for z in range(HEIGHT):
                    if this_point_is_an_obstacle(x, y, z):
                        obstacle_points.append(Point(x, y, z))
            else:
                z = STARTING_POINT_Z
                if this_point_is_an_obstacle(x, y, z):
                    obstacle_points.append(Point(x, y, z))


class OperationalPoint(Point):
    def move(self, axis: str, forward: bool = True):
        try:
            change = 1 if forward else -1
            x_new = self.x + change if axis == "x" else self.x
            y_new = self.y + change if axis == "y" else self.y
            z_new = self.z + change if axis == "z" else self.z
            if x_new > LENGTH or x_new < 0 or y_new > WIDTH or y_new < 0 or z_new > HEIGHT or z_new < 0:
                raise Exception(f"当前坐标：({x_new}, {y_new}, {z_new})，超出边界")
            else:
                g_new = self.g + 1
                if this_point_is_an_obstacle(x_new, y_new, z_new):
                    raise Exception(f"当前坐标：({x_new}, {y_new}, {z_new})，遇到障碍物")
                new_route = self.route[:]
                new_route.append([self.x, self.y, self.z])
                new_point = Point(x_new, y_new, z_new, g=g_new, route=new_route)
                if new_point.to_list() not in computed_points_lists:
                    computed_points_lists.append(new_point.to_list())
                    computed_points.append(new_point)
                else:
                    new_point_index = computed_points_lists.index(new_point.to_list())
                    if computed_points[new_point_index].f > new_point.f:
                        computed_points[new_point_index] = new_point
        except Exception as e:
            pass  # print(e)

    def iterate_one_time(self):
        threads = []
        if IF_3D:
            axis_list = ["x", "y", "z"]
        else:
            axis_list = ["x", "y"]
        for axis in axis_list:
            for forward in [True, False]:
                task = Thread(target=self.move, args=[axis, forward])
                threads.append(task)
                task.start()
        threads[-1].join()


def determine_best_point():
    global REACH_THE_DESTINATION
    if computed_points:
        best_point = None
        ALL_CLOSED = True
        for computed_point in computed_points:
            if not computed_point.close:
                ALL_CLOSED = False
                if best_point is None:
                    best_point = computed_point
                else:
                    if computed_point.to_list() not in closed_points_lists:
                        if computed_point.f < best_point.f:
                            best_point = computed_point
                        elif computed_point.f == best_point.f:
                            if computed_point.h < best_point.h:
                                best_point = computed_point
                            elif computed_point.h == best_point.h:
                                if random.randint(0, 1):  # 此处引入随机数，如果h和f均相等，由随机数决定是否为best_point
                                    best_point = computed_point
        if ALL_CLOSED:
            REACH_THE_DESTINATION = True
            print("未到达终点，但已遍历所有情况")
            return computed_points[0]
        if best_point.x == TERMINAL_POINT_X and best_point.y == TERMINAL_POINT_Y and best_point.z == TERMINAL_POINT_Z:
            REACH_THE_DESTINATION = True  # 到达终点
        if best_point.to_list() not in closed_points_lists:
            if not REACH_THE_DESTINATION:
                closed_points_lists.append(best_point.to_list())
                computed_points[computed_points.index(best_point)].be_closed()
        return best_point


# 使用plotly进行可视化
def visualize(route_mode: bool = True):
    t_ls = []
    x_ls = []
    y_ls = []
    z_ls = []
    if not route_mode:
        for closed_point in closed_points_lists:
            t_ls.append(closed_points_lists.index(closed_point))
            x_ls.append(closed_point[0])
            y_ls.append(closed_point[1])
            z_ls.append(closed_point[2])
    else:
        best_point = determine_best_point()
        routes = best_point.route
        for i in range(len(routes)):
            t_ls.append(i)
            x_ls.append(routes[i][0])
            y_ls.append(routes[i][1])
            z_ls.append(routes[i][2])
        t_ls.append(len(routes))
        x_ls.append(best_point.x)
        y_ls.append(best_point.y)
        z_ls.append(best_point.z)
    # 画计算到的点，调试用
    # for computed_point in computed_points:
    #     if computed_point.to_list() not in closed_points_lists:
    #         # t_ls.append(10 * computed_points_lists.index(computed_point) + 1000)
    #         t_ls.append(10 * computed_point.f + 1000)
    #         x_ls.append(computed_point.x)
    #         y_ls.append(computed_point.y)
    #         z_ls.append(computed_point.z)
    for obstacle_point in obstacle_points:
        t_ls.append(-100)
        x_ls.append(obstacle_point.x)
        y_ls.append(obstacle_point.y)
        z_ls.append(obstacle_point.z)

    data = {"t": t_ls, "x": x_ls, "y": y_ls, "z": z_ls}
    my_frame = pd.DataFrame(data)

    fig = px.scatter_3d(my_frame, x='x', y='y', z='z', color='t')
    plotly.offline.plot(fig, filename=f"{'result_route' if route_mode else 'result_scan'}.html")


if __name__ == '__main__':
    start_time = perf_counter()
    record_all_obstacle_on_the_map()

    starting_point = OperationalPoint(STARTING_POINT_X, STARTING_POINT_Y, STARTING_POINT_Z)
    initial_h = starting_point.h
    starting_point.be_closed()
    computed_points_lists.append(starting_point.to_list())
    computed_points.append(starting_point)
    closed_points_lists.append(starting_point.to_list())
    starting_point.iterate_one_time()

    while not REACH_THE_DESTINATION:
        best_point = determine_best_point()
        new_operational_point = OperationalPoint(best_point.x, best_point.y, best_point.z,
                                                 best_point.g, best_point.route)
        progress = 1 - new_operational_point.h / starting_point.h
        print("\r当前位置({}, {}, {})，有效路程 ÷ 始末点距离: {:.2f}%".format(new_operational_point.x,
                                                                new_operational_point.y,
                                                                new_operational_point.z,
                                                                100 * progress), end='')
        new_operational_point.iterate_one_time()

    print("\n用时: {:.2f}秒".format(perf_counter() - start_time))

    visualize(route_mode=True)
    visualize(route_mode=False)
