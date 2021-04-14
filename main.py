import pandas as pd
import plotly
import plotly.express as px

from time import perf_counter
import random
from threading import Thread
import argparse


# TODO: 在此处设置障碍物的位置
def this_point_is_an_obstacle(x: int, y: int, z: int):
    OBSTACLE = False
    # 2d obstacle
    if not opt.use_3d:
        if x > 10 and abs(y - 50 + x) <= 2:
            OBSTACLE = True
        if x < 50 and abs(y - 60 + x) <= 2:
            OBSTACLE = True
        if x > 40 and abs(y - 70 + x) <= 2:
            OBSTACLE = True
        if abs(x - 50) <= 2 and y > 40:
            OBSTACLE = True
        if abs(x - 40) <= 2 and 30 <= y < 80:
            OBSTACLE = True
        if 60 <= x <= 70 and abs(y - 120 + x) <= 2:
            OBSTACLE = True
        if 50 <= x <= 70 and abs(y - 140 + x) <= 2:
            OBSTACLE = True
        if abs(x - 70) <= 2 and 50 <= y <= 70:
            OBSTACLE = True
    # 3d obstacle
    else:
        if abs(y - 40 + x) <= 2 and z < 60:
            OBSTACLE = True
        if abs(y - 60 + x) <= 2 and 60 <= z <= 90:
            OBSTACLE = True
        if abs(x + y + z - 160) <= 2 and 40 <= y <= 60 and 40 <= z <= 80:
            OBSTACLE = True
    return OBSTACLE


class Point:
    def __init__(self, x: int, y: int, z: int, g: int = 0, route=None, t: int = 0):
        self.x = x
        self.y = y
        self.z = z
        self.g = g  # g: 步数

        # h: 距离终点的Manhattan distance: h(n) = D ∗ (dx + dy + dz)
        if opt.use_3d:
            self.h = abs(opt.end_x - self.x) + abs(opt.end_y - self.y) + abs(opt.end_z - self.z)
        else:
            self.h = int(abs(opt.end_x - self.x) + abs(opt.end_y - self.y))

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
    for x in range(opt.map_x):
        for y in range(opt.map_y):
            if opt.use_3d:
                for z in range(opt.map_z):
                    if this_point_is_an_obstacle(x, y, z):
                        obstacle_points.append(Point(x, y, z))
            else:
                z = opt.start_z
                if this_point_is_an_obstacle(x, y, z):
                    obstacle_points.append(Point(x, y, z))


class OperationalPoint(Point):
    def move(self, axis: str):
        try:
            if "x" in axis:
                change = 1
                if "-x" in axis:
                    change = -1
                x_new = self.x + change
            else:
                x_new = self.x
            if "y" in axis:
                change = 1
                if "-y" in axis:
                    change = -1
                y_new = self.y + change
            else:
                y_new = self.y
            if "z" in axis:
                change = 1
                if "-z" in axis:
                    change = -1
                z_new = self.z + change
            else:
                z_new = self.z
            if x_new > opt.map_x or x_new < 0 or y_new > opt.map_y or y_new < 0 or z_new > opt.map_z or z_new < 0:
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
        if opt.use_3d:
            axis_list = ["x", "y", "z", "-x", "-y", "-z"]
            if opt.oblique:
                axis_list = ["x", "y", "z", "-x", "-y", "-z", 'xy', 'xz', 'yz', '-xy',
                             '-xz', '-yz', 'x-y', 'x-z', 'y-z', '-x-y', '-x-z', '-y-z',
                             "xyz", "-xyz", "x-yz", "xy-z", "-x-yz", "-xy-z", "x-y-z", "-x-y-z"]
        else:
            axis_list = ["x", "y", "-x", "-y"]
            if opt.oblique:
                axis_list = ["x", "y", "-x", "-y", 'xy', '-xy', 'x-y', '-x-y']
        for axis in axis_list:
            task = Thread(target=self.move, args=[axis])
            threads.append(task)
            task.start()
        threads[-1].join()


def determine_best_point():
    global REACH_THE_DESTINATION
    if computed_points:
        temp_best_point = None
        ALL_CLOSED = True
        for computed_point in computed_points:
            if not computed_point.close:
                ALL_CLOSED = False
                if temp_best_point is None:
                    temp_best_point = computed_point
                else:
                    if computed_point.to_list() not in closed_points_lists:
                        if computed_point.f < temp_best_point.f:
                            temp_best_point = computed_point
                        elif computed_point.f == temp_best_point.f:
                            if computed_point.h < temp_best_point.h:
                                temp_best_point = computed_point
                            elif computed_point.h == temp_best_point.h:
                                if random.randint(0, 1):  # 此处引入随机数，如果h和f均相等，由随机数决定是否为temp_best_point
                                    temp_best_point = computed_point
        if ALL_CLOSED:
            REACH_THE_DESTINATION = True
            print("未到达终点，但已遍历所有情况")
            return computed_points[0]
        if temp_best_point.x == opt.end_x:
            if temp_best_point.y == opt.end_y:
                if temp_best_point.z == opt.end_z:
                    REACH_THE_DESTINATION = True  # 到达终点
        if temp_best_point.to_list() not in closed_points_lists:
            if not REACH_THE_DESTINATION:
                closed_points_lists.append(temp_best_point.to_list())
                computed_points[computed_points.index(temp_best_point)].be_closed()
        return temp_best_point


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
        last_best_point = determine_best_point()
        routes = last_best_point.route
        for i in range(len(routes)):
            t_ls.append(i)
            x_ls.append(routes[i][0])
            y_ls.append(routes[i][1])
            z_ls.append(routes[i][2])
        t_ls.append(len(routes))
        x_ls.append(last_best_point.x)
        y_ls.append(last_best_point.y)
        z_ls.append(last_best_point.z)
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

    parser = argparse.ArgumentParser()
    parser.add_argument('--use-3d', action='store_true', help='维度是否为3维')
    parser.add_argument('--debug', action='store_true', help='调试模式，可查看障碍物&起点终点位置')
    parser.add_argument('--oblique', action='store_true', help='是否可以沿对角线方向移动 (单线/单层障碍物会被穿过，除非至少与两轴平行)')
    parser.add_argument('--map-x', nargs='?', type=int, default=100, metavar='int', help='地图长度')
    parser.add_argument('--map-y', nargs='?', type=int, default=100, metavar='int', help='地图宽度')
    parser.add_argument('--map-z', nargs='?', type=int, default=100, metavar='int', help='地图高度')
    parser.add_argument('--start-x', nargs='?', type=int, default=0, metavar='int', help='起点x轴坐标')
    parser.add_argument('--start-y', nargs='?', type=int, default=0, metavar='int', help='起点y轴坐标')
    parser.add_argument('--start-z', nargs='?', type=int, default=0, metavar='int', help='起点z轴坐标')
    parser.add_argument('--end-x', nargs='?', type=int, default=80, metavar='int', help='终点x轴坐标')
    parser.add_argument('--end-y', nargs='?', type=int, default=80, metavar='int', help='终点y轴坐标')
    parser.add_argument('--end-z', nargs='?', type=int, default=80, metavar='int', help='终点z轴坐标')
    opt = parser.parse_args()

    if not opt.use_3d and opt.start_z != opt.end_z:
        opt.end_z = opt.start_z
        print("2维模式下，起点和终点的Z轴坐标必须相同，已自动将终点位置的z轴坐标设为与起点相同")

    # TODO: 计算过的点将会添加到此处
    computed_points = []
    computed_points_lists = []
    closed_points_lists = []
    obstacle_points = []

    REACH_THE_DESTINATION = opt.debug
    if REACH_THE_DESTINATION:
        print("当前为调试模式，可查看障碍物&起点终点位置")
        closed_points_lists.append([opt.end_x, opt.end_y, opt.end_z])

    record_all_obstacle_on_the_map()

    starting_point = OperationalPoint(opt.start_x, opt.start_y, opt.start_z)
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
