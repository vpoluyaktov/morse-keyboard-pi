import curses
from npyscreen import npysThemeManagers as ThemeManagers

class WhiteTheme(ThemeManagers.ThemeManager):
    _colors_to_define = (
        ('BLACK_WHITE', curses.COLOR_BLACK, curses.COLOR_WHITE),
        ('BLUE_BLACK', curses.COLOR_BLUE,curses.COLOR_BLACK),
        ('CYAN_BLACK', curses.COLOR_CYAN, curses.COLOR_BLACK),
        ('GREEN_BLACK', curses.COLOR_GREEN, curses.COLOR_BLACK),
        ('MAGENTA_BLACK', curses.COLOR_MAGENTA, curses.COLOR_BLACK),
        ('RED_BLACK', curses.COLOR_RED, curses.COLOR_BLACK),
        ('YELLOW_BLACK', curses.COLOR_YELLOW, curses.COLOR_BLACK),
        ('BLACK_RED', curses.COLOR_BLACK, curses.COLOR_RED),
        ('BLACK_GREEN', curses.COLOR_BLACK, curses.COLOR_GREEN),
        ('BLACK_YELLOW', curses.COLOR_BLACK, curses.COLOR_YELLOW),
        ('BLUE_WHITE', curses.COLOR_BLUE, curses.COLOR_WHITE),
        ('GREEN_WHITE', curses.COLOR_GREEN, curses.COLOR_WHITE),
        ('YELLOW_WHITE', curses.COLOR_YELLOW, curses.COLOR_WHITE),
        ('RED_WHITE', curses.COLOR_RED, curses.COLOR_WHITE),
    )

    default_colors = {
        'DEFAULT': 'BLACK_WHITE',
        'FORMDEFAULT': 'BLACK_WHITE',
        'NO_EDIT': 'BLACK_WHITE',
        'STANDOUT': 'BLUE_WHITE',
        'LABEL': 'BLACK_WHITE',
        'LABELBOLD': 'BLACK_WHITE',
        'CONTROL': 'BLACK_WHITE',
        'IMPORTANT': 'GREEN_WHITE',
        'SAFE': 'GREEN_WHITE',
        'WARNING': 'YELLOW_WHITE',
        'DANGER': 'RED_WHITE',
        'CRITICAL': 'RED_WHITE',
        'GOOD': 'GREEN_WHITE',
        'GOODHL': 'GREEN_WHITE',
        'VERYGOOD': 'BLACK_WHITE',
        'CAUTION': 'YELLOW_WHITE',
        'CAUTIONHL': 'BLACK_WHITE',
        }

