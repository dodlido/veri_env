import os
from pathlib import Path
import numpy as np
import math
from typing import List, Tuple
from utils.general import gen_err

########################
### Helper Functions ###
########################

def permissions_to_bit_str(permission: bool)->str:
    return '1\'b1' if permission else '1\'b0'

def create_port(direction: str, width: int, rgf_name: str, reg_name: str, field_name: str, suffix: str=None, commnet: str=None)->Tuple[str, str]:
    # parse signal name
    sig_name = f'{rgf_name}_{reg_name}_{field_name}'
    if suffix:
        sig_name += f'_{suffix}'
    
    module_port = f'{direction} logic [{width}-1:0] {sig_name}, // '
    instance_port = f'.{sig_name}({sig_name}), // '
    
    if commnet:
        temp_comment = f'{rgf_name}_{reg_name}_{field_name}: {commnet}'
        module_port += temp_comment
        instance_port += temp_comment + f' , {direction}({width}b)'

    return module_port, instance_port

###############
### Classes ###
###############

class Address(object):
    def __init__(self, byte_address: int=0):
        self.byte_address = byte_address
    
    def get_hex_address(self) -> str:
        return hex(self.byte_address * 8)
    
    def get_reg_index(self) -> int:
        if self.byte_address % 4 != 0:
            gen_err(f'illegal address found: {self.byte_address}')
        return int(self.byte_address / 4)
    
    def get_next_address(self) -> int:
        return self.byte_address + 4

class AccessPermissions(object):
    def __init__(self):
        self.sw_rd = True # SW has read permissions
        self.sw_wr = True # SW has write permissions
        self.hw_rd = True # HW has read permissions
        self.hw_wr = False # HW has no write permissions
        
    def check_valid_permissions(self):
        return not (self.sw_wr and self.hw_wr) # check whether both side have write permissions
    
    def set_cfg(self): # set permissions to mimic configuration permissions
        self.sw_rd = True # SW has read permissions
        self.sw_wr = True # SW has write permissions
        self.hw_rd = True # HW has read permissions
        self.hw_wr = False # HW has no write permissions
    
    def set_sts(self):# set permissions to mimic configuration permissions
        self.sw_rd = True # SW has read permissions
        self.sw_wr = False # SW has no write permissions
        self.hw_rd = False # HW has read permissions
        self.hw_wr = True # HW has write permissions
        
class Field(object):
    def __init__(self, name: str='field', description: str='some description', persmissions: AccessPermissions=AccessPermissions(), width: int=8, offset: int=None, reset_val: int=0, we: bool=False):
        self.name = name # field name
        self.description = description # field description
        self.permissions = persmissions # field access permissions
        self.width = width # field width [bits]
        self.offset = offset # field offset within the register [bits]
        self.reset_val = self.validate_reset_val(reset_val)
        self.we = self.parse_we(we)

    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "width": self.width,
            "offset": self.offset,
            "reset_val": self.reset_val,
            "HW write permission": self.permissions.hw_wr,
            "HW read permission": self.permissions.hw_rd,
            "SW write permission": self.permissions.sw_wr,
            "SW read permission": self.permissions.sw_wr
        }

    def get_verilog_ports(self, regfile_name: str, register_name: str) -> List[str]:
        module_ports, instance_ports = [], []
        if self.permissions.hw_rd:
            mps, ips = create_port('output', self.width, regfile_name, register_name, self.name, None, 'HW read port')
            module_ports.append(mps)
            instance_ports.append(ips)
        if self.permissions.hw_wr:
            mps, ips = create_port('input', self.width, regfile_name, register_name, self.name, 'hw_next', 'HW write port')
            module_ports.append(mps)
            instance_ports.append(ips)
        if self.we:
            mps, ips = create_port('input', 1, regfile_name, register_name, self.name, 'hw_we', 'HW write enable bit')
            module_ports.append(mps)
            instance_ports.append(ips)
        return module_ports, instance_ports
    
    def get_verilog_ff(self, regfile_name: str, register_name: str, register_address: Address, latch=False) -> str:
        
        # read from template
        template_path = Path(os.environ['tools_dir']) / 'regen' / 'register_template.v'
        with open(template_path, 'r') as template:
            ff = template.read()
        
        # parse permissions
        sw_wr_per_str = permissions_to_bit_str(self.permissions.sw_wr)
        hw_wr_per_str = permissions_to_bit_str(self.permissions.hw_wr)

        # choose between internal and external HW we
        hw_int_we_str = '{regfile_name}_{register_name}_{self.name}_hw_we' if self.we else '1\'b1'

        # mask HW write option in case of no permissions
        mask_hw_wr_str = '//' if not self.permissions.hw_wr else '  '
        mask_hw_rd_str = '//' if self.permissions.hw_rd else ''

        # latch
        latch_str = '1\'b1' if latch else '1\'b0'
                                                                            
        # replacement dictionary
        rep_dict = {
            '{RGF_NAME}': regfile_name,
            '{REG_NAME}': register_name,
            '{FLD_NAME}': self.name,
            '{FLD_SW_WR}': sw_wr_per_str,
            '{FLD_HW_WR}': hw_wr_per_str,
            '{FLD_OFFSET}': f'{self.offset}',
            '{FLD_ENDBIT}': f'{self.offset + self.width - 1}',
            '{FLD_WIDTH}': f'{self.width}',
            '{REG_ADD}': f"ADD_W'({register_address.byte_address})",
            '{REG_HEX_ADD}': f"{register_address.get_hex_address()}",
            '{FLD_HW_WE_INT}': hw_int_we_str,
            '{FLD_RST_VAL}': f'{self.width}\'h{self.reset_val}',
            '{MASK_HW_WR}': mask_hw_wr_str,
            '{MASK_HW_RD}': mask_hw_rd_str,
            '{LATCH}': latch_str
        }
        
        # go over dictionary, replacing all keys with values
        for key, value in rep_dict.items():
            ff= ff.replace(key, value)

        return ff
    
    def validate_reset_val(self, reset_val) -> int:
        if reset_val > (2 ** (self.width) - 1):
            gen_err(f'reset value of {reset_val} is illegal for an {self.width} bit field "{self.name}"')
        return reset_val
    
    def parse_we(self, we: bool=False) -> bool:
        if not self.permissions.hw_wr and we:
            gen_err(f'unable to set write-enable attribute to a field without HW write permissions (field {self.name})') 

class CfgField(Field):
    def __init__(self, name = 'field', description = 'some description', width = 8, offset = 0):
        persmissions = AccessPermissions()
        persmissions.set_cfg()
        super().__init__(name, description, persmissions, width, offset)

class StsField(Field):
    def __init__(self, name = 'field', description = 'some description', width = 8, offset = 0):
        persmissions = AccessPermissions()
        persmissions.set_sts()
        super().__init__(name, description, persmissions, width, offset)

class SWPulseWRField(Field):
    def __init__(self, name = 'field', description = 'some description', width=1, offset = None, reset_val = 0):
        permissions = AccessPermissions()
        permissions.set_cfg()
        we = False
        super().__init__(name, description, permissions, width, offset, reset_val, we)
    
    def get_verilog_ports(self, regfile_name, register_name):
        module_ports, instance_ports = super().get_verilog_ports(regfile_name, register_name)
        mps, ips = create_port('output', 1, regfile_name, register_name, self.name, 'sw_wr_pulse', 'SW wrote this field, pulse, active high')
        module_ports.append(mps)
        instance_ports.append(ips)
        return module_ports, instance_ports
    
    def get_verilog_ff(self, regfile_name, register_name, register_address):
        verilog_code = super().get_verilog_ff(regfile_name, register_name, register_address)
        signal_name = f'{regfile_name}_{register_name}_{self.name}'
        verilog_code += f'''\n
assign {signal_name}_sw_wr_pulse = {signal_name}_sw_write_access & {signal_name}_sw_we & |(pstrb_mask[{self.offset}+:{self.width}]) ;
// SW pulse active high when {signal_name} is written
\n'''
        return verilog_code

class SWPulseRDField(Field):
    def __init__(self, name = 'field', description = 'some description', width = 8, offset = None, reset_val = 0):
        permissions = AccessPermissions()
        permissions.set_sts()
        we = False
        super().__init__(name, description, permissions, width, offset, reset_val, we)

    def get_verilog_ports(self, regfile_name, register_name):
        module_ports, instance_ports = super().get_verilog_ports(regfile_name, register_name)
        mps, ips = create_port('output', 1, regfile_name, register_name, self.name, 'sw_rd_pulse', 'SW read this field, pulse, active high')
        module_ports.append(mps)
        instance_ports.append(ips)
        return module_ports, instance_ports
    
    def get_verilog_ff(self, regfile_name, register_name, register_address):
        verilog_code = super().get_verilog_ff(regfile_name, register_name, register_address)
        signal_name = f'{regfile_name}_{register_name}_{self.name}'
        verilog_code += f'''\n
assign {signal_name}_sw_rd_pulse = (paddr==ADD_W'({register_address.byte_address})) & (apb_sts_curr==APB_READ) ; 
// SW pulse active high when {signal_name} is read
\n''' 
        return verilog_code

class IntrField(Field):
    def __init__(self, name = 'field', description = 'some description', offset = None, reset_val = 0):
        permissions = AccessPermissions()
        permissions.set_sts()
        width = 1
        super().__init__(name, description, permissions, width, offset, reset_val, False)
        
    def get_verilog_ports(self, regfile_name, register_name):
        return super().get_verilog_ports(regfile_name, register_name)
    
    def get_verilog_ff(self, regfile_name, register_name, register_address):
        verilog_code = super().get_verilog_ff(regfile_name, register_name, register_address, True)
        signal_name = f'{regfile_name}_{register_name}_{self.name}'
        verilog_code += f'''
// interrupt for {signal_name}
logic {signal_name}_intr ; 
assign {signal_name}_intr = ~{signal_name} & {signal_name}_next ; 
'''
        return verilog_code
        
class Register(object):
    def __init__(self, name: str='register', description: str='some description', width: int=32, fields: List[Field]=[]):
        self.name = name # register name
        self.description = description # register description
        self.width = width # register width in [bits]
        self.address = Address(0)
        self.fields = [] # list of fields in register
        self.occupied_bmap = np.zeros(width) # bit-map of occupied bits
        for fd in fields:
            self.add_field(fd)
            
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "address": self.address.byte_address,
            "width": self.width,
            "fields": [fld.to_dict() for fld in self.fields]
        }

    def add_field(self, field: Field):
        
        # Check whether a field with the same name already exists
        existing_field_names = []
        for fld in self.fields:
            existing_field_names.append(fld.name)
        if field.name in existing_field_names:
            gen_err(f'field "{field.name}" already exists within register "{self.name}"')

        # handle field offset that was not set
        if not field.offset:
            found_empty_spot = False
            for i in range(4): # assume that fields should be byte-aligned
                inferred_offset = i*8
                if 1 not in self.occupied_bmap[inferred_offset:inferred_offset+field.width]: # found an empty slot
                    found_empty_spot = True
                    break
            if not found_empty_spot:
                gen_err(f'failed to infer an offset for field "{field.name}" at register "{self.name}"')
            field.offset = inferred_offset

        # check location is vacant
        field_location = np.zeros(self.width)
        field_location[field.offset:field.offset+field.width] = 1 
        double_booking_array = np.logical_and(field_location, self.occupied_bmap)
        if 1 in double_booking_array:
            gen_err(f"can't add field '{field.name}' to register '{self.name}'. following bits are already taken: {np.where(double_booking_array==1)[0]}")

        # if location is vacant, update bitmap and add field:
        self.occupied_bmap = np.logical_or(field_location, self.occupied_bmap)
        self.fields.append(field)
    
    def get_verilog_ffs(self, regfile_name: str) -> str:
        ffs = ''
        master_wire_declaration = f'\nlogic [{self.width}-1:0] {regfile_name}_{self.name} ;'
        master_wire_assignment = f'\nassign {regfile_name}_{self.name} = ' + '{'
        for fld in self.fields:
            ffs += fld.get_verilog_ff(regfile_name, self.name, self.address) + '\n\n'
            master_wire_assignment += f'{regfile_name}_{self.name}_{fld.name}, '
        master_wire_assignment = master_wire_assignment[:-2] + '};\n'
        return ffs + master_wire_declaration + master_wire_assignment
    
    def get_verilog_ports(self, regfile_name: str) -> List[str]:
        module_ports, instance_ports = [], []
        for fld in self.fields:
            mps, ips = fld.get_verilog_ports(regfile_name, self.name)
            module_ports += mps
            instance_ports += ips
        return module_ports, instance_ports

class RegFile(object):
    def __init__(self, name: str='regfile', description='some description', registers: List[Register]=[]):
        self.name = name
        self.description = description
        self.registers, self.running_address, self.rgf_addr_width, self.rgf_reg_width = self.arrange_registers(registers)
    
    def to_dict(self):
        return {
            "name": self.name,
            "description": self.description,
            "address width": self.rgf_addr_width,
            "registers": [reg.to_dict() for reg in self.registers]
        }

    def arrange_registers(self, registers: List[Register]=[]):
        
        # initialize some values
        register_names_list, register_list, rgf_reg_width, running_address = [], [], 0, Address(0)
        
        for reg in registers:
            # Check if this register already exists within the RGF
            if reg.name in register_names_list:
                gen_err(f'register "{reg.name}" already exists within RGF "{self.name}"')
            
            # Advance address and append to register list
            register_names_list.append(reg.name)
            reg.address = running_address
            running_address = Address(running_address.get_next_address())
            register_list.append(reg)

            # adapt register maximum width [bits]
            if rgf_reg_width < reg.width:
                rgf_reg_width = reg.width
        
        # infer the address width in [bits]
        rgf_addr_width = int(math.log(running_address.byte_address , 2))

        return register_list, running_address, rgf_addr_width, rgf_reg_width
    
    def add_register(self, register: Register):
        # check whether the register slready exists in the RGF
        reg_names = []
        for reg in self.registers:
            reg_names.append(reg.name)
        if register.name in reg_names:
            gen_err(f'register "{reg.name}" already exists within RGF "{self.name}"')

        # if not then it is OK to append it and advance the address
        register.address = self.running_address
        self.registers.append(register)
        self.runnin_address = Address(self.running_address.get_next_address())

    def get_verilog_ports(self) -> List[str]:
        module_ports, instance_ports = [], []
        found_an_intr = False
        for reg in self.registers:
            mps, ips = reg.get_verilog_ports(self.name)
            module_ports += mps
            instance_ports += ips
        for reg in self.registers:
            for fld in reg.fields:
                if isinstance(fld, IntrField):
                    found_an_intr = True
        if found_an_intr:
            intr_mps, intr_ips = create_port('output', 1, self.name, '', '', 'intr', 'agrregation of interrups in regfile')
            module_ports.append(intr_mps)
            instance_ports.append(intr_ips)
        return module_ports, instance_ports
    
    def get_html(self):
        # Start the HTML document
        html = "<html><head><title>Register File</title>"
        
        # Add CSS for styling
        html += """
        <style>
            /* Import Google Fonts */
            @import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap');
        
            body { font-family: 'Roboto', sans-serif; }
            h1, h2, h3 { 
                padding: 10px; 
                font-weight: 700;
            }
            
            /* Color scheme: shades of blue */
            h1 { background-color: #4A90E2; color: white; }
            h2 { background-color: #357ABD; color: white; }
            h3 { background-color: #2C6BA2; color: white; }

            p { 
                margin-left: 20px; 
                font-weight: 400;
            }

            /* Collapsible content style */
            .collapsible-content {
                margin-left: 30px;
                display: none;  /* Hidden by default */
                margin-top: 10px;
            }

            .collapsible-button {
                cursor: pointer;
                padding: 10px;
                color: white;
                border: none;
                background-color: #357ABD;
                text-align: left;
                width: 100%;
            }
            
            .collapsible-button:hover {
                background-color: #2C6BA2;
            }

            /* Make Middle and Bottom Class buttons and content slightly larger */
            .middle-class-button, .bottom-class-button {
                font-size: 24px;  /* Larger font size for buttons */
            }

            .middle-class-content, .bottom-class-content {
                font-size: 18px;  /* Slightly larger content font size */
            }
        </style>
        """
        
        # Add JavaScript for collapsible functionality
        html += """
        <script>
        // Function to toggle the visibility of collapsible content
        function toggleVisibility(id) {
            var content = document.getElementById(id);
            if (content.style.display === "none" || content.style.display === "") {
                content.style.display = "block"; // Make it visible
            } else {
                content.style.display = "none"; // Hide it
            }
        }
        </script>
        """
        
        # Convert the top instance to a dictionary and start adding it to the HTML
        rgf_dict = self.to_dict()
        
        # Adding the Top Class section
        html += f"<h1>{rgf_dict['name']}</h1>"
        html += f"<p><b>Description:</b> {rgf_dict['description']}</p>"
        html += f"<p><b>Address Space:</b> 0x{2 ** rgf_dict['address width']}</p>"
        
        # For each middle class instance in the top instance
        for reg_idx, reg_dict in enumerate(rgf_dict['registers']):
            reg_id = f"reg_{reg_idx}"  # Create a unique ID for each Middle Class
            
            html += f"""
            <button class="collapsible-button middle-class-button" onclick="toggleVisibility('{reg_id}')">Register: {reg_dict['name']}</button>
            <div id="{reg_id}" class="collapsible-content">
            <p><b>Description:</b> {reg_dict['description']}</p>
            <p><b>Address:</b> {reg_dict['address']}</p>
            <p><b>Width:</b> {reg_dict['width']}</p>
            """
            
            # For each bottom class instance in the middle class
            for fld_idx, fld_dict in enumerate(reg_dict['fields']):
                fld_id = f"bottom_{reg_idx}_{fld_idx}"  # Unique ID for Bottom Class
                
                html += f"""
                <button class="collapsible-button bottom-class-button" onclick="toggleVisibility('{fld_id}')">Field: {fld_dict['name']}</button>
                <div id="{fld_id}" class="collapsible-content">
                <p><b>Description:</b> {fld_dict['description']}</p>
                <p><b>Width:</b> {fld_dict['width']}</p>
                <p><b>Offset:</b> {fld_dict['offset']}</p>
                <p><b>Reset Value:</b> {fld_dict['reset_val']}</p>
                <p><b>HW write permission:</b> {fld_dict['HW write permission']}</p>
                <p><b>HW read permission:</b> {fld_dict['HW read permission']}</p>
                <p><b>SW write permission:</b> {fld_dict['SW write permission']}</p>
                <p><b>SW read permission:</b> {fld_dict['SW read permission']}</p>
                </div>
                """
            
            html += "</div>"  # Close the middle class div

        html += "</body></html>"
    
        return html

    def get_verilog(self) -> str:
        
        # build RGF content and output multiplexer
        rgf_content, output_mux, port_content = '', '', ''
        for reg in self.registers:
            rgf_content += reg.get_verilog_ffs(self.name) + '\n\n'
            output_mux += f'ADD_W\'({reg.address.byte_address}): prdata = {self.name}_{reg.name} ;\n   '
        port_list, _ = self.get_verilog_ports()
        for port in port_list:
            port_content += f'{port}\n   '
        
        # open template
        template_path = Path(os.environ['tools_dir']) / 'regen' / 'rgf_template.v'
        with open(template_path, 'r') as template:
            rgf_verilog = template.read()

        # replace key words
        rgf_verilog = rgf_verilog.replace('{HW_RGF_PORTS}', port_content)
        rgf_verilog = rgf_verilog.replace('{RGF_CONTENT}', rgf_content)
        rgf_verilog = rgf_verilog.replace('{OUTPUT_MUX}', output_mux)
        rgf_verilog = rgf_verilog.replace('{RGF_REG_WIDTH}', f'{self.rgf_reg_width}')
        rgf_verilog = rgf_verilog.replace('{RGF_ADD_WIDTH}', f'{self.rgf_addr_width}')
        rgf_verilog = rgf_verilog.replace('{RGF_NAME}', f'{self.name}')

        # handle interrupts
        intr_str = ''
        for reg in self.registers:
            for fld in reg.fields:
                if isinstance(fld, IntrField):
                    intr_str += f'{self.name}_{reg.name}_{fld.name}_intr | '
        intr_str = intr_str[:-2] + ';\n'

        rgf_verilog += f'\nassign {self.name}___intr = {intr_str}\n\nendmodule\n'
        
        return rgf_verilog
    
    def get_inst(self) -> str:

        _, port_list = self.get_verilog_ports()
        port_string = ''
        for port in port_list:
            port_string += f'   {port}\n'
        
        template_path = Path(os.environ['tools_dir']) / 'regen' / 'rgf_inst_template.v'
        with open(template_path, 'r') as template:
            inst = template.read()
        
        inst = inst.replace('{RGF_NAME}', f'{self.name}')
        inst = inst.replace('{RGF_PORTS}', port_string)
        return inst

    

