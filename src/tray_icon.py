import pystray
from PIL import Image, ImageDraw

ICON_SIZE = 64
TRAY_TITLE = "电脑锁定"
MENU_SHOW = "显示主窗口"
MENU_QUIT = "退出"
ACCENT_RGB = (74, 158, 255, 255)


def menu_labels():
    return [MENU_SHOW, MENU_QUIT]


def build_icon_image(size=ICON_SIZE):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    margin = size // 8
    draw.rounded_rectangle(
        [margin, margin, size - margin, size - margin],
        radius=size // 6,
        fill=ACCENT_RGB,
    )
    draw.rounded_rectangle(
        [size * 5 // 16, size // 2 + 1, size * 11 // 16, size * 13 // 16],
        radius=4,
        fill="#ffffff",
    )
    draw.arc(
        [size * 3 // 8, size * 9 // 32, size * 5 // 8, size * 13 // 16],
        start=180, end=360, fill="#ffffff", width=max(2, size // 16),
    )
    return img


def make_handlers(actions):
    return {
        "show": lambda: actions.put("show"),
        "quit": lambda: actions.put("quit"),
    }


def create_icon(actions):
    handlers = make_handlers(actions)
    menu = pystray.Menu(
        pystray.MenuItem(MENU_SHOW, handlers["show"], default=True),
        pystray.MenuItem(MENU_QUIT, handlers["quit"]),
    )
    icon = pystray.Icon(TRAY_TITLE, build_icon_image(), TRAY_TITLE, menu)
    icon.on_click = lambda icon, button: handlers["show"]() if button == pystray.Button.LEFT else None
    return icon
