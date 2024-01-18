
from PIL import Image, ImageDraw,ImageTk
import tkinter as tk
import datetime
import time,os
from pynput import mouse

Position = tuple[int, int]
Size = tuple[int, int]
Color = tuple[int, int, int, int]


class Colors:
    Left = (0, 255, 0, 100)
    Right = (255, 0, 0, 100)
    Middle = (255, 255, 0, 100)
    Move = (255, 255, 255, 50)


class Button(tk.Button):
    def __init__(self, *args, **kwarges):
        super(Button, self).__init__(*args, **kwarges)
        self.pack(pady=10)
        self["state"] = "normal"

    def switch(self):
        self["state"] = "disable" if self["state"] == "normal" else "normal"


class Checkbutton(tk.Checkbutton):
    def __init__(self, *args, **kwargs):
        super(Checkbutton, self).__init__(*args, **kwargs)
        self.pack(pady=2)

class ImageLable(tk.Label):
    def __init__(self,get_image:type(lambda : "a"), *args, **kwargs) -> None:
        super(ImageLable, self).__init__(*args, **kwargs)
        self.pack(pady=11)
        self.state = 1
        self.get_image=get_image
        print(self.get_image())

    
    def switch(self):
        self.state = not self.state

    def update_lable(self):
        """刷新隐藏状态"""
        if self.state:
            self.pack(pady=11)
        else:
            self.pack_forget()

    def update_image(self):
        """更新图片显示"""
        global image 
        image=self.get_image()
        self.config(image=image)
        self.after(10,self.update_image)



class ImageCache(object):
    def __init__(self, size: Size):
        """Image Cache"""
        self._size = size
        self._refresh()

    @property
    def cache(self):
        return self._cache

    def _refresh(self):
        self._cache = Image.new(
            "RGBA",
            self._size,
            (0, 0, 0, 255),
        )

    def get_image(self):
        """返回当前缓存的图像"""
        return ImageTk.PhotoImage(self.cache)

    def save(self, dirname="out", create_dir=True, clean=True):
        """
        Save the image
        Parameters:
        - dirname: the child dir name relative to the python file's parent dir for output
        - create_dir: whether to try creating or not
        - clean: whether to clean the cache or not
        """
        dir_path = os.path.join(os.path.dirname(__file__), dirname)
        if create_dir:
            os.makedirs(dir_path, exist_ok=True)
        elif not os.path.exists(dir_path):
            raise FileNotFoundError

        now = datetime.datetime.now()
        file_path = os.path.join(
            dir_path,
            f"mouse_track-{now.year}-{now.month}-{now.day}-{now.hour}-{now.minute}-{now.second}.png",
        )
        self.cache.save(file_path)

        if clean:
            self._refresh()
        print(f"轨迹图像已保存: {file_path}")

    def line(self, start: Position, end: Position, color=Colors.Move):
        """
        Draw a line
        Parameters:
        - start: tuple of the line's start
        - end: tuple of the line's end
        """
        self._draw_transp_line(xy=[start, end], fill=color, width=2)

    def ellipse(self, x, y, color: Color, radius=10):
        """
        Draw a point at `(x, y)`
        :param x:
        :param y:
        :param color: 注意：有四个值，最后一个值的不透明度最大值是255，不是float的0~1
        :param radius:
        :return: None
        """
        self._draw_transparent_ellipse(
            [(x - radius, y - radius), (x + radius, y + radius)],
            fill=color,
        )

    def _draw_transp_line(self, xy, **kwargs):
        """
        Draws a line inside the given bounding box onto given image.
        Supports transparent colors
        """
        transp = Image.new("RGBA", self._size, (0, 0, 0, 0))  # Temp drawing image.
        draw = ImageDraw.Draw(transp, "RGBA")
        draw.line(xy, **kwargs)
        # Alpha composite two images together and replace first with result.
        self._cache.paste(Image.alpha_composite(self._cache, transp))

    def _draw_transparent_ellipse(self, xy, **kwargs):
        """
        Draws an ellipse inside the given bounding box onto given image.
        Supports transparent colors
        https://stackoverflow.com/a/54426778
        """
        transp = Image.new("RGBA", self._size, (0, 0, 0, 0))  # Temp drawing image.
        draw = ImageDraw.Draw(transp, "RGBA")
        draw.ellipse(xy, **kwargs)
        # Alpha composite two images together and replace first with result.
        self._cache.paste(Image.alpha_composite(self._cache, transp))

class MoveTracker(tk.BooleanVar):
    def __init__(self, cache: ImageCache, interval: float=0.0):
        """A tracker that maintains a state of whether it should track or not
        
        Args:
            cache (ImageCache): An ImageCache object for caching images.
            interval (float): The time interval (in seconds) for capturing mouse movements.
        """
        super(MoveTracker, self).__init__(value=True)
        self.position = None
        self.cache = cache
        self.interval = interval
        self.last_capture_time = time.time()

    def track(self, x: int, y: int):
        if self.get() and time.time() - self.last_capture_time >= self.interval:
            position = (x, y)
            if self.position:
                # print(f"move to ({x}, {y})")
                self.cache.line(start=self.position, end=position)
            self.position = position
            self.last_capture_time = time.time()


class ClickTracker(tk.BooleanVar):
    def __init__(self, cache: ImageCache, color: Color):
        """A tracker that maintains a state of whether it should track or not"""
        super(ClickTracker, self).__init__(value=True)
        self.color = color
        self.cache = cache

    def track(self, x: int, y: int):
        if self.get():
            # print(f"click at ({x}, {y})")
            self.cache.ellipse(x, y, color=self.color)


class Trackers(mouse.Listener):
    def __init__(
        self,
        click_trackers: dict[mouse.Button, ClickTracker],
        move_tracker: MoveTracker,
    ):
        """
        Implemented by pynput.mouse
        The `mouse.Listener` will create a thread.
        """
        self.click_trackers = click_trackers
        self.move_tracker = move_tracker

    def reset(self):
        """Reset the mouse listener"""
        super(Trackers, self).__init__(
            on_move=self.move_tracker.track, on_click=self.on_click
        )

    def on_click(self, x, y, button, pressed):
        """Pick the right tracker and track"""
        if pressed:
            self.click_trackers[button].track(x, y)


class App(tk.Tk):
    def __init__(self):
        super(App, self).__init__()

        self.title("Mouse Tracker")
        self.geometry("400x400")

        self.start_button = Button(self, text="开始记录", command=self.start_tracking)
        self.stop_button = Button(self, text="停止记录", command=self.stop_tracking)
        self.stop_button.switch()

        self.cache = ImageCache(
            size=(self.winfo_screenwidth(), self.winfo_screenheight())
        )
        #self.canvas = tk.Canvas(self,width=400, height=400)  # Label组件用于显示图片
        self.image_lable = ImageLable(get_image=self.cache.get_image,master=self)
        self.trackers = Trackers(
            click_trackers={
                mouse.Button.left: ClickTracker(cache=self.cache, color=Colors.Left),
                mouse.Button.right: ClickTracker(cache=self.cache, color=Colors.Right),
                mouse.Button.middle: ClickTracker(
                    cache=self.cache, color=Colors.Middle
                ),
            },
            move_tracker=MoveTracker(self.cache),
        )

        self.check_buttons = [
            Checkbutton(self, text=text, variable=tracker)
            for text, tracker in zip(
                ["记录左键点击位置", "记录右键点击位置", "记录中键点击位置", "记录鼠标移动轨迹"],
                [*self.trackers.click_trackers.values(), self.trackers.move_tracker],
            )
        ]

    def start_tracking(self):
        """点击开始记录"""
        self.start_button.switch()
        self.stop_button.switch()
        self.trackers.reset()
        self.trackers.start()
        self.image_lable.update_image()  # 开始记录时更新图片显示

    def stop_tracking(self):
        """点击结束记录"""
        self.stop_button.switch()
        self.start_button.switch()
        self.cache.save()
        self.trackers.stop()

    


def main():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
