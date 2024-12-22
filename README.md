# veri_env
An easy-to-use environment for:
1. Development
2. Version-control
3. Compilation
4. Simulation
5. Verification
6. Synthesis
Of verilog projects

## Setup - first use only

1. Create a directory for the tools with your version of my_defs.sh (see my_defs_template.sh)

```bash
    mkdir tools
    cd tools
    git clone git@github.com:dodlido/veri_env.git 
    cp veri_env/my_defs_template.sh tools/my_defs.sh
```

   * Fill the my_defs.sh file with your personal prefrences and variables
   * Note that you will need to provide a github api key. Tutorial is here:
        https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

2. Download python's virtualenv library:

```bash
    pip3 install virtualenv
```
 
3. Under the tools directory, create a virtual env:

```bash
    python3 -m venv py_venv
```

4. Add to the activate script in py_venv/bin/activate with the following line:
   * source ${0%/*}/../../my_defs.sh 

5. Source the setup script:

```bash
    source tools/veri_env/setup.sh w setup
    cd -
```

6. Python's virtual environment should be set-up by now, you can verify this by:

```bash
    which python3
    >> tools/py_venv/bin/python3
```

7. Install python packages:

```bash
    pip3 install gitpython
    pip3 install requests
    pip3 install cocotb
```

8. Install IcarusVerilog:
        https://steveicarus.github.io/iverilog/usage/installation.html#

9. Install GTKWave:
        https://flathub.org/apps/io.github.gtkwave.GTKWave

10. Install make:

```bash
    sudo apt-get install build-essential
```

## Setting Up

1. When opening a new terminal, use setup to:
   * Familiarize the terminal with the 'veri_env' tools
   * Create a new workspace named 'my_workspace' and cd to $home_dir/my_workspace
   * Activate the python virtual environment
   * Create the sim, add, get aliases to the 'veri_env' tools

```bash
    source tools/veri_env/setup.sh w my_workspace
```

## File-System 

1. Under a given *workspace*, there could be any number of *project*s
2. *project*s are repositories
3. Under each *project* there could be up to 2 folders:
   - *design* - contains all design blocks under this project
   - *verification* - contains all verification blocks under this project
4. Under *design* there could be any number of *block*s, each in its own subfolder named "block_name"
5. Under each *design block* there could be up to 2 folders:
   - *rtl* - contains all the RTL of the *design block*
      - Under the *rtl* folder there could be any number of verilog source files
   - *misc* - contains the *design block* configuration file
      - The configuration file must be of the format "block_name.cfg"
      - The configuration file syntax is explained below
      - For each *design block* there could be a folder under the *verification* tree which contains:
         - a folder named *tests* which contains a cocotb testbench named "block_name_tb.py"
         - any number of folders and scripts that "block_name_tb.py" needs to function
6. You can browse an example workspace in the "exampl_ws" folder in this repository

```bash
.
├── aligners
│   ├── design
│   │   └── al_w2n
│   │       ├── misc
│   │       │   └── al_w2n.cfg
│   │       └── rtl
│   │           └── al_w2n.v
│   └── verification
│       └── al_w2n
│           ├── models
│           │   └── al_w2n_model.py
│           └── tests
│               └── al_w2n_tb.py
└── vlib
    └── design
        └── cnt_cfg_lim
            ├── misc
            │   └── cnt_cfg_lim.cfg
            └── rtl
                └── cnt_cfg_lim.v
```

## Configuration syntax

1. The configuration file utilizes 2 fundamental concepts:
   * *section*:  
      * *section* begins with "[section_name]"
      * *section* ends with ";"
      * There are a few reserved *section*s like [genral], [path]
      * Other *section*s can be of **view** names, for example [rtl]. 
         * **view** is "a way of looking at a project" 
         * Each **view** can define for example its own filelist
         * **view**s can be simulated separately
   * *key*: 
      * *key*s can be found under *section*s
      * Some *key*s have a **value** (or multiple **value**s) attached to them
      * single **value** *key* syntax:
         ```cfg
            key=value
         ```
      * multiple **value**s *key* syntax:
         ```cfg
            key:
               value1
               value2
               ...
         ```

2. [general] *section*:
   * This section is mandatory and specifies the *block* name and *project*:

   ```cfg
      [general]
         block=<project_name>/design/<block_name>
      ;
   ```

3. [path] *section*:
   * This section can be used to to specify where to find other *design block*s this *design block* utilizes as **children**.
   * Accepted *key*s are other *design blocks* specified in <project_name>/design/<block_name> format like in the [general] *section*
   * Accepted **value**s are:
      * "local" which means that the *design block* is somewhere within the workspace
      * "release, X.Y.Z" which means that the *design block* is in your release storage (location defined in my_defs.sh)

   ```cfg
      [path]
         <project1_name>/design/<block1_name>=local
         <project2_name>/design/<block2_name>=release, X.Y.Z
      ;
   ```

4. [view] *section*s:
   * *section*s that are not [general] or [path] are referred to as **view**s
   * Each **view** can contain up to 3 reserved *key*s:
      * **design** defines the top module of the view:
      * **child** defines the **children** **view**s used in this **view**
      * **file** defines the filelist the **view** utilizes (from this *design block* only, without referring to **children**) 
   
   ```cfg
      [rtl]
         design:
            top=<top_level_module_name>
         child:
            <project1_name>/design/<block1_name>=<view1_name>
            <project2_name>/design/<block2_name>=<view2_name>
         file:
            <rtl/file1.v>
            <rtl/file2.v>
            ...
      ;
   ```

## Simulation
1. Use sim.py for all you simulation needs
2. Flags: 
   * -c PATH   :  path to a configuration file, optional, if cwd is some *design block* this is not necessary
   * -v VIEW   :  view name, required
   * --waves   :  Open gtkwave, optional trigger 
3. The target directory of the simulation results is $work_dir/ws_name/block_name where $work_dir was defined in your my_defs.sh
3. Which test will run? 
   * If sim.py found an existing testbench in the reserved path as explained in the file system section, it will use it for simulation
   * Otherwise, an automatic testbench will be generated  

## Managing blocks
1. Users can use the 'add' alias to add a new git repository to their on github account
2. Users can use the 'get' alias to get to their current workspace a clone of any remote repository from their github account
3. Users can use the 'rls' alias to create a release of any repository. This will:
   * sign all verilog source files with the date, version and author's name
   * Create a remote tag
   * Create a local copy of the repo at the location provided in my_defs.sh

## TODO:
1. Implement top-level-synth
2. top-level-tb features
   * no clock designs fail the auto-test
   * automatic test-bench generation
2. Plant desired .vcd location in top-level-tb
3. Check that everything works fine with sv syntax
