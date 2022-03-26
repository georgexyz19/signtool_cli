import signtool

import yaml
import sys
import pprint
import io
import pathlib

import click


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


@click.command()
@click.option('--width', '-w', default=0, help='Width of the sign in inches for output svg' )
@click.option('--ratio', '-r', default=1.0, help='Ratio to true scale when drawing the sign, default 1.0')
@click.argument('input_dir', type=click.Path(exists=True, dir_okay=True, file_okay=False))
@click.argument('output_dir', type=click.Path(dir_okay=True), required=False)
def cli(width, ratio, input_dir, output_dir):
    # fn = sys.argv[-1] 

    pathlist = pathlib.Path(input_dir).glob('**/*.yaml')

    for filename in pathlist:

        stream = open(filename, 'r')
        d = yaml.safe_load(stream)
        arg = dict_to_obj(d)

        # modified the code for width and ratio
        e = signtool.SignTool(width, ratio)

        instream = io.StringIO('<svg></svg>')
        output_stream = io.StringIO()
        e.affect(arg, instream, output_stream)
        # print((output_stream.getvalue()))

        if output_dir is None:
            output_dir = input_dir
                    
        output_filename = output_dir + pathlib.Path(filename).stem + '.svg'

        out_file = open(output_filename, 'w')
        out_file.write(output_stream.getvalue())

        click.echo(f'Write the file to {output_filename}')
    

if __name__ == '__main__':
    cli()