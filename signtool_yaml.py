import signtool

import yaml
import sys
import pprint
import io


def dict_to_obj(d):
    arg = signtool.SignParam()
    arg.fcolor = signtool.colors[ d['sign']['fcolor'] ]
    arg.bcolor = signtool.colors[ d['sign']['bcolor'] ]
    arg.shape =  d['sign']['shape']


    bd = signtool.BorderParam()
    if arg.shape == 'rect':
        d_border = d['sign']['border']
        bd.bdwidth = d_border['bdwidth']
        bd.height = d_border['height']
        bd.offset = d_border['offset']
        bd.radius = d_border['radius']
        bd.width = d_border['width']

    if arg.shape == 'diamond':
        d_border = d['sign']['border']
        bd.diamond_width = d_border['diamond_width']
        bd.diamond_radius = d_border['diamond_radius']
        bd.diamond_offset = d_border['diamond_offset']
        bd.diamond_bdwidth = d_border['diamond_bdwidth']

    bd.strokewidth = d_border.get('strokewidth', 5)
    bd.drawmark = d_border.get('drawmark', False)

    arg.border = bd

    # m1 = signtool.MessageParam()
    t = d['sign']['messages']

    for msg in t:
        m1 = signtool.MessageParam()
        d_message = msg['message']
        m1.distance = d_message['distance']
        m1.drawbox = d_message.get('drawbox', False)
        m1.fontheight = d_message['fontheight']
        m1.fontsize = d_message['fontsize']
        m1.message = d_message['message']
        arg.messages.append(m1)

    return arg


if __name__ == '__main__':

    fn = sys.argv[-1] 
    stream = open(fn, 'r')
    d = yaml.safe_load(stream)
    arg = dict_to_obj(d)

    e = signtool.SignTool()

    instream = io.StringIO('<svg></svg>')
    output = io.StringIO()
    e.affect(arg, instream, output)
    print((output.getvalue()))