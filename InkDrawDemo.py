# -*- coding: utf-8 -*-

#   This file is part of emesene.
#
#    Emesene is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    emesene is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with emesene; if not, write to the Free Software
#    Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import gtk
import gtk.gdk
import Theme
import InkDraw
import time

# Ink draw demo written by alencool

class InkDrawDemo(gtk.Window):
    def __init__(self, theme):
        gtk.Window.__init__(self)
        self.set_size_request(-1, 200)
        ### Drawing Area
        self._inkcanvas = InkDraw.InkCanvas( \
            pointer_pixbuf= theme.getImage('cursor-mouse'), 
            paintbrush_pixbuf= theme.getImage('tool-paintbrush'), 
            erasor_pixbuf= theme.getImage('tool-eraser') )

        ### paint button
        paint_image = gtk.Image()
        paint_image.set_from_pixbuf(theme.getImage('paintbrush'))
        paint_button = gtk.RadioToolButton()
        paint_button.set_icon_widget(paint_image)
        paint_button.connect('clicked', self.__set_paint)
        
        ### eraser button
        erase_image = gtk.Image()
        erase_image.set_from_pixbuf(theme.getImage('eraser'))
        erase_button = gtk.RadioToolButton(paint_button)
        erase_button.set_icon_widget(erase_image)
        erase_button.connect('clicked', self.__set_eraser)

        ### Color select
        self._color_label = InkDraw.ColorLabel(self._inkcanvas.get_stroke_color())
        hbox = gtk.HBox()        
        hbox.pack_start(self._color_label)
        hbox.pack_start(gtk.Arrow(gtk.ARROW_DOWN, gtk.SHADOW_IN))
        color_button = InkDraw.ColorButton(hbox)
        color_button.connect('color-set', self.__color_set, paint_button)
        
        ### clear button
        imgclear = gtk.Image()
        imgclear.set_from_stock(gtk.STOCK_CLEAR, gtk.ICON_SIZE_LARGE_TOOLBAR )
        clear = gtk.ToolButton(imgclear)
        clear.connect( 'clicked', self.__clear_canvas )
        
        
        main_img = gtk.Image()
        main_img.set_from_pixbuf(theme.getImage('medium_grid'))
        blank_img = gtk.Image()
        blank_img.set_from_pixbuf(theme.getImage('no_grid') )
        small_img = gtk.Image()
        small_img.set_from_pixbuf(theme.getImage('small_grid'))
        medium_img = gtk.Image()
        medium_img.set_from_pixbuf(theme.getImage('medium_grid'))
        large_img = gtk.Image()
        large_img.set_from_pixbuf(theme.getImage('large_grid'))
        
        ### grid button
        grid_button = InkDraw.GridButton(
            main_img, blank_img, small_img, medium_img, large_img,
            self._inkcanvas.get_grid_type())
        grid_button.connect( 'grid-type-set', self.__set_grid_type)

        ### undo Button
        undo_button = gtk.ToolButton()
        undo_button.set_stock_id(gtk.STOCK_UNDO)
        undo_button.connect("clicked", self.__undo)

        ### redo Button
        redo_button = gtk.ToolButton()
        redo_button.set_stock_id(gtk.STOCK_REDO)
        redo_button.connect("clicked", self.__redo)
        
        ### size Slider
        brushsmall = gtk.Image()
        brushsmall.set_from_pixbuf(theme.getImage('brush-small'))
        brushlarge = gtk.Image()
        brushlarge.set_from_pixbuf(theme.getImage('brush-large'))
        brush_slider = gtk.HScale(gtk.Adjustment(value=8, lower=1, upper=20, step_incr=0.5, page_incr=1, page_size=0))
        brush_slider.set_draw_value(True)
        brush_slider.set_size_request(130, -1)
        brush_slider.set_value_pos(gtk.POS_RIGHT)
        brush_slider.set_digits(0)
        brush_slider.set_update_policy(gtk.UPDATE_DISCONTINUOUS)
        brush_slider.connect("value-changed", self.__set_size)
                
        ### hbox
        hbox = gtk.HBox()
        hbox.pack_start(color_button, False, False)
        hbox.pack_start(paint_button, False, False)
        hbox.pack_start(erase_button, False, False)
        hbox.pack_start(undo_button, False, False)
        hbox.pack_start(redo_button, False, False) 
        hbox.pack_start(clear, False, False)
        hbox.pack_start(grid_button, False, False)
        hbox.pack_start(brushsmall, False, False)
        hbox.pack_start(brush_slider, False, False)
        hbox.pack_start(brushlarge, False, False) 
        
        ### vbox
        vbox = gtk.VBox()
        vbox.pack_start(hbox, expand= False)
        vbox.pack_start(self._inkcanvas)
        self.add(vbox)
        self.show_all()

    def __color_set(self, widget, color, paint_button):
        self._color_label.set_color(color)
        self._inkcanvas.set_stroke_color(color)
        self._inkcanvas.set_tool_type(InkDraw.ToolType.Paintbrush)
        paint_button.set_active(True)

    def __set_paint(self, widget=None):
        self._inkcanvas.set_tool_type(InkDraw.ToolType.Paintbrush)

    def __set_eraser(self, widget=None):
        self._inkcanvas.set_tool_type(InkDraw.ToolType.Eraser)

    def __clear_canvas(self, widget):
        self._inkcanvas.clear_canvas()

    def __set_grid_type(self, widget, grid_type):
        self._inkcanvas.set_grid_type(grid_type)

    def __undo(self, widget):
        self._inkcanvas.undo()
        
    def __redo(self, widget):
        self._inkcanvas.redo()
 
    def __set_size(self, range_widget):
        self._inkcanvas.set_stroke_size(range_widget.get_value())

if __name__ == "__main__":
    theme = Theme.Theme(None)
    win = InkDrawDemo(theme)
    win.connect('destroy', gtk.main_quit)
    gtk.main()
