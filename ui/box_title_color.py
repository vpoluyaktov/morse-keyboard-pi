import npyscreen
import curses

class BoxTitleColor(npyscreen.BoxTitle):

    def update(self, clear=True):
        super(BoxTitleColor, self).update(clear=clear)

        HEIGHT = self.height - 1
        WIDTH  = self.width - 1
        box_attributes = self.parent.theme_manager.findPair(self, self.color)
        self.parent.curses_pad.attron(box_attributes)
        # draw box.
        self.parent.curses_pad.hline(self.rely, self.relx, curses.ACS_HLINE, WIDTH)
        self.parent.curses_pad.hline(self.rely + HEIGHT, self.relx, curses.ACS_HLINE, WIDTH)
        self.parent.curses_pad.vline(self.rely, self.relx, curses.ACS_VLINE, self.height)
        self.parent.curses_pad.vline(self.rely, self.relx+WIDTH, curses.ACS_VLINE, HEIGHT)
        
        # draw corners
        self.parent.curses_pad.addch(self.rely, self.relx, curses.ACS_ULCORNER, )
        self.parent.curses_pad.addch(self.rely, self.relx+WIDTH, curses.ACS_URCORNER, )
        self.parent.curses_pad.addch(self.rely+HEIGHT, self.relx, curses.ACS_LLCORNER, )
        self.parent.curses_pad.addch(self.rely+HEIGHT, self.relx+WIDTH, curses.ACS_LRCORNER, )
        self.parent.curses_pad.attroff(box_attributes)

        # draw title
        if self.name:
            if isinstance(self.name, bytes):
                name = self.name.decode(self.encoding, 'replace')
            else:
                name = self.name
            name = self.safe_string(name)
            name = " " + name + " "
            if isinstance(name, bytes):
                name = name.decode(self.encoding, 'replace')
            name_attributes = curses.A_NORMAL
            if self.do_colors() and not self.editing:
                name_attributes = name_attributes | self.parent.theme_manager.findPair(self, self.color) #| curses.A_BOLD
            elif self.editing:
                name_attributes = name_attributes | self.parent.theme_manager.findPair(self, 'HILIGHT')
            else:
                name_attributes = name_attributes #| curses.A_BOLD
            
            if self.editing:
                name_attributes = name_attributes | curses.A_BOLD
                
            self.add_line(self.rely, self.relx+4, name, 
                self.make_attributes_list(name, name_attributes), 
                self.width-8)
            # end draw title
            
            # draw footer
        if hasattr(self, 'footer') and self.footer:
            footer_text = self.footer
            if isinstance(footer_text, bytes):
                footer_text = footer_text.decode(self.encoding, 'replace')
            footer_text = self.safe_string(footer_text)
            footer_text = " " + footer_text + " "
            if isinstance(footer_text, bytes):
                footer_text = footer_text.decode(self.encoding, 'replace')
            
            footer_attributes = self.get_footer_attributes(footer_text)
            if len(footer_text) <= self.width - 4:
                placing = self.width - 4 - len(footer_text)
            else:
                placing = 4
        
            self.add_line(self.rely+HEIGHT, self.relx+placing, footer_text, 
                footer_attributes, 
                self.width-placing-2)
