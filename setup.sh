#!/usr/bin/bash

echo "enter tools absolute path:"
read TOOLS_PATH
echo "Enter workspace absolute path:"
read WS_PATH
PATH=/c/Users/User1/Notepad++:$PATH
PATH=/c/iverilog/bin:$PATH
PATH=/c/iverilog/gtkwave/bin:$PATH
python $TOOLS_PATH/setup.py -w $WS_PATH	  
cd $WS_PATH
echo "All set!" 