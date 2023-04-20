# VCD-Viewer
a python program used to view vcd file

When you think using Modelsim is kind of complex and using teroshdl will somewhat run into some trouble in viewing the wave, you can try this.

## Requirements and Usage
Use this when you have:
- python3 with matplotlib installed
- a vcd file

then put this Python file in the same directory as your VCD file, and run the command `python VCD_Viewer.py filename` in the command line.

## Example
I'll take the vcd file `JK.vcd` in the folder `example-vcd` as an example. Enter `python VCD_Viewer.py .\example-vcd\JK.vcd` in your command line, and a plot like this would be shown:

![results](https://user-images.githubusercontent.com/94591149/233064318-346bf6db-7777-4f7d-a475-8c4526907860.png)

## It must be acknowledged that this code still has many problems. If you have a better solution, you are welcome to submit your pull request and issue!
