#! /usr/bin/python
# -*- coding: utf-8 -*-
"""
# signtool.py

Copyright (C) February 2018, June 2018 George Zhang
Copyright (C) February 2020 Modified George Zhang

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

from place_message_tb import *
import re
import gzip


def table(s):
    if s.strip().upper() == 'B':
        return table_B
    elif s.strip().upper() == 'C':
        return table_C
    elif s.strip().upper() == 'D':
        return table_D
    elif s.strip().upper() == 'E':
        return table_E
    elif s.strip().upper() == 'F':
        return table_F
    elif s.strip().upper() == 'EM':
        return table_EM

def downtb(s):
    if s.strip().upper() == 'B':
        return downtb_B
    elif s.strip().upper() == 'C':
        return downtb_C
    elif s.strip().upper() == 'D':
        return downtb_D
    elif s.strip().upper() == 'E':
        return downtb_E
    elif s.strip().upper() == 'F':
        return downtb_F
    elif s.strip().upper() == 'EM':
        return downtb_EM


class SignTool(inkex.Effect):
    def __init__(self, width, ratio):
        inkex.Effect.__init__(self)
        self.style_stroke = {}

        #  DELETE ALL opt add option code 2/7/2020, not needed for standalone app.
        # opt = self.OptionParser.add_option
        with gzip.open('sign_letters', 'rb') as f:
            str_etree = f.read()

        groot, gidmap = inkex.etree.XMLID(str_etree)
        self.groot = groot
        self.gidmap = gidmap

        self.output_width = width
        self.output_ratio = ratio

    def effect(self):
        params = self.options
        so = params.border
        self.bd_options = params.border # this is to patch both programs use self.options

        ra = 25.4
        svg_elem = self.document.getroot()
        page_width, page_height = (1, 1)
        svg_elem.set('width', str(page_width) + 'in')
        svg_elem.set('height', str(page_height) + 'in')
        svg_elem.set('viewBox', '0 0 ' + str(page_width * ra) + ' '
                     + str(page_height * ra))

        self.strokewidth = self.unittouu(str(so.strokewidth) + 'px')
        self.fcolor = params.fcolor
        self.bcolor = params.bcolor

        # remove drawBar to message app 2/7/2020
        # modified this will not compatible with draw_border.py
        if params.shape == 'rect':
            self.drawRectBorder()
        elif params.shape == 'diamond':
            ## change distance 
            self.drawDiamondBorder()
            msg_params = self.options.messages
            for msg_param in msg_params:
                msg_param.distance = msg_param.distance + \
                    so.diamond_width * math.cos(math.radians(45))
            
        else:
            inkex.debug('Please choose other tabs, then apply')

        msg_params = self.options.messages

        for msg_param in msg_params:
            self.drawmessage(msg_param)

    def drawmessage(self, msg_param):
        so = msg_param
        fontheight = self.unittouu(str(so.fontheight)+'in')
        message = so.message
        fontsize = so.fontsize
        distance = self.unittouu(str(so.distance + 1)+'in')

        self.drawbox = so.drawbox

        layer = self.create_layer(self.document.getroot(), 'messages')
        group = self.create_group(layer, message)  # group at center of page

        msg_width = self.message_width(message, fontsize, fontheight)
        doc_width = self.unittouu(self.getDocumentWidth())
        self.draw_message(message, fontsize, fontheight, doc_width / 2 -
                          msg_width / 2, distance, group)

    def create_group(self, parent, group_name):
        group = inkex.etree.SubElement(parent, 'g')
        group.set(inkex.addNS('label', 'inkscape'), group_name)
        group.set('fill', self.fcolor)
        return group

    # return an element of a character
    def get_char(self, letter, fontsize):
        if letter == 'cent':
            id = fontsize + 'cent'
            elem = self.gidmap[id]
            return elem
        else:
            code = ord(letter)
            id = fontsize + str(code)
            elem = self.gidmap[id]
            return elem

    def get_box(self, elem):
        #elem = self.get_char(letter)
        bbox = simpletransform.computeBBox([elem])
        return bbox

    def remove_id(self, d, key):
        if key in d:
            del d[key]
        return d

    # is upper case or is a number, those align vertical center
    # or is one of the eleven characters &!#()@?$-=+
    def is_align_center(self, letter):
        if letter.isupper() or (letter in "0123456789") or (letter in "&!#()@?$-=+:"):
            return True
        else:
            return False

    def parse_message(self, message):
        if not message:
            return
        message = message.strip()
        message = re.sub(' +', ' ', message)  # combine multiple space into 1

        message_list = []
        char_set = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890&!"#$*.,:()-@=+?'

        i = 0
        while i < len(message):
            if message[i] in char_set:
                message_list.append(('letter', message[i]))
            elif message[i] == ' ':
                message_list.append(('space', ' '))
            elif message[i] == '/':
                message_list.pop()
                message_list.append(('fraction', message[i-1: i+2]))
                i = i + 1
            elif message[i] == '|':
                j = i+1
                while j < len(message):
                    if message[j] == '|':
                        message_list.append(('distance', message[i+1:j]))
                        i = j
                        break
                    j = j + 1
            elif message[i] == '\\':
                j = i+1
                while j < len(message):
                    if message[j] == '\\':
                        message_list.append(('cent', message[i+1:j]))
                        i = j
                        break
                    j = j + 1

            i = i + 1
        return message_list

    def draw_message(self, message, fontsize, fontheight, xleft_in, ytop_in, parent):
        msg_list = self.parse_message(message)

        xleft = xleft_in
        ytop = ytop_in
        bfirst = True
        i = 0
        while i < len(msg_list):

            le = msg_list[i]
            if le[0] == 'letter':
                (le_left, le_width, le_right) = self.letter_size(
                    le[1], fontsize, fontheight)

                if bfirst:
                    le_left = 0
                    bfirst = False

                xleft = xleft + le_left
                self.draw_letter(
                    le[1], fontsize, fontheight, xleft, ytop, parent)
                xleft = xleft + le_width + le_right

            elif le[0] == 'space':
                if msg_list[i-1][0] == 'letter' and msg_list[i+1][0] == 'letter':
                    xleft = xleft + self.space_width(fontsize, fontheight,
                                                     msg_list[i-1][1], msg_list[i+1][1])
                else:               # / left right are zero, x has strange results
                    xleft = xleft + \
                        self.space_width(fontsize, fontheight, '/', '/')

            elif le[0] == 'fraction':
                self.draw_fraction(
                    le[1], fontsize, fontheight, xleft, ytop, parent)
                xleft = xleft + \
                    self.fraction_width(le[1], fontsize, fontheight)

            elif le[0] == 'distance':
                if msg_list[i-1][0] == 'letter' and msg_list[i+1][0] == 'letter':
                    xleft = xleft + \
                        self.distance_width(
                            le[1], fontsize, fontheight, msg_list[i-1][1], msg_list[i+1][1])
                else:
                    xleft = xleft + \
                        self.distance_width(
                            le[1], fontsize, fontheight, '/', '/')

            elif le[0] == 'cent':
                (le_left, le_width, le_right) = self.letter_size(
                    'cent', fontsize, fontheight)

                if bfirst:
                    le_left = 0
                    bfirst = False

                xleft = xleft + le_left
                self.draw_letter('cent', fontsize, fontheight,
                                 xleft, ytop, parent)
                xleft = xleft + le_width + le_right

            i = i + 1

    def message_width(self, message, fontsize, fontheight):
        msg_list = self.parse_message(message)

        xleft = 0  # xleft_in
        #ytop = ytop_in
        bfirst = True
        i = 0
        (le_left, le_width, le_right) = (0, 0, 0)
        while i < len(msg_list):

            le = msg_list[i]
            if le[0] == 'letter':
                (le_left, le_width, le_right) = self.letter_size(
                    le[1], fontsize, fontheight)

                if bfirst:
                    le_left = 0
                    bfirst = False

                xleft = xleft + le_left + le_width + le_right
                #self.draw_letter(le[1], fontsize, fontheight, xleft, ytop, parent)
                #xleft = xleft + le_width + le_right

            elif le[0] == 'space':
                if msg_list[i-1][0] == 'letter' and msg_list[i+1][0] == 'letter':
                    xleft = xleft + self.space_width(fontsize, fontheight,
                                                     msg_list[i-1][1], msg_list[i+1][1])
                else:               # / left right are zero, x has strange results
                    xleft = xleft + \
                        self.space_width(fontsize, fontheight, '/', '/')

            elif le[0] == 'fraction':
                #self.draw_fraction(le[1] ,fontsize, fontheight, xleft, ytop, parent)
                xleft = xleft + \
                    self.fraction_width(le[1], fontsize, fontheight)

            elif le[0] == 'distance':
                if msg_list[i-1][0] == 'letter' and msg_list[i+1][0] == 'letter':
                    xleft = xleft + self.distance_width(le[1], fontsize, fontheight,
                                                        msg_list[i-1][1], msg_list[i+1][1])
                else:
                    xleft = xleft + \
                        self.distance_width(
                            le[1], fontsize, fontheight, '/', '/')

            elif le[0] == 'cent':
                (le_left, le_width, le_right) = self.letter_size(
                    'cent', fontsize, fontheight)

                if bfirst:
                    le_left = 0
                    bfirst = False

                xleft = xleft + le_left + le_width + le_right
                #self.draw_letter('cent', fontsize, fontheight, xleft, ytop, parent)
                #xleft = xleft + le_width + le_right

            i = i + 1

        width = xleft - le_right
        return width

    def fraction_width(self, message, fontsize, fontheight):

        space_ratio = {'B': 0.65, 'C': 0.75, 'D': 0.85,
                       'E': 1.0, 'EM': 1.0, 'F': 1.15}

        whole_width = fontheight * 1.5 * 7 / 6 * space_ratio[fontsize] / 0.85

        if message[0] != '1':
            whole_width = fontheight * 1.5 * 8 / 6

        return whole_width

    # draw fractions, message in the format of 1/2 2/3
    # width is 7/6 of height
    def draw_fraction(self, message, fontsize, fontheight, xleft, ytop, parent):
        if len(message) != 3 and message[1] != '/':
            return

        whole_width = self.fraction_width(message, fontsize, fontheight)

        # draw numerator
        ytop_n = ytop - fontheight / 4.0
        self.draw_letter(message[0], fontsize,
                         fontheight, xleft, ytop_n, parent)

        # draw slash
        space_width = whole_width - self.letter_size(message[0], fontsize, fontheight)[1] - \
            self.letter_size(message[2], fontsize, fontheight)[1]
        xleft_slash = xleft + self.letter_size(message[0], fontsize, fontheight)[1] + \
            space_width * 9 / 16 - \
            self.letter_size(message[1], fontsize, fontheight)[1] / 2

        if message[2] == '4':
            xleft_slash = xleft_slash + space_width * 2 / 16

        ytop_slash = ytop_n + fontheight / 2.0
        self.draw_letter(message[1], fontsize, fontheight,
                         xleft_slash, ytop_slash, parent)

        # draw denominator
        xleft_d = xleft + whole_width - \
            self.letter_size(message[2], fontsize, fontheight)[1]
        ytop_d = ytop + fontheight / 4.0
        self.draw_letter(message[2], fontsize,
                         fontheight, xleft_d, ytop_d, parent)

    def distance_width(self, distance, fontsize, fontheight, prev_letter, next_letter):
        d_width = self.unittouu(distance + 'in')
        prev_letter_r = self.letter_size(prev_letter, fontsize, fontheight)[2]
        next_letter_l = self.letter_size(next_letter, fontsize, fontheight)[0]
        d_width = d_width - prev_letter_r - next_letter_l
        return d_width

    # do not support 2 spaces together
    def space_width(self, fontsize, fontheight, prev_letter, next_letter):
        space_ratio = {'B': 0.65, 'C': 0.75, 'D': 0.85,
                       'E': 1.0, 'EM': 1.0, 'F': 1.15}
        space_width = fontheight * 3.0 / 4.0 * space_ratio[fontsize]
        prev_letter_r = self.letter_size(prev_letter, fontsize, fontheight)[2]
        next_letter_l = self.letter_size(next_letter, fontsize, fontheight)[0]
        space_w = space_width - prev_letter_r - next_letter_l
        return space_w

    # letter size in the table (assume 4 inch letter) font size ABCD
    def letter_size(self, letter, fontsize, fontheight):
        ratio = fontheight * 1/4  # table values are in 4 inch letter height
        left = table(fontsize)[letter][0] * ratio  # fontsize BCDEEMF
        w_letter = table(fontsize)[letter][1] * ratio
        right = table(fontsize)[letter][2] * ratio
        return (left, w_letter, right)

    # ytop is top of the letter to top sign edge
    def draw_letter(self, letter, fontsize, fontheight, xleft, ytop, parent):

        elem = copy.deepcopy(self.get_char(letter, fontsize))

        new_id = self.uniqueId(elem.attrib['id'])
        elem.attrib['id'] = new_id

        bbox = self.get_box(elem)  # returns xmin, xmax, ymin, and ymax
        l_width = bbox[1] - bbox[0]
        l_height = bbox[3] - bbox[2]

        left = self.letter_size(letter, fontsize, fontheight)[0]
        w_letter = self.letter_size(letter, fontsize, fontheight)[1]
        right = self.letter_size(letter, fontsize, fontheight)[2]

        # xleft, ytop, w_letter, fontheight is the box size
        if self.drawbox:
            style_rect = {
                'stroke_color': '#000000',
                'stroke_width': self.unittouu('3px'),
                'fill': 'none'}
            self.draw_SVG_rect(xleft, ytop, w_letter,
                               fontheight, style_rect, letter, parent)

        l_ratio = w_letter / l_width

        # scale elem to fontheight inch size
        t1 = 'scale(' + str(l_ratio) + ')'
        m1 = simpletransform.parseTransform(t1)
        simpletransform.applyTransformToNode(m1, elem)

        if letter in 'gjpqy",*abcdeosuQ':   # one of the eight characters has down
            down = downtb(fontsize)[letter]
        else:
            down = 0
        down = down * fontheight / 2  # down units is in 2 inch letters

        bbox = self.get_box(elem)
        if not self.is_align_center(letter):  # lowcase align bottom
            t2 = 'translate(' + \
                str(xleft + w_letter / 2 - (bbox[0] + bbox[1])/2) + ',' + \
                str(ytop + fontheight - bbox[3] + down) + ')'
        else:
            t2 = 'translate(' + \
                str(xleft + w_letter / 2 - (bbox[0] + bbox[1])/2) + ',' + \
                str(ytop + fontheight/2 - (bbox[2] + bbox[3])/2 + down) + ')'

        m2 = simpletransform.parseTransform(t2)
        simpletransform.applyTransformToNode(m2, elem)

        parent.append(elem)

    def draw_SVG_rect(self, x, y, width, height, style, name, parent):
        line_style = {'stroke': style['stroke_color'],
                      'stroke-width': str(style['stroke_width']),
                      'fill': style['fill']}
        rect_attribs = {'style': simplestyle.formatStyle(line_style),
                        'width': str(width),
                        'height': str(height),
                        'x': str(x), 'y': str(y),
                        inkex.addNS('label', 'inkscape'): name}
        inkex.etree.SubElement(
            parent, inkex.addNS('rect', 'svg'), rect_attribs)


    def drawDiamondBorder(self):
        so = self.bd_options
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

        layer_bd = self.create_layer(svg_elem, 'border', delete=True)

        trans_str = 'translate(' + str(page_width / 2 *
                                       ra) + ',' + str(1 * ra) + ') '
        trans_str += 'rotate(' + str(45) + ')'
        trans_mat = simpletransform.parseTransform(trans_str)

        arg = (0, 0, w*ra, h*ra, r*ra, off*ra, bdw*ra)

        elm = self.draw_SVG_outer_path(arg, 'border_outside', layer_bd)
        simpletransform.applyTransformToNode(trans_mat, elm)

        elm = self.draw_SVG_border_path(arg, 'boder', layer_bd)
        simpletransform.applyTransformToNode(trans_mat, elm)

        if self.bd_options.drawmark:
            layer_bk = self.create_layer(svg_elem, 'corner_marks', delete=True)
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
        so = self.bd_options
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

        layer_bd = self.create_layer(svg_elem, 'border', delete=True)
        trans_str = 'translate(' + str(1 * ra) + ',' + str(1 * ra) + ')'
        trans_mat = simpletransform.parseTransform(trans_str)

        bd_arg = (0, 0, w*ra, h*ra, r*ra, off*ra, bdw*ra)

        elm = self.draw_SVG_outer_path(bd_arg, 'border_outside', layer_bd)
        simpletransform.applyTransformToNode(trans_mat, elm)

        elm = self.draw_SVG_border_path(bd_arg, 'border', layer_bd)
        simpletransform.applyTransformToNode(trans_mat, elm)

        if self.bd_options.drawmark:
            layer_bk = self.create_layer(svg_elem, 'corner_marks', delete=True)
            self.draw_corner_marks(w, h, ra, layer_bk)
            self.draw_outside_marks(w, h, ra, layer_bk)


    # pass bd_arg with 7 elements, so it for both rect and diamond borders
    def draw_SVG_outer_path(self, bd_arg, name, parent):

        strokecolor = '#000000' if self.bcolor == '#FFFFFF'.lower() else self.bcolor

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

    # 6/13/2018 Change logic to delete layer if existing then create
    # 2/8/2020 add delete parameter
    def create_layer(self, parent, layer_name, delete=False):
        path = '//g[@inkscape:label="%s"]' % layer_name # it is an error to have svg:g
        el_list = self.document.xpath(path, namespaces=inkex.NSS)
        if el_list:
            layer = el_list[0]
            if delete:
                layer_parent = layer.getparent()
                layer_parent.remove(layer)
        else: 
            layer = inkex.etree.SubElement(parent, 'g')
            layer.set(inkex.addNS('label', 'inkscape'), layer_name)
            layer.set(inkex.addNS('groupmode', 'inkscape'), 'layer')
        return layer

    def applyratio(self):
        width, height = (self.getDocumentWidth(), self.getDocumentHeight())
        width, height = map(lambda x: float(x) if '.' in x else int(x), (width[:-2], height[:-2]))

        true_ratio = self.output_ratio
        if self.output_width != 0:
            true_ratio = self.output_width / width

        page_width, page_height = (width * true_ratio, height * true_ratio)
        svg_elem = self.document.getroot()
        svg_elem.set('width', str(page_width)+'in')
        svg_elem.set('height', str(page_height)+'in')

        
 
    # Override parent class methods 
    # Those methods could be in a middle layer class
    def output(self, stream):
        stream.write(etree.tostring(self.document, pretty_print=True).decode('utf-8'))
        # self.document.write(stream)

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
        self.applyratio()
        if outstream:
            self.output(outstream)

    def getoptions(self, args):
        self.options = args

    # no need to worry about ids in param
    def getselected(self):
        pass


# Define a simple class to store arguments
# TODO the whole program could be organized into classes Border, Message, Sign, etc
class BorderParam(object):
    def __init__(self):

        self.width = 36
        self.height = 48
        self.radius = 2.25
        self.offset = 0.625
        self.bdwidth = 0.875
        self.strokewidth = 5
        self.drawmark = False

        self.diamond_width = 36
        self.diamond_radius = 3
        self.diamond_offset = 0.75
        self.diamond_bdwidth = 1


class MessageParam(object):
    def __init__(self):
        self.fontheight = 6
        self.message = 'SPEED'
        self.fontsize = 'E'
        self.distance = 6
        self.drawbox = False
        # self.ids = []

class SignParam(object):
    def __init__(self):
        self.border = BorderParam()
        self.messages = []

        self.fcolor = colors['black']
        self.bcolor = colors['white']
        self.shape = 'rect'

colors = {
    'black': '#231f20',
    'blue': '#005696',
    'brown': '#794500',
    'fluorescent_pink': '#f15e7c',
    'fluorescent_yellow_green': '#c1d72e',
    'green': '#006f51',
    'orange': '#f4911e',
    'purple': '#6c277c',
    'red': '#bf2e1a',
    'white': '#ffffff',
    'yellow': '#ffd24f',
    'coral': '#ff7f50',
    'light_blue': '#5a93c1',
    'black_ink': '#000000',
    'red_ink': '#ff0000',
    'blue_ink': '#0000ff',
}


if __name__ == '__main__':
    
    e = SignTool()

    # W3-8 sign
    bd = BorderParam()
    bd.diamond_width = 36
    bd.diamond_radius = 2.25
    bd.diamond_offset = .625
    bd.diamond_bdwidth = .875

    m1 = MessageParam()
    m1.fontheight = 4
    m1.fontsize = 'D'
    m1.message = 'RAMP'
    m1.distance = - 4 - 2.5 - 4 - 2.5

    m2 = MessageParam()
    m2.fontheight = 4
    m2.fontsize = 'D'
    m2.message = 'METERED'
    m2.distance =  - 4 - 2.5

    m3 = MessageParam()
    m3.fontheight = 4
    m3.fontsize = 'D'
    m3.message = 'WHEN'
    m3.distance = 0

    m4 = MessageParam()
    m4.fontheight = 4
    m4.fontsize = 'D'
    m4.message = 'FLASHING'
    m4.distance = 4 + 2.5

    arg = SignParam()
    arg.border = bd
    arg.messages.extend([m1, m2, m3, m4])
    arg.fcolor = colors['black']
    arg.bcolor = colors['yellow']
    arg.shape = 'diamond'

    instream = io.StringIO('<svg></svg>')
    output = io.StringIO()
    e.affect(arg, instream, output)
    print((output.getvalue()))
