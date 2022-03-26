# Command Line Tool to Generate Traffic Sign Graphics

The code in this repo was written in Feb 2020 by George Zhang. It is a command line tool 
to generate traffic sign graphics. More specifically, you create a yaml file with 
sign border dimensions and sign messages, run the tool to generate an SVG rendering 
of the sign. 

For example, you have this yaml file for R2-1 sign, 

```
sign:
  fcolor: 'black'
  bcolor: 'white'
  shape: 'rect'
  border:
    width: 36
    height: 48
    radius: 2.25
    offset: 0.625
    bdwidth: 0.875
    strokewidth: 5
    drawmark: false  
  messages:
    - message:
        fontheight: 6
        fontsize: 'E'
        message: 'SPEED'
        distance: 6
        drawbox: false
    - message:
        fontheight: 6
        fontsize: 'E'
        message: 'LIMIT'
        distance: 17
        drawbox: false
    - message:
        fontheight: 14
        fontsize: 'E'
        message: '50'
        distance: 28
        drawbox: false
```

On the command line, run the command

```
$(venv) george@NUC:~/Code/opensigntool_cli$ python signtool_cli.py yaml/R2-1.yaml 
Write the file to yaml/R2-1.svg
```

The `opensigntool_cli` program will write an output file to yaml/R2-1.svg. 


Run the command below will batch process all yaml file in a directory. 

```
(venv) george@NUC:~/Code/opensigntool_cli$ python signtool_dir.py ./yaml ./svg
Write the file to ./svgR2-1.svg
Write the file to ./svgW8-5P.svg
Write the file to ./svgW13-1P.svg
Write the file to ./svgTrucks.svg
Write the file to ./svgR1-2aP.svg
Write the file to ./svgR1-10P.svg
Write the file to ./svgR2-2P.svg
Write the file to ./svgW3-8.svg
Write the file to ./svgR2-6bP.svg
Write the file to ./svgR1-3p.svg
Write the file to ./svgW7-6.svg
```

Most code is in the signtool.py file.  The module is dependent on other six 
inkex (before Inkscape 1.0) library files. Those six files were originally in 
py2.  I upgraded them to py3 with the 2to3 tool in Python stdlib. 

The inkex API is rewritten since Inkscape 1.0.  I don't plan to spend more 
time on this project unless for obvious and easy bugs.  The code base could 
serve an example for other projects. 

The tools work fine for simple traffic sign generation as demonstrated by 
the files in the /yaml directory. 

