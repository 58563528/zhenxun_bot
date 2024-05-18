import random
from io import BytesIO
from pathlib import Path
from re import S

from pydantic import BaseModel
from strenum import StrEnum

from ._build_image import BuildImage


class MatType(StrEnum):

    LINE = "LINE"
    """折线图"""
    BAR = "BAR"
    """柱状图"""
    BARH = "BARH"
    """横向柱状图"""


class BuildMatData(BaseModel):

    mat_type: MatType
    """类型"""
    data: list[int | float] = []
    """数据"""
    x_name: str | None = None
    """X轴坐标名称"""
    y_name: str | None = None
    """Y轴坐标名称"""
    x_index: list[str] = []
    """显示轴坐标值"""
    y_index: list[int | float] = []
    """数据轴坐标值"""
    space: tuple[int, int] = (15, 15)
    """坐标值间隔(X, Y)"""
    rotate: tuple[int, int] = (0, 0)
    """坐标值旋转(X, Y)"""
    title: str | None = None
    """标题"""
    font: str = "msyh.ttf"
    """字体"""
    font_size: int = 15
    """字体大小"""
    display_num: bool = True
    """是否在点与柱状图顶部显示数值"""
    is_grid: bool = False
    """是否添加栅格"""
    background_color: tuple[int, int, int] | str = (255, 255, 255)
    """背景颜色"""
    background: Path | bytes | None = None
    """背景图片"""
    bar_color: list[str] = ["*"]
    """柱状图柱子颜色, 多个时随机, 使用 * 时七色随机"""
    padding: tuple[int, int] = (50, 50)
    """图表上下左右边距"""


class BuildMat:
    """
    针对 折线图/柱状图，基于 BuildImage 编写的 非常难用的 自定义画图工具
    目前仅支持 正整数
    """

    class InitGraph(BaseModel):

        mark_image: BuildImage
        """BuildImage"""
        x_height: int
        """横坐标高度"""
        x_point: list[int]
        """横坐标坐标"""
        graph_height: int
        """坐标轴高度"""

        class Config:
            arbitrary_types_allowed = True

    def __init__(self, mat_type: MatType) -> None:
        self.line_length = 760
        self._x_padding = 0
        self._y_padding = 0
        self.build_data = BuildMatData(mat_type=mat_type)

    @property
    def x_name(self) -> str | None:
        return self.build_data.x_name

    @x_name.setter
    def x_name(self, data: str) -> str | None:
        self.build_data.x_name = data

    @property
    def y_name(self) -> str | None:
        return self.build_data.y_name

    @y_name.setter
    def y_name(self, data: str) -> str | None:
        self.build_data.y_name = data

    @property
    def data(self) -> list[int | float]:
        return self.build_data.data

    @data.setter
    def data(self, data: list[int | float]):
        self._check_value(data, self.build_data.y_index)
        self.build_data.data = data

    @property
    def x_index(self) -> list[str]:
        return self.build_data.x_index

    @x_index.setter
    def x_index(self, data: list[str]):
        self.build_data.x_index = data

    @property
    def y_index(self) -> list[int | float]:
        return self.build_data.y_index

    @y_index.setter
    def y_index(self, data: list[int | float]):
        # self._check_value(self.build_data.data, data)
        data.sort()
        self.build_data.y_index = data

    @property
    def space(self) -> tuple[int, int]:
        return self.build_data.space

    @space.setter
    def space(self, data: tuple[int, int]):
        self.build_data.space = data

    @property
    def rotate(self) -> tuple[int, int]:
        return self.build_data.rotate

    @rotate.setter
    def rotate(self, data: tuple[int, int]):
        self.build_data.rotate = data

    @property
    def title(self) -> str | None:
        return self.build_data.title

    @title.setter
    def title(self, data: str):
        self.build_data.title = data

    @property
    def font(self) -> str:
        return self.build_data.font

    @font.setter
    def font(self, data: str):
        self.build_data.font = data

    # @property
    # def font_size(self) -> int:
    #     return self.build_data.font_size

    # @font_size.setter
    # def font_size(self, data: int):
    #     self.build_data.font_size = data

    @property
    def display_num(self) -> bool:
        return self.build_data.display_num

    @display_num.setter
    def display_num(self, data: bool):
        self.build_data.display_num = data

    @property
    def is_grid(self) -> bool:
        return self.build_data.is_grid

    @is_grid.setter
    def is_grid(self, data: bool):
        self.build_data.is_grid = data

    @property
    def background_color(self) -> tuple[int, int, int] | str:
        return self.build_data.background_color

    @background_color.setter
    def background_color(self, data: tuple[int, int, int] | str):
        self.build_data.background_color = data

    @property
    def background(self) -> Path | bytes | None:
        return self.build_data.background

    @background.setter
    def background(self, data: Path | bytes):
        self.build_data.background = data

    @property
    def bar_color(self) -> list[str]:
        return self.build_data.bar_color

    @bar_color.setter
    def bar_color(self, data: list[str]):
        self.build_data.bar_color = data

    def _check_value(
        self,
        y: list[int | float],
        y_index: list[int | float] | None = None,
        x_index: list[int | float] | None = None,
    ):
        """检查值合法性

        参数:
            y: 坐标值
            y_index: y轴坐标值
            x_index: x轴坐标值
        """
        if y_index:
            _value = x_index if self.build_data.mat_type == "barh" else y_index
            if not isinstance(y[0], str):
                __y = [float(t_y) for t_y in y]
                _y_index = [float(t_y) for t_y in y_index]
                if max(__y) > max(_y_index):
                    raise ValueError("坐标点的值必须小于y轴坐标的最大值...")
                i = -9999999999
                for _y in _y_index:
                    if _y > i:
                        i = _y
                    else:
                        raise ValueError("y轴坐标值必须有序...")

    async def build(self):
        """构造图片"""
        A = None
        bar_color = self.build_data.bar_color
        if "*" in bar_color:
            bar_color = [
                "#FF0000",
                "#FF7F00",
                "#FFFF00",
                "#00FF00",
                "#00FFFF",
                "#0000FF",
                "#8B00FF",
            ]
        init_graph = await self._init_graph()
        mark_image = None
        if self.build_data.mat_type == MatType.LINE:
            mark_image = await self._build_line_graph(init_graph, bar_color)
        if self.build_data.mat_type == MatType.BAR:
            pass
        if self.build_data.mat_type == MatType.BARH:
            pass
        if mark_image:
            padding_width, padding_height = self.build_data.padding
            width = mark_image.width + padding_width * 2
            height = mark_image.height + padding_height * 2
            if self.build_data.background:
                if isinstance(self.build_data.background, bytes):
                    A = BuildImage(
                        width, height, background=BytesIO(self.build_data.background)
                    )
                elif isinstance(self.build_data.background, Path):
                    A = BuildImage(width, height, background=self.build_data.background)
            else:
                A = BuildImage(width, height, self.build_data.background_color)
            if A:
                await A.paste(mark_image, (padding_width, padding_height))
                if self.build_data.title:
                    font = BuildImage.load_font(
                        self.build_data.font, self.build_data.font_size + 7
                    )
                    title_width, title_height = BuildImage.get_text_size(
                        self.build_data.title, font
                    )
                    pos = (
                        int(A.width / 2 - title_width / 2),
                        int(padding_height / 2 - title_height / 2),
                    )
                    await A.text(pos, self.build_data.title)
                if self.build_data.x_name:
                    font = BuildImage.load_font(
                        self.build_data.font, self.build_data.font_size + 4
                    )
                    title_width, title_height = BuildImage.get_text_size(
                        self.build_data.x_name, font  # type: ignore
                    )
                    pos = (
                        A.width - title_width - 20,
                        A.height - int(padding_height / 2 + title_height),
                    )
                    await A.text(pos, self.build_data.x_name)
        return A

    async def _init_graph(self) -> InitGraph:
        """构造初始化图表

        返回:
            InitGraph: InitGraph
        """
        padding_width = 0
        padding_height = 0
        font = BuildImage.load_font(self.build_data.font, self.build_data.font_size)
        width_list = []
        height_list = []
        for x in self.build_data.x_index:
            text_size = BuildImage.get_text_size(x, font)
            if text_size[1] > padding_height:
                padding_height = text_size[1]
            width_list.append(text_size[0])
        if not self.build_data.y_index:
            """没有指定y_index时，使用data自动生成"""
            max_num = max(self.build_data.data)
            s = int(max_num / 5)
            _y_index = [max_num]
            for _n in range(4):
                max_num -= s
                _y_index.append(max_num)
            _y_index.sort()
            self.build_data.y_index = _y_index
        for item in self.build_data.y_index:
            text_size = BuildImage.get_text_size(str(item), font)
            if text_size[0] > padding_width:
                padding_width = text_size[0]
            height_list.append(text_size[1])
        width = (
            sum([w + self.build_data.space[0] for w in width_list])
            + height_list[0]
            + self.build_data.space[0] * 2
            + 20
        )
        height = (
            sum([h + self.build_data.space[1] for h in height_list])
            + self.build_data.space[1] * 2
            + 30
        )
        if self.build_data.mat_type == MatType.BARH:
            """横向柱状图时xy轴长度调换"""
            _tmp = height
            height = width
            width = _tmp
        A = BuildImage(
            width,
            (height + 10),
            color=(255, 255, 255, 0),
        )
        padding_height += 5
        await A.line(
            (
                padding_width + 5,
                padding_height,
                padding_width + 5,
                height - padding_height,
            ),
            width=2,
        )
        await A.line(
            (
                padding_width + 5,
                height - padding_height,
                width - padding_width + 5,
                height - padding_height,
            ),
            width=2,
        )
        _x_index = self.build_data.x_index
        _y_index = self.build_data.y_index
        if self.build_data.mat_type == MatType.BARH:
            _tmp = _y_index
            _y_index = _x_index
            _x_index = _tmp
        cur_width = padding_width + self.build_data.space[0] * 2
        cur_height = height - height_list[0] - 5
        x_point = []
        for i, _x in enumerate(_x_index):
            """X轴数值"""
            grid_height = cur_height
            if self.build_data.is_grid:
                grid_height = padding_height
            await A.line((cur_width, cur_height - 1, cur_width, grid_height - 5))
            x_point.append(cur_width - 1)
            mid_point = cur_width - int(width_list[i] / 2)
            await A.text((mid_point, cur_height), str(_x), font=font)
            cur_width += width_list[i] + self.build_data.space[0]
        cur_width = padding_width
        cur_height = height - self.build_data.padding[1]
        for i, _y in enumerate(_y_index):
            """Y轴数值"""
            grid_width = cur_width
            if self.build_data.is_grid:
                grid_width = width - padding_width + 5
            await A.line((cur_width + 5, cur_height, grid_width + 11, cur_height))
            text_width = BuildImage.get_text_size(str(_y), font)[0]
            await A.text(
                (cur_width - text_width, cur_height - int(height_list[i] / 2) - 3),
                str(_y),
                font=font,
            )
            cur_height -= height_list[i] + self.build_data.space[1]
        graph_height = height - self.build_data.padding[1] - cur_height + 5
        return self.InitGraph(
            mark_image=A,
            x_height=height - height_list[0] - 5,
            graph_height=graph_height,
            x_point=x_point,
        )

    async def _build_line_graph(
        self, init_graph: InitGraph, bar_color: list[str]
    ) -> BuildImage:
        """构建折线图

        参数:
            init_graph: InitGraph
            bar_color: 颜色列表

        返回:
            BuildImage: 折线图
        """
        font = BuildImage.load_font(self.build_data.font, self.build_data.font_size)
        mark_image = init_graph.mark_image
        x_height = init_graph.x_height
        graph_height = init_graph.graph_height
        random_color = random.choice(bar_color)
        _black_point = BuildImage(11, 11, color=random_color)
        await _black_point.circle()
        max_num = max(self.y_index)
        point_list = []
        for x_p, y in zip(init_graph.x_point, self.build_data.data):
            """折线图标点"""
            y_height = int(y / max_num * init_graph.graph_height)
            await mark_image.paste(_black_point, (x_p, x_height - y_height))
            point_list.append((x_p + 4, x_height - y_height + 4))
        for i in range(len(point_list) - 1):
            """画线"""
            a_x, a_y = point_list[i]
            b_x, b_y = point_list[i + 1]
            await mark_image.line((a_x, a_y, b_x, b_y), random_color)
            if self.build_data.display_num:
                """显示数值"""
                value = self.build_data.data[i]
                text_size = BuildImage.get_text_size(str(value), font)
                await mark_image.text(
                    (a_x - int(text_size[0] / 2), a_y - text_size[1] - 5),
                    str(value),
                    font=font,
                )
        """最后一个数值显示"""
        value = self.build_data.data[-1]
        text_size = BuildImage.get_text_size(str(value), font)
        await mark_image.text(
            (
                point_list[-1][0] - int(text_size[0] / 2),
                point_list[-1][1] - text_size[1] - 5,
            ),
            str(value),
            font=font,
        )
        return mark_image

    async def _build_bar_graph(self):
        pass

    async def _build_barh_graph(self):
        pass
