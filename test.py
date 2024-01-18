import tkinter as tk
from PIL import Image, ImageTk

root = tk.Tk()
root.title('oxxo.studio')
root.geometry('400x400')

img = Image.open('./out/mouse_track-2024-1-18-14-18-50.png')
tk_img = ImageTk.PhotoImage(img)

canvas = tk.Canvas(root, width=400, height=400)
canvas.create_image(0, 0, anchor='nw', image=tk_img)   # 在 Canvas 中放入圖片
canvas.pack()

root.mainloop()