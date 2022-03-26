#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
# draw_border.py
Draw the border for the SignTool package

Copyright (C) February 2018, June 2018 George Zhang
Copyright (C) February 2020 Modify for Flask App George Zhang
  The code is also more organized, should be easier to upgrade to py3

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""

import simpletransform
import simplestyle
import io
from lxml import etree
import copy
import math
import sys
import inkex


class Border(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        self.style_stroke = {}

        #  DELETE ALL opt add option code 2/7/2020, not needed for standalone app.
        # opt = self.OptionParser.add_option

    def effect(self):
        so = self.options

        # code added for unittouu to work, revised on 2/6/2020
        ra = 25.4
        svg_elem = self.document.getroot()
        page_width, page_height = (1, 1)
        svg_elem.set('width', str(page_width) + 'in')
        svg_elem.set('height', str(page_height) + 'in')
        svg_elem.set('viewBox', '0 0 ' + str(page_width * ra) + ' '
                     + str(page_height * ra))

        self.strokewidth = self.unittouu(str(so.fStrokeWidth) + 'px')
        self.fcolor = so.fcolor
        self.bcolor = so.bcolor

        # pass string value is "rect", this is really weired
        # grep to find it was used in gcodetools.py print(so.active_tab)
        # remove drawBar to message app 2/7/2020
        if so.active_tab == '"rect"':
            self.drawRectBorder()
        elif so.active_tab == '"diamond"':
            self.drawDiamondBorder()
        else:
            inkex.debug('Please choose other tabs, then apply')

    def drawDiamondBorder(self):
        so = self.options
        w, h, r, off, bdw = (so.diamond_width, so.diamond_width,
                             so.diamond_radius, so.diamond_offset, so.diamond_bdwidth)

        if w == 0 or r == 0:
            return
        ra = 25.4
        svg_elem = self.document.getroot()

        page_width = w * math.cos(math.radians(45)) * 2 + 2
        page_height = page_width

        svg_elem.set('width', str(page_width) + 'in')
        svg_elem.set('height', str(page_height) + 'in')
        svg_elem.set('viewBox', '0 0 ' + str(page_width * ra) + ' '
                     + str(page_height * ra))

        layer_bd = self.createLayer(svg_elem, 'border')

        trans_str = 'translate(' + str(page_width / 2 *
                                       ra) + ',' + str(1 * ra) + ') '
        trans_str += 'rotate(' + str(45) + ')'
        trans_mat = simpletransform.parseTransform(trans_str)

        arg = (0, 0, w*ra, h*ra, r*ra, off*ra, bdw*ra)

        elm = self.draw_SVG_outer_path(arg, 'border_outside', layer_bd)
        simpletransform.applyTransformToNode(trans_mat, elm)

        elm = self.draw_SVG_border_path(arg, 'boder', layer_bd)
        simpletransform.applyTransformToNode(trans_mat, elm)

        if self.options.bDrawMark:
            layer_bk = self.createLayer(svg_elem, 'corner_marks')
            self.draw_diamond_corner_marks(
                page_width, page_height, ra, layer_bk)

    def draw_diamond_corner_marks(self, width, height, ra, layer_bk):
        self.draw_mark(width / 2 * ra, ra, 0.5 * ra, 'mark1', layer_bk)
        self.draw_mark(width / 2 * ra, (height - 1) * ra,
                       0.5 * ra, 'mark2', layer_bk)
        self.draw_mark(ra, height / 2 * ra, 0.5 * ra, 'mark3', layer_bk)
        self.draw_mark((width - 1) * ra, height / 2 * ra,
                       0.5 * ra, 'mark4', layer_bk)

    def drawRectBorder(self):
        so = self.options
        w, h, r, off, bdw = (so.width, so.height, so.radius,
                             so.offset, so.bdwidth)  # inch

        ra = 25.4  # inch to mm
        svg_elem = self.document.getroot()
        if w == 0 or h == 0 or r == 0:
            return

        page_width, page_height = (w + 1 * 2, h + 1 * 2)
        svg_elem.set('width', str(page_width)+'in')
        svg_elem.set('height', str(page_height)+'in')
        svg_elem.set('viewBox', '0 0 ' + str(page_width * ra) + ' '
                     + str(page_height * ra))

        layer_bd = self.createLayer(svg_elem, 'border')
        trans_str = 'translate(' + str(1 * ra) + ',' + str(1 * ra) + ')'
        trans_mat = simpletransform.parseTransform(trans_str)

        bd_arg = (0, 0, w*ra, h*ra, r*ra, off*ra, bdw*ra)

        elm = self.draw_SVG_outer_path(bd_arg, 'border_outside', layer_bd)
        simpletransform.applyTransformToNode(trans_mat, elm)

        elm = self.draw_SVG_border_path(bd_arg, 'border', layer_bd)
        simpletransform.applyTransformToNode(trans_mat, elm)

        if self.options.bDrawMark:
            layer_bk = self.createLayer(svg_elem, 'corner_marks')
            self.draw_corner_marks(w, h, ra, layer_bk)
            self.draw_outside_marks(w, h, ra, layer_bk)

    # LET's not call self.options in those helper methods
    # pass bd_arg with 7 elements, so it for both rect and diamond borders
    def draw_SVG_outer_path(self, bd_arg, name, parent):

        strokecolor = '#000000' if self.bcolor == '#FFFFFF' else self.bcolor

        line_style = {'stroke': strokecolor,
                      'stroke-width': self.strokewidth,
                      'fill': self.bcolor}

        p = self.path_dvalue_counter(bd_arg)

        rect_ri_attribs = {'style': simplestyle.formatStyle(line_style),
                           'd': p, inkex.addNS('label', 'inkscape'): name}

        elm = inkex.etree.SubElement(
            parent, inkex.addNS('path', 'svg'), rect_ri_attribs)
        return elm

    def draw_SVG_border_path(self, bd_arg, name, parent):
        line_style = {'stroke': self.fcolor,
                      'stroke-width': self.strokewidth,
                      'fill': self.fcolor}

        (x, y, width, height, radius, offset, bdwidth) = bd_arg

        x0, y0 = (x + offset, y + offset)
        width0, height0 = (width - 2 * offset, height - 2 * offset)
        radius0 = radius - offset

        bd_arg0 = (x0, y0, width0, height0, radius0)
        p0 = self.path_dvalue_counter(bd_arg0)

        x1, y1 = (x0 + bdwidth, y0 + bdwidth)
        width1, height1 = (width0 - 2 * bdwidth, height0 - 2 * bdwidth)
        radius1 = radius0 - bdwidth

        bd_arg1 = (x1, y1, width1, height1, radius1)
        p1 = self.path_dvalue_clockwise(bd_arg1)
        p = p0 + ' ' + p1

        rect_ri_attribs = {'style': simplestyle.formatStyle(line_style),
                           'd': p, inkex.addNS('label', 'inkscape'): name}

        elm = inkex.etree.SubElement(
            parent, inkex.addNS('path', 'svg'), rect_ri_attribs)
        return elm

    def path_dvalue_counter(self, bd_arg):
        (x, y, width, height, radius) = bd_arg[:5]
        d = 'M' + str(x + radius) + ',' + str(y) + \
            ' a ' + str(radius) + ',' + str(radius) + ' 0 0 0 ' + \
            str(-1 * radius) + ',' + str(radius) + \
            ' l ' + '0' + ',' + str(height - 2 * radius) + \
            ' a ' + str(radius) + ',' + str(radius) + ' 0 0 0 ' + \
            str(radius) + ',' + str(radius) + \
            ' l ' + str(width - 2 * radius) + ',' + '0' + \
            ' a ' + str(radius) + ',' + str(radius) + ' 0 0 0 ' + \
            str(radius) + str(-1 * radius) + \
            ' l ' + '0' + ',' + str(-1 * height + 2 * radius) + \
            ' a ' + str(radius) + ',' + str(radius) + ' 0 0 0 ' + \
            str(-1 * radius) + str(-1 * radius) + \
            ' l ' + str(-1 * width + 2 * radius) + ',' + '0' + \
            ' z'
        return d

    def path_dvalue_clockwise(self, bd_arg):
        (x, y, width, height, radius) = bd_arg[:5]
        d = 'M' + str(x + radius) + ',' + str(y) + \
            ' l ' + str(width-2 * radius) + ',' + '0' + \
            ' a ' + str(radius) + ',' + str(radius) + ' 0 0 1 ' + \
            str(radius) + ',' + str(radius) + \
            ' l ' + '0' + ',' + str(height - 2 * radius) + \
            ' a ' + str(radius) + ',' + str(radius) + ' 0 0 1 ' + \
            str(-1 * radius) + ',' + str(radius) + \
            ' l ' + str(-1 * width + 2 * radius) + ',' + '0' + \
            ' a ' + str(radius) + ',' + str(radius) + ' 0 0 1 ' + \
            str(-1 * radius) + ',' + str(-1 * radius) + \
            ' l ' + '0' + ',' + str(-1 * height + 2 * radius) + \
            ' a ' + str(radius) + ',' + str(radius) + ' 0 0 1 ' + \
            str(radius) + ',' + str(-1 * radius) + \
            ' z'
        return d

    # draw four corner marks
    def draw_corner_marks(self, width, height, ra, layer_bk):
        self.draw_mark(ra, ra, 0.5 * ra, 'mark1', layer_bk)
        self.draw_mark((width + 1) * ra, ra, 0.5 * ra, 'mark2', layer_bk)
        self.draw_mark(ra, (height + 1) * ra, 0.5 * ra,
                       'mark3', layer_bk)
        self.draw_mark((width + 1) * ra, (height + 1) * ra,
                       0.5 * ra, 'mark4', layer_bk)

    def draw_mark(self, x, y, radius, name, parent):
        self.draw_SVG_circle(x, y, radius, name + 'circle', parent)
        self.draw_SVG_line(x - radius, y, x + radius, y,
                           name + 'line1', parent)
        self.draw_SVG_line(x, y - radius, x, y + radius,
                           name + 'line2', parent)

    def draw_SVG_circle(self, x, y, radius, name, parent):
        circle_style = {'stroke': '#000000',
                        'stroke-width': self.strokewidth,
                        'fill': 'none'}
        circle_attribs = {'style': simplestyle.formatStyle(circle_style),
                          inkex.addNS('label', 'inkscape'): name,
                          'cx': str(x), 'cy': str(y),
                          'r': str(radius)}
        elm = inkex.etree.SubElement(
            parent, inkex.addNS('circle', 'svg'), circle_attribs)
        return elm

    def draw_SVG_line(self, x1, y1, x2, y2, name, parent):
        line_style = {'stroke': '#000000',
                      'stroke-width': self.strokewidth,
                      'fill': 'none'}
        line_attribs = {'style': simplestyle.formatStyle(line_style),
                        inkex.addNS('label', 'inkscape'): name,
                        'd': 'M ' + str(x1) + ',' + str(y1) + ' L' +
                        str(x2) + ',' + str(y2)}
        elm = inkex.etree.SubElement(
            parent, inkex.addNS('path', 'svg'), line_attribs)
        return elm

    def draw_outside_marks(self, width, height, ra, layer_bk):
        self.draw_mark((width/2 + 1) * ra, -0.5 * ra, 0.5 *
                       ra, 'outmark1', layer_bk)
        self.draw_mark((width/2 + 1) * ra, (height + 2 + 0.5) * ra,
                       0.5 * ra, 'outmark2', layer_bk)
        self.draw_mark(-0.5 * ra, (height / 2 + 1) * ra, 0.5 *
                       ra, 'outmark2', layer_bk)
        self.draw_mark((width + 2 + 0.5) * ra, (height / 2 + 1) * ra,
                       0.5 * ra, 'outmark2', layer_bk)

    # those layer methods are stable ==================
    # Create a layer given layer name and parent
    # 6/13/2018 Change logic to delete layer if existing then create
    def createLayer(self, parent, layer_name):
        path = '//svg:g[@inkscape:label="%s"]' % layer_name
        el_list = self.document.xpath(path, namespaces=inkex.NSS)
        if el_list:
            layer = el_list[0]
            layer_parent = layer.getparent()
            layer_parent.remove(layer)

        layer = inkex.etree.SubElement(parent, 'g')
        layer.set(inkex.addNS('label', 'inkscape'), layer_name)
        layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        return layer

    def findLayer(self, parent, layer_name):
        path = '//svg:g[@inkscape:label="%s"]' % layer_name
        el_list = self.document.xpath(path, namespaces=inkex.NSS)
        if el_list:
            layer = el_list[0]
        else:
            path_layer = '//svg:g[@inkscape:groupmode="layer"]'
            elem_list = self.document.xpath(path_layer, namespaces=inkex.NSS)
            if elem_list:
                layer = elem_list[0]
            else:
                layer = self.createLayer(self.document.getroot(), 'layer_new')
        return layer

    # Override parent class methods ============================
    # Those methods could be in a middle layer class ===========
    def output(self, stream):
        self.document.write(stream)

    def parse(self, stream=None):
        """Parse document in specified file or on stdin"""
        if stream is not None:
            p = etree.XMLParser(huge_tree=True)
            self.document = etree.parse(stream, parser=p)
            self.original_document = copy.deepcopy(self.document)
            stream.close()

    def affect(self, args=sys.argv[1:], instream=None, outstream=None):
        """Affect an SVG document with a callback effect"""
        self.svg_file = ''
        # localize()
        self.getoptions(args)
        self.parse(instream)
        self.getposinlayer()
        self.getselected()
        self.getdocids()
        self.effect()
        if outstream:
            self.output(outstream)

    def getoptions(self, args):
        self.options = args


# Define a simple class to store arguments
class BorderParam(object):
    x = 0
    y = 0
    width = 36
    height = 48
    radius = 2.25
    offset = 0.625
    bdwidth = 0.875
    fStrokeWidth = 5
    bDrawMark = False
    active_tab = '"rect"'
    fcolor = '#000000'
    bcolor = '#FFFFFF'
    ids = []

    diamond_width = 36
    diamond_radius = 3
    diamond_offset = 0.75
    diamond_bdwidth = 1


if __name__ == '__main__':
    e = Border()

    # args = ['--width=36', '--height=48', '--radius=2.25',
    #         '--offset=0.625', '--bdwidth=0.875', '--fStrokeWidth=5', '--bDrawMark=false', '--tab="rect"']
    # args = ['--width=48', '--height=48', '--radius=3',
    #         '--offset=0.75', '--bdwidth=1.25', '--fStrokeWidth=5', '--bDrawMark=true', '--tab="rect"']

    arg = BorderParam()

    # arg.width, arg.height, arg.radius, arg.offset, arg.bdwidth = 48, 48, 3, 0, 1.25
    # arg.fStrokeWidth, arg.bDrawMark = 5, True
    # arg.fcolor, arg.bcolor = '#000000', '#FFFFFF'

    instream = io.StringIO('<svg></svg>')
    output = io.StringIO()
    e.affect(arg, instream, output)
    print((output.getvalue()))
