#Usage:
##A small compression program that uses  Lempel–Ziv–Welch (LZW) algorithm
#to compress a file 
#compressor = Compress()
#compressor.compress('path_to_file')
#
#to decompress a .lzw file
#supports only decompression of data with .lzw extenstion(compressed with the same program)
#decompressor = Decompress()
#decompressor.decompress('path_to_lzw_file')

import struct

CLEAR_CODE = 256
END_OF_CODE = 257
INITIAL_TABLE_SIZE = 258
MAX_BITS = 12
MIN_BITS = 9
def bits_to_int(bit_source):

    index  = 0
    result = 0
    for bit in bit_source[::-1]:

        result = result + bit * (2 ** index)
        index = index + 1

    return result
        
def int_to_bits(number,width=None):

    remains = number
    result = []

    while remains != 0:
        
        result.append(remains % 2)
        remains = remains // 2

    result = result[::-1]

    if width:
        add_on = [0] * (width - len(result))
        result = add_on + result

    return result

def unpack_byte(b):
    (ret,) = struct.unpack("B", b)
    return ret 

def bytes_to_bits(byte_source):

    unpacked_bits = []
    
    for byte in byte_source:

        value = byte

        for index in range(8,0,-1):
            
            bit_index = index - 1
            bit = 1 & (value >> bit_index)
            unpacked_bits.append(bit)

    return unpacked_bits


    


def bits_to_bytes(bits):

    bytes = []
    next_byte = 0
    next_bit = 7

    for bit in bits:

        if bit:
            next_byte = next_byte | (2 ** next_bit)

        if next_bit:
            next_bit = next_bit - 1
        else:
            bytes.append(next_byte)
            next_bit = 7
            next_byte = 0

    if next_bit < 7:
        bytes.append(next_byte)

    return bytes
            

class IntToByte:

    def __init__(self):
        self.packer = struct.Struct('B');
        
    def __int_to_byte(self,i):
        packed = self.packer.pack(i)
        return packed
   
    def int_to_byte_with_dict(self):
        table = dict((self.__int_to_byte(i),i) for i in range(256))
        table[CLEAR_CODE] = CLEAR_CODE
        table[END_OF_CODE] = END_OF_CODE
        return table

    def int_to_byte_with_list(self):
        table = [self.__int_to_byte(i) for i in range(256)]
        table.append(CLEAR_CODE)
        table.append(END_OF_CODE)
        return table
        


class LZWCoder:

    def __init__(self):

        self.__int_to_byte_dict = IntToByte().int_to_byte_with_dict()
        self.__max_code_length = (2 ** MAX_BITS) - 1
        self.__table = []
        
    def __code_lenght(self):
        return len(self.__table)
    
    def __clear_table(self):
        temp_table = dict(self.__int_to_byte_dict)

        return temp_table
        
    def lzw_code(self,bytesource):

        self.__byte_array = bytesource
        self.__table = self.__clear_table()
        output_code = []
        sequence = None

        packer = struct.Struct('B');

        for byte in self.__byte_array:

            byte = packer.pack(byte)

            if sequence == None:
                temp_sequence = byte
                #print('prevcode byte {0}'.format(self.__table[byte]))
            else:
                temp_sequence = sequence + byte

            if temp_sequence in self.__table :
                sequence = temp_sequence
            else:
                output_code.append(self.__table[sequence])
                self.__table[temp_sequence] = len(self.__table)
                sequence = byte

            if self.__code_lenght() == self.__max_code_length - 1:
                output_code.append(self.__table[sequence])
                output_code.append(CLEAR_CODE)
                sequence = None
                self.__table = self.__clear_table()
                
        if sequence != None:
            output_code.append(self.__table[sequence])
        output_code.append(END_OF_CODE)
        #print(output_code)
        
        return output_code
        
            
class LZWDecoder:

    def __init__(self):

        self.__code_to_byte = IntToByte().int_to_byte_with_list()
        self.__table = []
        
    def __code_lenght(self):
        
        return len(self.__table)
    
    def __clear_table(self):
        
        temp_table = list(self.__code_to_byte[:])
        return temp_table
    

    def __is_table_cleared(self):

        return len(self.__table) == INITIAL_TABLE_SIZE

    def lzw_decode(self,lzw_code):
        
        self.__input_code = lzw_code
        self.__table = self.__clear_table()
        #prevcode = self.__input_code[0]
        output = []
        prevcode = -1
        #output.append(self.__table[prevcode])
        packer = struct.Struct('B')
        #print(self.__input_code)

        for code in self.__input_code:

            if self.__is_table_cleared() == True and prevcode == -1:
                prevcode = code
                #print('prevcode {0}'.format(prevcode))
                output.append(self.__table[prevcode])
                continue
            
            if code == CLEAR_CODE:
                self.__table = self.__clear_table()
                prevcode = -1
                #print('clear code')
                continue
            elif code == END_OF_CODE:
                continue
            elif code >= len(self.__table):
                entry = self.__table[prevcode]
                entry += packer.pack(entry[0])
            else:
                entry = self.__table[code]
                
            output.append(entry)
            self.__table.append(self.__table[prevcode] + packer.pack(entry[0]))
            prevcode = code
            
        return output

class CodePacker:

    def __init__(self,table_size):
        
       
        self.__initial_code_length = table_size

    def pack_integers(self,lzw_input_code):

        self.__lzw_code = lzw_input_code
        current_bits = []
        output_bytes = []
        code_length = self.__initial_code_length
        packer = struct.Struct('B')

        minwidth = MIN_BITS
        current_width = minwidth

        for code in self.__lzw_code:

            bits = int_to_bits(code,current_width)
            current_bits = current_bits + bits

            code_length = code_length + 1

            if code == END_OF_CODE:
                while len(current_bits) % 8:
                    current_bits.append(0)

            if  code == CLEAR_CODE:
                current_width = minwidth
                print(code_length)
                code_length = self.__initial_code_length
            elif code_length >= (2 ** current_width):
                current_width = current_width + 1

            while len(current_bits) > 8:
                byte_in_bits = current_bits[:8]
                current_bytes = bits_to_bytes(byte_in_bits)

                for byte in current_bytes:
                    output_bytes.append(packer.pack(byte))

                current_bits = current_bits[8:]

        if current_bits:
              last = bits_to_bytes(current_bits)
              for byte in last:
                output_bytes.append(packer.pack(byte))
                
        return output_bytes

class CodeUnpacker:

    def __init__(self,table_size):
        
        self.__initial_code_length = table_size

    def unpack_bytes(self,input_code):

        self.__packed_byte_code = input_code
        code_length = self.__initial_code_length
        minwidth = MIN_BITS
        current_code_width = minwidth
        
        current_bits = []
        unpacked_code = []
        offset = 0
        ignore = 0

        unpacked_bits = bytes_to_bits(self.__packed_byte_code)

        for bit in unpacked_bits:

            offset = (offset + 1) % 8

            if ignore > 0:
                ignore = ignore - 1
                continue

            current_bits.append(bit)
            
            if len(current_bits) == current_code_width:
                code_value = bits_to_int(current_bits)
                unpacked_code.append(code_value)
                current_bits = []

                code_length = code_length + 1

                if code_value == CLEAR_CODE:
                    print(code_length)
                    current_code_width == minwidth
                    code_length = self.__initial_code_length                  
                else:
                    while code_length >= (2 ** current_code_width):
                        current_code_width = current_code_width + 1

                if code_value == END_OF_CODE:
                    ignore = (8 - offset) % 8

        return unpacked_code
                                        
 
class Compress:
    
    def __init__(self):
        pass
    
    def __write_output(self,file_name,byte_source):
    
        file = open(file_name,"wb")
        
        for byte in byte_source:
            file.write(byte)

        file.close()
    
    def compress(self,file_name):
        
        file = open(file_name,'rb')
        lzw = LZWCoder()
        packer = CodePacker(258)

        buffer = file.read(1024*1024)
        while buffer:
            
            compressed_output = lzw.lzw_code(buffer)  
            compressed_output = packer.pack_integers(compressed_output)
            self.__write_output((file_name + '.lzw'),compressed_output)
            buffer = file.read(1024*1024)
            
        file.close()
        

class Decompress:
    
    def __init__(self):
        self.__decompressed_output = []
     
    def __read_file(self,file_name):
    
        file = open(file_name,'rb')
        buffer = file.read(1024*1024)
        file.close()

        return buffer
        
    def __write_output(self,file_name,byte_source):
    
        file = open(file_name,"wb")
        
        for byte in byte_source:
            file.write(byte)

        file.close()
    
    def decompress(self,file_name):
        
        if file_name[len(file_name) - 4:] != '.lzw':
            print("You have to enter the name of a compressed file")
        else:
            new_file_name = file_name[:len(file_name) - 4]
            file = open(file_name,'rb')
            unpacker = CodeUnpacker(258)
            lzw = LZWDecoder()
                
            buffer = file.read(1024*1024)     
            while buffer:
                self.__decompressed_output = unpacker.unpack_bytes(buffer)
                self.__decompressed_output = lzw.lzw_decode(self.__decompressed_output )
                self.__write_output(new_file_name,self.__decompressed_output)
                buffer = file.read(1024*1024)
                    
            file.close()   
        
        
    
        
        
import struct

CLEAR_CODE = 256
END_OF_CODE = 257
INITIAL_TABLE_SIZE = 258
MAX_BITS = 12
MIN_BITS = 9
def bits_to_int(bit_source):

    index  = 0
    result = 0
    for bit in bit_source[::-1]:

        result = result + bit * (2 ** index)
        index = index + 1

    return result
        
def int_to_bits(number,width=None):

    remains = number
    result = []

    while remains != 0:
        
        result.append(remains % 2)
        remains = remains // 2

    result = result[::-1]

    if width:
        add_on = [0] * (width - len(result))
        result = add_on + result

    return result

def unpack_byte(b):
    (ret,) = struct.unpack("B", b)
    return ret 

def bytes_to_bits(byte_source):

    unpacked_bits = []
    
    for byte in byte_source:

        value = byte

        for index in range(8,0,-1):
            
            bit_index = index - 1
            bit = 1 & (value >> bit_index)
            unpacked_bits.append(bit)

    return unpacked_bits


    


def bits_to_bytes(bits):

    bytes = []
    next_byte = 0
    next_bit = 7

    for bit in bits:

        if bit:
            next_byte = next_byte | (2 ** next_bit)

        if next_bit:
            next_bit = next_bit - 1
        else:
            bytes.append(next_byte)
            next_bit = 7
            next_byte = 0

    if next_bit < 7:
        bytes.append(next_byte)

    return bytes
            

class IntToByte:

    def __init__(self):
        self.packer = struct.Struct('B');
        
    def __int_to_byte(self,i):
        packed = self.packer.pack(i)
        return packed
   
    def int_to_byte_with_dict(self):
        table = dict((self.__int_to_byte(i),i) for i in range(256))
        table[CLEAR_CODE] = CLEAR_CODE
        table[END_OF_CODE] = END_OF_CODE
        return table

    def int_to_byte_with_list(self):
        table = [self.__int_to_byte(i) for i in range(256)]
        table.append(CLEAR_CODE)
        table.append(END_OF_CODE)
        return table
        


class LZWCoder:

    def __init__(self):

        self.__int_to_byte_dict = IntToByte().int_to_byte_with_dict()
        self.__max_code_length = (2 ** MAX_BITS) - 1
        self.__table = []
        
    def __code_lenght(self):
        return len(self.__table)
    
    def __clear_table(self):
        temp_table = dict(self.__int_to_byte_dict)

        return temp_table
        
    def lzw_code(self,bytesource):

        self.__byte_array = bytesource
        self.__table = self.__clear_table()
        output_code = []
        sequence = None

        packer = struct.Struct('B');

        for byte in self.__byte_array:

            byte = packer.pack(byte)

            if sequence == None:
                temp_sequence = byte
                #print('prevcode byte {0}'.format(self.__table[byte]))
            else:
                temp_sequence = sequence + byte

            if temp_sequence in self.__table :
                sequence = temp_sequence
            else:
                output_code.append(self.__table[sequence])
                self.__table[temp_sequence] = len(self.__table)
                sequence = byte

            if self.__code_lenght() == self.__max_code_length - 1:
                output_code.append(self.__table[sequence])
                output_code.append(CLEAR_CODE)
                sequence = None
                self.__table = self.__clear_table()
                
        if sequence != None:
            output_code.append(self.__table[sequence])
        output_code.append(END_OF_CODE)
        #print(output_code)
        
        return output_code
        
            
class LZWDecoder:

    def __init__(self):

        self.__code_to_byte = IntToByte().int_to_byte_with_list()
        self.__table = []
        
    def __code_lenght(self):
        
        return len(self.__table)
    
    def __clear_table(self):
        
        temp_table = list(self.__code_to_byte[:])
        return temp_table
    

    def __is_table_cleared(self):

        return len(self.__table) == INITIAL_TABLE_SIZE

    def lzw_decode(self,lzw_code):
        
        self.__input_code = lzw_code
        self.__table = self.__clear_table()
        #prevcode = self.__input_code[0]
        output = []
        prevcode = -1
        #output.append(self.__table[prevcode])
        packer = struct.Struct('B')
        #print(self.__input_code)

        for code in self.__input_code:

            if self.__is_table_cleared() == True and prevcode == -1:
                prevcode = code
                #print('prevcode {0}'.format(prevcode))
                output.append(self.__table[prevcode])
                continue
            
            if code == CLEAR_CODE:
                self.__table = self.__clear_table()
                prevcode = -1
                #print('clear code')
                continue
            elif code == END_OF_CODE:
                continue
            elif code >= len(self.__table):
                entry = self.__table[prevcode]
                entry += packer.pack(entry[0])
            else:
                entry = self.__table[code]
                
            output.append(entry)
            self.__table.append(self.__table[prevcode] + packer.pack(entry[0]))
            prevcode = code
            
        return output

class CodePacker:

    def __init__(self,table_size):
        
       
        self.__initial_code_length = table_size

    def pack_integers(self,lzw_input_code):

        self.__lzw_code = lzw_input_code
        current_bits = []
        output_bytes = []
        code_length = self.__initial_code_length
        packer = struct.Struct('B')

        minwidth = MIN_BITS
        current_width = minwidth

        for code in self.__lzw_code:

            bits = int_to_bits(code,current_width)
            current_bits = current_bits + bits

            code_length = code_length + 1

            if code == END_OF_CODE:
                while len(current_bits) % 8:
                    current_bits.append(0)

            if  code == CLEAR_CODE:
                current_width = minwidth
                print(code_length)
                code_length = self.__initial_code_length
            elif code_length >= (2 ** current_width):
                current_width = current_width + 1

            while len(current_bits) > 8:
                byte_in_bits = current_bits[:8]
                current_bytes = bits_to_bytes(byte_in_bits)

                for byte in current_bytes:
                    output_bytes.append(packer.pack(byte))

                current_bits = current_bits[8:]

        if current_bits:
              last = bits_to_bytes(current_bits)
              for byte in last:
                output_bytes.append(packer.pack(byte))
                
        return output_bytes

class CodeUnpacker:

    def __init__(self,table_size):
        
        self.__initial_code_length = table_size

    def unpack_bytes(self,input_code):

        self.__packed_byte_code = input_code
        code_length = self.__initial_code_length
        minwidth = MIN_BITS
        current_code_width = minwidth
        
        current_bits = []
        unpacked_code = []
        offset = 0
        ignore = 0

        unpacked_bits = bytes_to_bits(self.__packed_byte_code)

        for bit in unpacked_bits:

            offset = (offset + 1) % 8

            if ignore > 0:
                ignore = ignore - 1
                continue

            current_bits.append(bit)
            
            if len(current_bits) == current_code_width:
                code_value = bits_to_int(current_bits)
                unpacked_code.append(code_value)
                current_bits = []

                code_length = code_length + 1

                if code_value == CLEAR_CODE:
                    print(code_length)
                    current_code_width == minwidth
                    code_length = self.__initial_code_length                  
                else:
                    while code_length >= (2 ** current_code_width):
                        current_code_width = current_code_width + 1

                if code_value == END_OF_CODE:
                    ignore = (8 - offset) % 8

        return unpacked_code
                                        
 
class Compress:
    
    def __init__(self):
        pass
    
    def __write_output(self,file_name,byte_source):
    
        file = open(file_name,"wb")
        
        for byte in byte_source:
            file.write(byte)

        file.close()
    
    def compress(self,file_name):
        
        file = open(file_name,'rb')
        lzw = LZWCoder()
        packer = CodePacker(258)

        buffer = file.read(1024*1024)
        while buffer:
            
            compressed_output = lzw.lzw_code(buffer)  
            compressed_output = packer.pack_integers(compressed_output)
            self.__write_output((file_name + '.lzw'),compressed_output)
            buffer = file.read(1024*1024)
            
        file.close()
        

class Decompress:
    
    def __init__(self):
        self.__decompressed_output = []
     
    def __read_file(self,file_name):
    
        file = open(file_name,'rb')
        buffer = file.read(1024*1024)
        file.close()

        return buffer
        
    def __write_output(self,file_name,byte_source):
    
        file = open(file_name,"wb")
        
        for byte in byte_source:
            file.write(byte)

        file.close()
    
    def decompress(self,file_name):
        
        if file_name[len(file_name) - 4:] != '.lzw':
            print("You have to enter the name of a compressed file")
        else:
            new_file_name = file_name[:len(file_name) - 4]
            file = open(file_name,'rb')
            unpacker = CodeUnpacker(258)
            lzw = LZWDecoder()
                
            buffer = file.read(1024*1024)     
            while buffer:
                self.__decompressed_output = unpacker.unpack_bytes(buffer)
                self.__decompressed_output = lzw.lzw_decode(self.__decompressed_output )
                self.__write_output(new_file_name,self.__decompressed_output)
                buffer = file.read(1024*1024)
                    
            file.close()   
        

    
        
