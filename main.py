from random import randint
from time import perf_counter
from threading import Thread
import argparse
from pandas import DataFrame
import plotly
import plotly.express as px

# 全局变量
computed_points = []
computed_points_lists = []
computed_points_f = []
closed_points_lists = []
obstacle_points = []
exceptions = []  # 该列表记录遇障情况，默认不输出


# TODO: 在此处设置障碍物的位置
def this_point_is_an_obstacle(x: int, y: int, z: int):
    OBSTACLE = False
    # TODO: ↓ 在下方定义 2d 的障碍
    if not opt.use_3d:
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
    # TODO: ↓ 在下方定义 3d 的障碍
    else:
        if x == 20 and z < 30:
            OBSTACLE = True
        if z == 50 and y < 60:
            OBSTACLE = True
        if y == 80 and x < 60:
            OBSTACLE = True
        if x == 50 and 20 < y < 80 and z > 20:
            OBSTACLE = True
    return OBSTACLE


class Point:
    def __init__(self, x: int, y: int, z: int, g: float or int = 0.0, route_input=None, t: int = 0):
        self.x = x
        self.y = y
        self.z = z
        self.g = g  # g: 步数

        if opt.use_3d:  # h 到终点的距离
            self.h = abs(opt.end_x - self.x) + abs(opt.end_y - self.y) + abs(opt.end_z - self.z)
            if not opt.straight:
                self.h = ((opt.end_x - self.x) ** 2 + (opt.end_y - self.y) ** 2 + (opt.end_z - self.z) ** 2) ** 0.5
        else:
            self.h = int(abs(opt.end_x - self.x) + abs(opt.end_y - self.y))
            if not opt.straight:
                self.h = ((opt.end_x - self.x) ** 2 + (opt.end_y - self.y) ** 2) ** 0.5

        self.f = self.g + 1.5 * self.h  # 提高h的占比，使得在原本f相同时，取h小的点
        self.t = g if t == 0 else t  # t: 默认值为g, 数值越大颜色越鲜艳
        self.route = route_input if route_input is not None else []  # 从终点到该点的路径
        self.close = False  # 是否close

    def to_list(self):
        return [self.x, self.y, self.z]

    def be_closed(self):
        self.close = True


# 在图中画出障碍物
def record_all_obstacle_on_the_map():
    global obstacle_points
    for x in range(opt.map_x + 1):
        for y in range(opt.map_y + 1):
            if opt.use_3d:
                for z in range(opt.map_z + 1):
                    if this_point_is_an_obstacle(x, y, z):
                        obstacle_points.append([x, y, z])
            else:
                z = opt.start_z
                if this_point_is_an_obstacle(x, y, z):
                    obstacle_points.append([x, y, z])
    if not opt.use_3d:  # 2维图画出边界
        for x in range(- 1, opt.map_x + 2):
            obstacle_points.append([x, -1, opt.start_z])
            obstacle_points.append([x, opt.map_y + 1, opt.start_z])
        for y in range(0, opt.map_y + 1):
            obstacle_points.append([-1, y, opt.start_z])
            obstacle_points.append([opt.map_x + 1, y, opt.start_z])


class OperationalPoint(Point):
    def move(self, axis: str):
        try:
            distance = 0
            new_coordinate = {'x': self.x, 'y': self.y, 'z': self.z}
            for axis_name in ['x', 'y', 'z']:
                from_where = {'x': self.x, 'y': self.y, 'z': self.z}
                if axis_name in axis:
                    change = -1 if ("-" + axis_name) in axis else 1
                    new_coordinate[axis_name] += change
                    from_where[axis_name] += change
                    if not this_point_is_an_obstacle(from_where['x'], from_where['y'], from_where['z']):
                        distance += 1
                    else:
                        raise Exception(f"({from_where['x']}, {from_where['y']}, {from_where['z']})，遇到障碍物")
            if new_coordinate['x'] > opt.map_x or new_coordinate['x'] < 0 or new_coordinate['y'] > opt.map_y or \
                    new_coordinate['y'] < 0 or new_coordinate['z'] > opt.map_z or new_coordinate['z'] < 0:
                raise Exception(f"({new_coordinate['x']}, {new_coordinate['y']}, {new_coordinate['z']})，超出边界")
            else:
                g_new = self.g + distance ** 0.5
                if this_point_is_an_obstacle(new_coordinate['x'], new_coordinate['y'], new_coordinate['z']):
                    raise Exception(f"({new_coordinate['x']}, {new_coordinate['y']}, {new_coordinate['z']})，遇到障碍物")
                new_route = self.route[:]
                new_route.append([self.x, self.y, self.z])
                new_point = Point(new_coordinate['x'], new_coordinate['y'], new_coordinate['z'], g_new, new_route)
                if new_point.to_list() not in computed_points_lists:
                    computed_points_lists.append(new_point.to_list())
                    computed_points.append(new_point)
                    computed_points_f.append(new_point.f)
                else:
                    new_point_index = computed_points_lists.index(new_point.to_list())
                    if computed_points[new_point_index].g > new_point.g:
                        computed_points[new_point_index] = new_point
                        computed_points_f[new_point_index] = new_point.f
                        if new_point.to_list() in closed_points_lists:
                            closed_points_lists.remove(new_point.to_list())
        except Exception as e:
            exceptions.append(e)  # 添加遇障信息

    def iterate_one_time(self):
        threads = []
        if opt.use_3d:  # 3d 情况
            axis_list = ["x", "y", "z", "-x", "-y", "-z"]
            if not opt.straight:
                axis_list = ["x", "y", "z", "-x", "-y", "-z", 'xy', 'xz', 'yz', '-xy',
                             '-xz', '-yz', 'x-y', 'x-z', 'y-z', '-x-y', '-x-z', '-y-z',
                             "xyz", "-xyz", "x-yz", "xy-z", "-x-yz", "-xy-z", "x-y-z", "-x-y-z"]
        else:  # 2d 情况
            axis_list = ["x", "y", "-x", "-y"]
            if not opt.straight:
                axis_list = ["x", "y", "-x", "-y", 'xy', '-xy', 'x-y', '-x-y']
        while axis_list:
            axis = axis_list.pop(randint(0, len(axis_list) - 1))
            task = Thread(target=self.move, args=[axis])  # 多线程加速计算
            threads.append(task)
            task.start()
        threads[-1].join()


def determine_best_point() -> Point:
    global REACH_THE_DESTINATION
    MAX_DISTANCE_ON_THE_MAP = (opt.map_x + opt.map_y + opt.map_z) * 10
    if computed_points:
        min_f = min(computed_points_f[::-1])
        ALL_CLOSED = False if min_f <= MAX_DISTANCE_ON_THE_MAP else True
        index_min_f = len(computed_points_f) - computed_points_f[::-1].index(min_f) - 1
        temp_best_point = computed_points[index_min_f]
        if ALL_CLOSED:
            REACH_THE_DESTINATION = True
            print("未到达终点，但已遍历所有情况")
            final_point = temp_best_point
            return final_point
        if temp_best_point.x == opt.end_x:
            if temp_best_point.y == opt.end_y:
                if temp_best_point.z == opt.end_z:
                    REACH_THE_DESTINATION = True  # 到达终点
        if temp_best_point.to_list() not in closed_points_lists:
            assert not temp_best_point.close
            if not REACH_THE_DESTINATION:
                closed_points_lists.append(temp_best_point.to_list())
                computed_points[index_min_f].be_closed()
                computed_points_f[index_min_f] += MAX_DISTANCE_ON_THE_MAP
        else:
            REACH_THE_DESTINATION = True
            print("未到达终点，但出错了")
        return temp_best_point


# 使用plotly进行可视化
def visualize(route_mode: bool, last_point: Point):
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
        last_best_point = last_point
        routes = last_best_point.route
        if routes:
            for i in range(len(routes)):
                t_ls.append(i)
                x_ls.append(routes[i][0])
                y_ls.append(routes[i][1])
                z_ls.append(routes[i][2])
            t_ls.append(len(routes))
            x_ls.append(last_best_point.x)
            y_ls.append(last_best_point.y)
            z_ls.append(last_best_point.z)
    for obstacle_point in obstacle_points:
        t_ls.append(-100)
        x_ls.append(obstacle_point[0])
        y_ls.append(obstacle_point[1])
        z_ls.append(obstacle_point[2])

    data = DataFrame({'x': x_ls, 'y': y_ls, 'z': z_ls, 'step': t_ls})
    fig = px.scatter_3d(data, x='x', y='y', z='z', color='step')
    plotly.offline.plot(fig, filename=f"{'result_route' if route_mode else 'result_scan'}.html")


def prepare_before_iterate(start_point: OperationalPoint):
    computed_points_lists.append(start_point.to_list())
    computed_points.append(start_point)
    computed_points_f.append(start_point.f)


if __name__ == '__main__':
    start_time = perf_counter()  # 记录开始时间

    parser = argparse.ArgumentParser()
    parser.add_argument('--use-3d', action='store_true', help='维度是否为3维')
    parser.add_argument('--debug', action='store_true', help='调试模式，可查看障碍物&起点终点位置')
    parser.add_argument('--straight', action='store_true', help='是否按直线行进（即不能沿对角线方向移动）')
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

    REACH_THE_DESTINATION = opt.debug
    if REACH_THE_DESTINATION:
        print("当前为调试模式，可查看障碍物&起点终点位置")
        closed_points_lists.append([opt.start_x, opt.start_y, opt.start_z])
        closed_points_lists.append([opt.end_x, opt.end_y, opt.end_z])

    record_all_obstacle_on_the_map()

    best_point = OperationalPoint(opt.start_x, opt.start_y, opt.start_z)  # 初始点
    starting_h = best_point.h
    if not opt.debug:
        prepare_before_iterate(start_point=best_point)

    while not REACH_THE_DESTINATION:
        best_point = determine_best_point()
        new_operational_point = OperationalPoint(best_point.x, best_point.y, best_point.z,
                                                 best_point.g, best_point.route)
        progress = 1 - new_operational_point.h / starting_h
        print("\r当前位置({}, {}, {})，有效路程 ÷ 始末点距离: {:.2f}%".format(new_operational_point.x,
                                                                new_operational_point.y,
                                                                new_operational_point.z,
                                                                100 * progress), end='')
        new_operational_point.iterate_one_time()

    route = best_point.route
    print("\n用时: {:.4f}秒".format(perf_counter() - start_time))

    if not opt.debug:
        visualize(last_point=best_point, route_mode=True)
    visualize(last_point=best_point, route_mode=False)
    input('\n请敲击回车来结束程序:')
