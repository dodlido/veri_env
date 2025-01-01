from collections import deque
import cocotb
from cocotb.triggers import RisingEdge, ReadOnly
from cocotb_bus.drivers import BusDriver
from cocotb_bus.monitors import BusMonitor

# Error class for wrong field name
class FieldNotFoundError(Exception):
    def __init__(self, field_name=None, field_addr=None, field_strobe=None):
        if not field_name:
            self.message = f"Field at address {field_addr} with strobe {field_strobe} not found"
        else:
            self.message = f"Field '{field_name}' not found."
        super().__init__(self.message)

# Convert a field, offset, width triplet to a register value
def fld2reg(reg_width, fld_dat, offset, fld_width):
    # Start with a zeroed value of 'x' with the specified bus width
    reg = 0
    
    # Create a mask to clear 'width' bits starting from 'offset'
    mask = (1 << fld_width) - 1  # Mask with 'width' bits set to 1
    mask = mask << offset  # Shift the mask to the desired offset position

    # Clear the target bits in 'x' (though it's already zeroed out)
    reg_cleared = reg & ~mask  # This will have no effect since x is zero

    # Shift 'y' to the correct position and insert it into 'x'
    fld_shifted = fld_dat << offset

    # Combine the cleared 'x' with the shifted 'y'
    reg = reg_cleared | fld_shifted

    # Ensure the result does not exceed the bus width
    reg = reg & ((1 << reg_width) - 1)  # Apply the bus width mask

    return reg

# parse register data, field offset and field width to get field data
def reg2fld(reg: int, offset: int, width: int)->int:
    mask = (1<<width)-1
    fld = (reg>>offset) & mask
    return fld

# Get field's strobe and address out of a name
def fld2loc(fld_name: str, rgf_dict: dict, rgf_name: str='rgf'):
    for fld in rgf_dict[rgf_name]:
        if fld['name'] == fld_name:
            address, strobe, offset, width = fld['address'], fld['strobe'], fld['offset'], fld['width']
            address = int(address, 16)
            return address, strobe, offset, width
    raise FieldNotFoundError(field_name=fld_name)

# Get field's name from strobe+address pair
def loc2fld(paddr: int, pstrb: int, bus_width: int, rgf_dict: dict, rgf_name: str='rgf'):
    for fld in rgf_dict[rgf_name]:
        strb_width = int(bus_width / 8)
        binary_string = bin(pstrb)[2:]
        padded_binary = binary_string.zfill(strb_width)
        strobe = [bit == '1' for bit in padded_binary]
        strobe = strobe[::-1]
        address = hex(paddr)
        if fld['address'] == address and fld['strobe']==strobe:
            return fld['name'], fld['offset'], fld['width']
    raise FieldNotFoundError(fld_addr=address, fld_strobe=strobe)

# APB Transaction Class
class APBTransaction(object):
    '''
        APB Transaction Class
            * gets field's full name + data if this is a write transaction
            * Looks up the register dictionary to find the field's name
            * Converts the field's name + address + strobe to a transaction
            * Defines print, equal and other functions
    '''
    def __init__(self, field_name: str, rgf_dict: dict, fld_data: int=None, write: bool=False, bus_width: int=32, address_width: int=8):
        self.field_name = field_name
        self.reg_address, self.reg_strobe, self.fld_offset, self.fld_width = fld2loc(field_name, rgf_dict)
        self.write = write
        self.reg_width = bus_width
        if fld_data is not None:
            self.reg_data = fld2reg(self.reg_width, fld_data, self.fld_offset, self.fld_width)
            self.fld_data = fld_data
        else:
            self.reg_data = None
            self.fld_data = None
        self.address_width = address_width
        self.start_time = None
        self.rgf_dict = rgf_dict

    # print transaction
    def print(self):
        direction_str = 'WRITE' if self.write else 'READ'
        strobe_str = ''
        for strb in self.reg_strobe:
            strobe_str += str(int(strb))
        strobe_str = strobe_str[::-1]

        print('-'*120)
        print('APB Transaction - ', end='')
        if self.start_time:
            print('Started at %d ns' % self.start_time)
        else:
            print('Has not occurred yet')
        print('')

        print('  Field:      %s' % self.field_name)
        print('  Address:    0x%08X' % self.reg_address)
        print('  Strobe:     0b%s' % strobe_str)
        print('  Direction:  %s' % direction_str)
        

        if self.reg_data != None:
            print('  Reg Data:   0x%0*X ' % (int(self.reg_width/4),self.reg_data))
            print('  Field Data: 0x%0*X ' % (int(self.fld_width/4),self.fld_data))
        else:
            print('NO DATA YET!')

        print('-'*120)
    
    # override equal operator
    def __eq__(self, other):

        # compare each field
        fail = False
        fail = fail or not (self.reg_address == other.reg_address)
        fail = fail or not (self.write == other.write)
        fail = fail or not (self.fld_data == other.fld_data)

        # return response
        return not fail
    
    # override not-equal operator
    def __ne__(self, value):
        return not self.__eq__(value)

# APB Monitor Class
class APBMonitor(BusMonitor):
    '''
        APB Monitor
            * listen to the APB bus for valid transactions
    '''
    # override BusMonitor's _signals attribute
    _signals = ['paddr', 'pprot', 'psel', 'penable', 'pwrite', 'pwdata', 'pstrb', 'pwakeup', 'pready', 'prdata', 'pslverr']

    # init monitor
    def __init__(self, entity, name, clock, rgf_dict: dict, bus_width=32, reset=None, reset_n=None, callback=None, event=None, **kwargs):
        super().__init__(entity, name, clock, reset, reset_n, callback, event, **kwargs)
        self.clock = clock
        self.bus_width = bus_width
        self.rgf_dict = rgf_dict

    # monitor main coro
    async def _monitor_recv(self):
        
        await RisingEdge(self.clock)
        while True:
            
            await ReadOnly()

            # both slave and master are ready for transfer
            if self.bus.psel.value and self.bus.penable.value and self.bus.pready.value:

                # retrieve the data and strobe from the bus
                address = self.bus.paddr.value
                strobe = self.bus.pstrb.value

                # get either read or write data                
                write = True if self.bus.pwrite.value else False
                reg_data = self.bus.pwdata.value if write else self.bus.prdata.value

                # store the transaction object
                fld_name, fld_offset, fld_width = loc2fld(address, strobe, self.bus_width, self.rgf_dict)
                fld_data = reg2fld(reg_data, fld_offset, fld_width)
                transaction = APBTransaction(fld_name, self.rgf_dict, fld_data, write)
                transaction.start_time = cocotb.utils.get_sim_time('ns')

                # signal to the callback
                self._recv(transaction)

            # begin next cycle
            await RisingEdge(self.clock)
            
# APB Master Driver Class
class APBMasterDriver(BusDriver):
    '''
        APB Master Driver Class
            * new transactions are appended to a transaction queue
            * if the transaction queue transitions from empty to not-empty, a _tx_pipe coro is forked
    '''
    
    # override BusDriver's _signals attribute
    _signals = ['paddr', 'pprot', 'psel', 'penable', 'pwrite', 'pwdata', 'pstrb', 'pwakeup', 'pready', 'prdata', 'pslverr']

    # init
    def __init__(self, entity, name, clock, **kwargs):
        super().__init__(entity, name, clock, **kwargs)
        self.bus.penable.value = 0 
        self.bus.pwrite.value = 0 
        self.bus.paddr.value = 0 
        self.bus.psel.value = 0 
        self.bus.pwdata.value = 0 
        self.bus.pstrb.value = 0 
        self.tx_coro = None
        self.tx_q = deque()
        self.clock = clock
    
    # transmition pipeline
    async def _tx_pipe(self):
        
        state = 'SETUP'

        while (len(self.tx_q)!=0) or state != 'IDLE':

            # setup phase
            if state=='SETUP':

                # pop transaction
                curr_tx = self.tx_q.popleft()
                curr_tx.start_time = cocotb.utils.get_sim_time('ns')

                # assign values
                self.bus.psel.value = 1 
                self.bus.paddr.value = curr_tx.reg_address
                self.bus.pwrite.value = 1 if curr_tx.write else 0

                # strobe logic
                pstrb_int = 0
                for i, pstrb_i in enumerate(curr_tx.reg_strobe):
                    pstrb_int += pstrb_i << i
                self.bus.pstrb.value = pstrb_int

                # drive data bus
                if curr_tx.write:
                    self.bus.pwdata.value = curr_tx.reg_data
                
                # move to next state
                state = 'ACCESS'
            
            # access phase
            elif state=='ACCESS':

                self.bus.penable.value = 1 

                state = 'SAMPLE'
            
            await RisingEdge(self.clock)

            # sample phase
            if state=='SAMPLE': 

                # check if the slave is ready
                if self.bus.pready.value == 1:
                    
                    # sample data
                    if not curr_tx.write:
                        curr_tx.reg_data = self.bus.prdata.value

                    # next state logic
                    if len(self.tx_q)==0:
                        state = 'IDLE'
                    else:
                        state = 'SETUP'
                    
                    # de-assert enable
                    self.bus.penable.value = 0 
            
        # reset the bus
        self.bus.pwdata.value = 0 
        self.bus.pwrite.value = 0 
        self.bus.psel.value = 0 
        self.bus.penable.value = 0 
    
    # override _driver_send
    async def _driver_send(self, transaction: APBTransaction, sync: bool=True):
        
        self.tx_q.append(transaction)

        if not self.tx_coro:
            self.tx_coro = cocotb.start_soon(self._tx_pipe())
