import curses
from npyscreen import npysThemeManagers as ThemeManagers

class BlueTheme(ThemeManagers.ThemeManager):
    _colors_to_define = (
        ('WHITE_BLUE', curses.COLOR_WHITE, curses.COLOR_BLUE),
        ('BLUE_WHITE', curses.COLOR_BLUE, curses.COLOR_WHITE),
        ('BLACK_BLUE', curses.COLOR_BLACK,curses.COLOR_BLUE),
        ('CYAN_BLUE', curses.COLOR_CYAN, curses.COLOR_BLUE),
        ('GREEN_BLUE', curses.COLOR_GREEN, curses.COLOR_BLUE),
        ('MAGENTA_BLUE', curses.COLOR_MAGENTA, curses.COLOR_BLUE),
        ('RED_BLUE', curses.COLOR_RED, curses.COLOR_BLUE),
        ('YELLOW_BLUE', curses.COLOR_YELLOW, curses.COLOR_BLUE),
        ('YELLOW_WHITE', curses.COLOR_YELLOW, curses.COLOR_WHITE),
        ('BLACK_RED', curses.COLOR_BLACK, curses.COLOR_RED),
        ('BLACK_GREEN', curses.COLOR_BLACK, curses.COLOR_GREEN),
        ('BLACK_YELLOW', curses.COLOR_BLACK, curses.COLOR_YELLOW),
    )

    default_colors = {
        'DEFAULT': 'WHITE_BLUE',
        'FORMDEFAULT': 'WHITE_BLUE',
        'NO_EDIT': 'RED_BLUE',
        'STANDOUT': 'CYAN_BLUE',
        'CURSOR': 'WHITE_BLUE',
        'CURSOR_INVERSE': 'BLUE_WHITE',
        'LABEL': 'WHITE_BLUE',
        'LABELBOLD': 'YELLOW_BLUE',
        'CONTROL': 'YELLOW_BLUE',
        'IMPORTANT': 'RED_BLUE',
        'SAFE': 'GREEN_BLUE',
        'WARNING': 'YELLOW_BLUE',
        'DANGER': 'RED_BLUE',
        'CRITICAL': 'RED_BLUE',
        'GOOD': 'GREEN_BLUE',
        'GOODHL': 'GREEN_BLUE',
        'VERYGOOD': 'WHITE_BLUE',
        'CAUTION': 'YELLOW_BLUE',
        'CAUTIONHL': 'WHITE_BLUE',
        'HILIGHT': 'YELLOW_BLUE'
        }
