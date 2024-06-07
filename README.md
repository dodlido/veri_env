# veri_env
An easy-to-use environment for compilation and simulation of verilog projects

## Foundations
1. Uses icarus-verilog for compilation
2. Uses gtkwave for waveform viewer
3. Uses config file format for project description

## Basic usage
1. sim.py is the base script
2. Flags: 
   * -c PATH   :  path to a configuration file
   * -v VIEW   :  view name
   * -o PATH   :  Output directory
   * --pre-run :  Conduct pre-run (creates file-list, compiles and elaborates)
   * --run     :  Conduct run (runs simulation)
   * --waves   :  Open gtkwave 
3. Use sim.py -h to view options at your leisure

## Configuration syntax
1. 2 basic concepts:
   * Section:  
      * Section begins with "[section_name]"
      * Section ends with ";"
      * Saved sections are:
         * [path] : Includes relevent paths i.e children top directories
      * Other sections can be of view names, for example [rtl]. A view is a way of looking at a project
   * Key: 
      * Keys can be found under sections
      * Some keys have a value (or multiple values) attached to them
      * Type 1 key,value pair: "key=value"
      * Type 2 key,value pair, for multiple values: "key: \n value1 \n value2 \n ... valueN"
2. To specify locations of children, use key=value pairs under [path] section where:
   * key = child name
   * value = "local, path" where local signifies that this project is found locally and path is the path to the top-level folder
3. To specify children views use "key: \n value1 \n value2 \n ... valueN" syntax where under [view] section of your configuration where:
   * key = "child"
   * value = "name=view" where name must match child name from section 2 and view is the desired view
4. To specify files, use "key: \n value1 \n value2 \n ... valueN" syntax under [view] section of your configuration where:
   * key = "file"
   * value = "file_name" where file_name is a desired file (path relative to this top-level folder)

## TODO:
1. Implement top-level-synth and top-level-tb features
2. Plant desired .vcd location in top-level-tb
3. Check that everything works fine with sv syntax
