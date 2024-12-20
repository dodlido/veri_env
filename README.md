# veri_env
An easy-to-use environment for development, version-control, compilation and simulation of verilog projects

## Setup - first use only
1. Create a directory for the tools with your version of my_defs.sh (see my_defs_template.sh)
   * Note that you will need to provide a github api key
2. In the same directory, create a virtual env (python3 -m venv veri_env)
3. Add to the activate script in veri_env/bin/activate with the following line:
   * source ${0%/*}/../../my_defs.sh 
4. Source the setup.sh script
5. Install python packages:
   * pip3 install gitpython
   * pip3 install requests
   * pip3 install cocotb
6. Install IcarusVerilog and GTKWave

## Foundations and dependencies
1. Uses icarus-verilog for compilation
2. Uses gtkwave for waveform viewer
3. Uses config file format for project description
4. Uses cocotb for testbenches

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

## Managing blocks
1. Users can use the 'add' alias to add a new git repository to their on github account
2. Users can use the 'get' alias to get to their current workspace a clone of any remote repository from their github account
3. Users can use the 'rls' alias to create a release of any repository. This will:
   * sign all verilog source files with the date, version and author's name
   * Create a remote tag
   * Create a local copy of the repo at the location provided in my_defs.sh

## TODO:
1. Implement top-level-synth and top-level-tb features
2. Plant desired .vcd location in top-level-tb
3. Check that everything works fine with sv syntax
