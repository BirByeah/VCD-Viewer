import sys
import re
import matplotlib.pyplot as plt

class VCD_Parser:
    date_format = ["week", "month", "day", "time", "year"]
    version_format = ["type", "fix_version", 'version number']
    def __init__(self, filename) -> None:
        self.filename = filename
        self.vcd_content = None
        self.vcd_content_len = 0
        self.signal_len = 0
        self.signals = {}
        self.header_info = dict(filename=filename)
        self.__content_index = 0
        
        self.__load_file()
        
    def __load_file(self) -> None:
        """
        get the list of items in the vcd file.
        """
        with open(self.filename, 'r') as f:
            content_rl = f.readlines()
            content_str = "".join(content_rl)
            self.vcd_content = content_str.split()
            self.vcd_content_len = len(self.vcd_content)
            del content_str, content_rl
        self.__parse_header()
        self.__parse_module()
        self.__parse_signal()
        self.__process_signals()
       
    @property 
    def content(self) -> tuple:
        return (self.header_info, self.signals)
            
    def __key_finder(self, key:str, interrupt:str = None) -> None:
        """
        find the key you want, and then it will move forward to the first real infos

        Args:
            key (str): the key you want to find

        Raises:
            IndexError: when the key was not found
        """
        while self.vcd_content[self.__content_index] != key:
            self.__content_index += 1
            if self.__content_index == self.vcd_content_len:
                raise IndexError("Key %s not found" % key)
        self.__content_index += 1
        
        # to avoid end with '$end'
        while self.vcd_content[self.__content_index] == "$end":
            self.__content_index += 1
            
    def __interrupt_key_finder(self, key:str, interrupt:str) -> bool:
        """
        a key finder that can be interrupted by certain words

        Args:
            key (str): the key you want to find
            interrupt (str): the key that interrupts this finding

        Raises:
            IndexError: _description_

        Returns:
            bool: if True, no interrupt was found; if False, one interrupt happened.
        """
        while self.vcd_content[self.__content_index] != key:
            self.__content_index += 1
            if interrupt is not None:
                if self.vcd_content[self.__content_index] == interrupt:
                    return False
            if self.__content_index == self.vcd_content_len:
                raise IndexError("Key %s not found" % key)
        self.__content_index += 1
        
        # to avoid end with '$end'
        while self.vcd_content[self.__content_index] == "$end":
            self.__content_index += 1
        return True
            
    def __parse_header(self) -> None:
        """
        get header info
        """
        self.__content_index = 0
        info = ["date", "version", "timescale"]
        pattern = r'(\d+)([a-zA-Z]+)'
        for key in info:
            self.__key_finder(f"${key}")
            if key == "date":
                self.header_info[key] = dict(zip(VCD_Parser.date_format, self.vcd_content[self.__content_index:self.__content_index + len(VCD_Parser.date_format)]))
            elif key == "version":
                self.header_info[key] = dict(zip(VCD_Parser.version_format, self.vcd_content[self.__content_index:self.__content_index + len(VCD_Parser.version_format)]))
            elif key == "timescale":
                matchs = re.match(pattern, self.vcd_content[self.__content_index])
                if matchs is None:
                    raise LookupError("%s does not match the pattern %s" % (self.vcd_content[self.__content_index], pattern))
                self.header_info[key] = int(matchs.group(1))
                self.header_info['timeunit'] = matchs.group(2)
        # print(self.header_info)
    
    def __parse_module(self) -> None:
        self.__key_finder('$scope')
        while self.__interrupt_key_finder('$var', '$scope'):
            type = self.vcd_content[self.__content_index]
            bit_width = self.vcd_content[self.__content_index + 1]
            id = self.vcd_content[self.__content_index + 2]
            name = self.vcd_content[self.__content_index + 3]
            self.signals[id] = dict(type=type, bit_width=bit_width, name=name, signal=[])
        while self.__interrupt_key_finder('$var', '$upscope'):
            type = self.vcd_content[self.__content_index]
            bit_width = self.vcd_content[self.__content_index + 1]
            id = self.vcd_content[self.__content_index + 2]
            name = self.vcd_content[self.__content_index + 3]
            self.signals[id] = dict(type=type, bit_width=bit_width, name=name, signal=[])
        self.__key_finder("$enddefinitions")
        # print(self.signals)
    
    def __parse_signal(self) -> None:
        first_time = True
        current_time = 0
        pattern_time = r"^#(\d+)"
        pattern_signal = r"^([\d+xt])(\S)"
        while self.__content_index < self.vcd_content_len:
            match_time = re.match(pattern_time, self.vcd_content[self.__content_index])
            match_signal = re.match(pattern_signal, self.vcd_content[self.__content_index])
            if self.vcd_content[self.__content_index] == '$dumpvars':
                pass
            elif self.vcd_content[self.__content_index] == '$end':
                first_time = False
            elif match_time is not None:
                temp_time = int(f"0{match_time.group(1)}")
                if not first_time:
                    for index in range(current_time, temp_time):
                        for value in self.signals.values():
                            value['signal'].append(value['signal'][index])
                current_time = temp_time
                self.signal_len = temp_time + 1
            elif match_signal is not None:
                if first_time:
                    self.signals[match_signal.group(2)]['signal'].append(match_signal.group(1))
                else:
                    self.signals[match_signal.group(2)]['signal'][current_time] = match_signal.group(1)
            elif re.match('b\d+', self.vcd_content[self.__content_index]) is not None and re.match('\S+', self.vcd_content[self.__content_index + 1]):
                if first_time:
                    self.signals[self.vcd_content[self.__content_index + 1]]['signal'].append(f'0{self.vcd_content[self.__content_index]}')
                else:
                    self.signals[self.vcd_content[self.__content_index + 1]]['signal'][current_time] = f'0{self.vcd_content[self.__content_index]}'
                self.__content_index += 1
            else:
                print(self.vcd_content[self.__content_index])
                raise LookupError(f'{self.vcd_content[self.__content_index]} does not match time or signal')
            self.__content_index += 1
        self.header_info['signal_len'] = self.signal_len
        # print(self.signals)
        
    def __process_signals(self) -> None:
        temp_signal = {}
        for value in self.signals.values():
            if value['name'] in temp_signal.keys():
                continue
            temp_signal[value['name']] = dict(type=value['type'], bit_width=int(value['bit_width']), signal=value['signal'])
        self.signals = temp_signal
        self.header_info['signal_num'] = len(self.signals)
        
class VCD_Viewer:
    signal_height = 1
    signal_interval = 0.5
    def __init__(self, header_res:dict, signal_res:dict) -> None:
        self.signals = signal_res
        self.header = header_res
        
        self.__preprocess()
        self.plot()
        
    def __preprocess(self) -> None:
        for index, value in enumerate(self.signals.values()):
            max_num = pow(2, value['bit_width']) - 1
            value['offset'] = (self.header['signal_num'] - index - 1) * (VCD_Viewer.signal_height + VCD_Viewer.signal_interval)
            for index, sig in enumerate(value['signal']):
                if sig != 'x' and sig != 'z':
                    value['signal'][index] = int(sig, 2) / max_num
    
    def plot(self) -> None:
        current_signal = 0
        next_signal = 0
        color = None
        for key, value in self.signals.items():
            plt.text(-1, value['offset'] + VCD_Viewer.signal_height / 2, key, horizontalalignment='right')
            for i in range(self.header['signal_len']):
                if value['signal'][i] == 'x':
                    current_signal = value['offset'] + VCD_Viewer.signal_height / 2
                    color = 'r'
                    # plt.plot([i, i + 1], [value['offset'] + VCD_Viewer.signal_height / 2] * 2, c='red')
                elif value['signal'][i] == 'z':
                    current_signal = value['offset'] + VCD_Viewer.signal_height / 2
                    color = 'brown'
                    # plt.plot([i, i + 1], [value['offset'] + VCD_Viewer.signal_height / 2] * 2, c='brown')
                else:
                    current_signal = value['offset'] + value['signal'][i]
                    color = 'b'
                plt.plot([i * self.header['timescale'], (i + 1) * self.header['timescale']], [current_signal] * 2, c=color)
                if i < self.header['signal_len'] - 1:
                    if value['signal'][i + 1] == 'x':
                        next_signal = value['offset'] + VCD_Viewer.signal_height / 2
                        color = 'r'
                    elif value['signal'][i + 1] == 'z':
                        next_signal = value['offset'] + VCD_Viewer.signal_height / 2
                        color = 'brown'
                    else:
                        next_signal = value['offset'] + value['signal'][i + 1]
                        color = 'b'
                    plt.plot([(i + 1) * self.header['timescale'], (i + 1) * self.header['timescale']], [current_signal, next_signal], c=color)
        plt.xlabel(f'time/{self.header["timeunit"]}')
        plt.xlim([0, self.header['signal_len']])
        plt.yticks([])
        plt.show()        
        
if __name__ == "__main__":
    argv = sys.argv
    if len(argv) == 2:
        filename = argv[1] 
        vcdp = VCD_Parser(filename).content
        VCD_Viewer(*vcdp)
    else:
        print("Usage: python VCD_Viewer.py filename")
    