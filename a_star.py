import random
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
TERMINAL_POINT_X = 60
TERMINAL_POINT_Y = 90
TERMINAL_POINT_Z = 80

# TODO: 维度是否为3维
IF_3D = False
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

# TODO: 路径模型，True:结果只显示最终结果，False:显示迭代过程
ROUTE_MODE = True


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
        if x == 70 and 20 <= y <= 70:
            OBSTACLE = True
    # 3d obstacle
    else:
        if y == x - 30:
            OBSTACLE = True
        if z == y - 30:
            OBSTACLE = True
        if x == z - 30:
            OBSTACLE = True
    return OBSTACLE


class Point:
    def __init__(self, x: int, y: int, z: int, g: int = 0, route=None, t: int = 0):
        if route is None:
            route = []
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

        # 到该点的路径
        self.route = route if route is not None else []

    def to_list(self):
        return [self.x, self.y, self.z]


# 以面来表示障碍物，点过多可能会导致图像加载失败
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
    def __init__(self, x: int, y: int, z: int, g: int = 0, route=None, t: int = 0):
        super(OperationalPoint, self).__init__(x, y, z, g, route, t)
        if IF_3D:
            self.iterate_funcs = [self.move_x, self.move_x_, self.move_y, self.move_y_, self.move_z, self.move_z_]
        else:
            self.iterate_funcs = [self.move_x, self.move_x_, self.move_y, self.move_y_]

    def move_x(self):
        x_new = self.x + 1
        if x_new > LENGTH or x_new < 0:
            # obstacle_points.append(Point(x_new, self.y, self.z))
            raise Exception(f"当前坐标：({x_new}, {self.y}, {self.z})，超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(x_new, self.y, self.z):
                # obstacle_points.append(Point(x_new, self.y, self.z))
                raise Exception(f"当前坐标：({x_new}, {self.y}, {self.z})，遇到障碍物")
            new_route = self.route[:]
            new_route.append([self.x, self.y, self.z])
            return Point(x_new, self.y, self.z, g=g_new, route=new_route)

    def move_x_(self):
        x_new = self.x - 1
        if x_new > LENGTH or x_new < 0:
            # obstacle_points.append(Point(x_new, self.y, self.z))
            raise Exception(f"当前坐标：({x_new}, {self.y}, {self.z})，超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(x_new, self.y, self.z):
                # obstacle_points.append(Point(x_new, self.y, self.z))
                raise Exception(f"当前坐标：({x_new}, {self.y}, {self.z})，遇到障碍物")
            new_route = self.route[:]
            new_route.append([self.x, self.y, self.z])
            return Point(x_new, self.y, self.z, g=g_new, route=new_route)

    def move_y(self):
        y_new = self.y + 1
        if y_new > WIDTH or y_new < 0:
            # obstacle_points.append(Point(self.x, y_new, self.z))
            raise Exception(f"当前坐标：({self.x}, {y_new}, {self.z})，超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(self.x, y_new, self.z):
                # obstacle_points.append(Point(self.x, y_new, self.z))
                raise Exception(f"当前坐标：({self.x}, {y_new}, {self.z})，遇到障碍物")
            new_route = self.route[:]
            new_route.append([self.x, self.y, self.z])
            return Point(self.x, y_new, self.z, g=g_new, route=new_route)

    def move_y_(self):
        y_new = self.y - 1
        if y_new > WIDTH or y_new < 0:
            # obstacle_points.append(Point(self.x, y_new, self.z))
            raise Exception(f"当前坐标：({self.x}, {y_new}, {self.z})，超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(self.x, y_new, self.z):
                # obstacle_points.append(Point(self.x, y_new, self.z))
                raise Exception(f"当前坐标：({self.x}, {y_new}, {self.z})，遇到障碍物")
            new_route = self.route[:]
            new_route.append([self.x, self.y, self.z])
            return Point(self.x, y_new, self.z, g=g_new, route=new_route)

    def move_z(self):
        z_new = self.z + 1
        if z_new > HEIGHT or z_new < 0:
            # obstacle_points.append(Point(self.x, self.y, z_new))
            raise Exception(f"当前坐标：({self.x}, {self.y}, {z_new})，超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(self.x, self.y, z_new):
                # obstacle_points.append(Point(self.x, self.y, z_new))
                raise Exception(f"当前坐标：({self.x}, {self.y}, {z_new})，遇到障碍物")
            new_route = self.route[:]
            new_route.append([self.x, self.y, self.z])
            return Point(self.x, self.y, z_new, g=g_new, route=new_route)

    def move_z_(self):
        z_new = self.z - 1
        if z_new > HEIGHT or z_new < 0:
            # obstacle_points.append(Point(self.x, self.y, z_new))
            raise Exception(f"当前坐标：({self.x}, {self.y}, {z_new})，超出边界")
        else:
            g_new = self.g + 1
            if this_point_is_an_obstacle(self.x, self.y, z_new):
                # obstacle_points.append(Point(self.x, self.y, z_new))
                raise Exception(f"当前坐标：({self.x}, {self.y}, {z_new})，遇到障碍物")
            new_route = self.route[:]
            new_route.append([self.x, self.y, self.z])
            return Point(self.x, self.y, z_new, g=g_new, route=new_route)

    def iterate_one_time(self):
        # print("当前选择了：" + str(self.to_list()) + "进行迭代")
        for method in self.iterate_funcs:
            try:
                new_point = method()
                # print("当前坐标：" + str(new_point.to_list()))
                if new_point.to_list() not in computed_points_lists:
                    computed_points_lists.append(new_point.to_list())
                    computed_points.append(new_point)
            except Exception as e:
                print(e)
                continue


def determine_best_point():
    global REACH_THE_DESTINATION
    if computed_points:
        best_point = computed_points[0]
        for i in range(len(computed_points)):
            if computed_points[i].to_list() not in closed_points_lists:
                best_point = computed_points[i]
                break
            elif i == len(computed_points) - 1:
                REACH_THE_DESTINATION = True
                print("未到达终点，但已遍历所有情况")
                return computed_points[0]

        for computed_point in computed_points:
            if computed_point.to_list() not in closed_points_lists:
                if computed_point.f < best_point.f:
                    best_point = computed_point
                elif computed_point.f == best_point.f:
                    if computed_point.h < best_point.h:
                        best_point = computed_point
                    elif computed_point.h == best_point.h:
                        if random.randint(0, 1):  # 此处引入随机数，如果h和f均相等，由随机数决定是否为best_point
                            best_point = computed_point
        if best_point.x == TERMINAL_POINT_X and best_point.y == TERMINAL_POINT_Y and best_point.z == TERMINAL_POINT_Z:
            REACH_THE_DESTINATION = True

        if best_point.to_list() not in closed_points_lists:
            if not REACH_THE_DESTINATION:
                closed_points_lists.append(best_point.to_list())
                computed_points.pop(computed_points.index(best_point))
        return best_point


def visualize():
    t_ls = []
    x_ls = []
    y_ls = []
    z_ls = []
    if not ROUTE_MODE:
        for closed_point in closed_points_lists:
            # t_ls.append(10 * closed_points_lists.index(closed_point) + 1000)
            t_ls.append(closed_points_lists.index(closed_point))
            x_ls.append(closed_point[0])
            y_ls.append(closed_point[1])
            z_ls.append(closed_point[2])
    else:
        best_point = determine_best_point()
        routes = best_point.route
        for i in range(len(routes)):
            t_ls.append(i + 100)
            x_ls.append(routes[i][0])
            y_ls.append(routes[i][1])
            z_ls.append(routes[i][2])
        t_ls.append(len(routes) + 100)
        x_ls.append(best_point.x)
        y_ls.append(best_point.y)
        z_ls.append(best_point.z)
    # for computed_point in computed_points:
    #     if computed_point.to_list() not in closed_points_lists:
    #         # t_ls.append(10 * computed_points_lists.index(computed_point) + 1000)
    #         t_ls.append(10 * computed_point.f + 1000)
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
    record_all_obstacle_on_the_map()

    starting_point = OperationalPoint(STARTING_POINT_X, STARTING_POINT_Y, STARTING_POINT_Z)
    closed_points_lists.append(starting_point.to_list())
    starting_point.iterate_one_time()

    while not REACH_THE_DESTINATION:
        best_point = determine_best_point()
        new_operational_point = OperationalPoint(best_point.x, best_point.y, best_point.z,
                                                 best_point.g, best_point.route)
        new_operational_point.iterate_one_time()

    # print(closed_points_lists)
    visualize()
