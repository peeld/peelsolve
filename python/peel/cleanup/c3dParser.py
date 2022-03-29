import struct
import binascii
import os


class C3D(object):
    def __init__(self):
        """Initializes all the variables for the class.
        fp : file parser
        proc_type : processor environment endian format"""
        self.fp = None
        self.header = None
        self.proc_type = None

        self.points = 0
        self.analog = 0
        self.frame1 = 0
        self.frameN = 0
        self.max_interpolation = 0
        self.body_data_offset = 0
        self.frames_per_field = 0
        self.frame_rate = 0

        self.analog_frames = 0
        self.point_frames = 0
        self.scale_factor = 1.0
        self.post_scale = 1.0

        self.timecode_used = False
        self.timecode_dropframe = False
        self.timecode_fieldNumbers = []
        self.timecode_standard = 30
        self.timecode_subframesample = 0
        self.timecode_offset = 0
        self.timecode = []

        self.group_dict = {}
        self.data = {}

    def conform(self, value):

        if self.proc_type == 86:
            # big endian - mips
            return struct.unpack('>h', value)
        else:
            # little endian - itel/dec
            return struct.unpack('<h', value)

    def to_float(self, value):

        ret = ""

        if self.proc_type == 84:
            return struct.unpack('f', value)[0]

        elif self.proc_type == 85:
            # 2 3 0 1
            t = list(struct.unpack("4B", value))
            #print([hex(i) for i in t])
            if t[0] or t[1] or t[2] or t[3]:
                t[1] = t[1] - 1
            tt = struct.pack("4B", t[2], t[3], t[0], t[1])
            #print([hex(i) for i in tt])

            return struct.unpack("<f", tt)[0]

        elif self.proc_type == 86:
            # 3 2 1 0
            t = struct.unpack("4B", value)
            tmp2 = struct.pack("4B", t[3], t[2], t[1], t[0])

            ret += value[3]
            ret += value[2]
            ret += value[1]
            ret += value[0]

        else:
            raise ValueError("Unknown data type: " + str(self.proc_type))

        return struct.unpack('f', ret)[0]

    def read_byte(self):
        return struct.unpack('b', self.fp.read(1))[0]

    def read_ubyte(self):
        return struct.unpack('B', self.fp.read(1))[0]

    def read_short(self):
        return struct.unpack('h', self.fp.read(2))[0]

    def read_float(self):
        return self.to_float(self.fp.read(4))

    def load(self, file_name):
        self.fp = open(file_name, 'rb')              # opens file in binary format.

    def close(self):
        if self.fp:
            self.fp.close()

    def read_header(self):
        """
        As per the C3D User Guide (refer pg 37), when reading 2 bytes at a time, the sequence of words in a C3D file
        contain the following:
        Word 1: Byte 1 : pointer to first parameter block, defines the endian format of the C3D file
                Byte 2 : always 0x50h (decimal 80), indicating that the file is written in the ADTech format.
        Words 2 to 11: refer to in-line comments.
        """
        self.header = self.fp.read(2)                # read two-bytes at a time.
        #h1 = struct.unpack('b', self.header[0])[0]
        #h2 = struct.unpack('b', self.header[1])[0]
        h1 = self.header[0]
        h2 = self.header[1]
        if ord(h1) != 2 and ord(h2) != 80:
            print(str(h1))
            print(str(h2))
            raise RuntimeError("Invalid c3d file")

        # header
        self.points = self.read_short()              # 2 Number of 3D points in the file
        self.analog = self.read_short()              # 3 Number of analog measurements per 3D frame
        self.frame1 = self.read_short()              # 4 First frame of raw data
        self.frameN = self.read_short()              # 5 Last frame of raw data
        self.max_interpolation = self.read_short()   # 6 Maximum interpolation gap in 3D frames
        self.scale_factor = self.fp.read(4)          # 7-8 Scale factor: converts signed int 3D data to ref system unit
        self.body_data_offset = self.read_short()    # 9 Number of the first block of the analog-and-3D-data section
        self.frames_per_field = self.read_short()    # 10 Number of analog samples per 3D frame
        self.frame_rate = self.fp.read(4)            # 11-12 Frame rate in Hz

        param_data_offset = struct.unpack_from('b', self.header, 0)[0]

        self.fp.seek(param_data_offset * 256)

        param_header = self.fp.read(4)
        param_blocks = param_header[2]

        # 84 - Intel,  85 - DEC,  86 - MIPS(SGI)
        self.proc_type = struct.unpack_from('b', param_header, 3)[0]

        self.frame_rate = self.to_float(self.frame_rate)
        #

        last_param = False

        while not last_param:

            num_char = self.read_byte()

            if num_char < 0:
                num_char = -num_char
                param_locked = True
            else:
                param_locked = False

            param_group_id = self.read_byte()

            param_name = None
            if num_char > 0:
                param_name = self.fp.read(num_char).decode("ascii").strip()

            current_pos = self.fp.tell()

            next_offset = self.read_short()

            if next_offset <= 0:
                last_param = True

                if param_name is None:
                    break

            if param_group_id < 0:
                newGroup = {}
                self.group_dict[-param_group_id] = newGroup
                # print "GROUP: %d " % param_group_id + str(param_name)
                self.data[param_name] = newGroup
            else:
                param_dict = self.group_dict[param_group_id]
                param_dict[param_name] = self.read_param()

            self.fp.seek(current_pos + next_offset, 0)

    def read_data(self):

        self.fp.seek((self.body_data_offset-1)*512, os.SEEK_SET)

        scale_value = self.to_float(self.scale_factor)

        size_marker = self.points
        size_analog = self.analog

        if scale_value < 0:
            size_marker *= 16
            size_analog *= 4
        else:
            size_marker *= 8
            size_analog *= 2

        data = []

        for i in range(self.frameN - self.frame1):

            if size_marker > 0:

                for mark_n in range(self.points):

                    if scale_value < 0.0:

                        valx = self.read_float()
                        valy = self.read_float()
                        valz = self.read_float()
                        extra = self.read_float()

                        if valx == 0.0 and valy == 0.0 and valz == 0.0:
                            continue

                        #print(valx, valy, valz, extra)

                    else:

                        valx = self.fp.read(2) * self.scale_factor
                        valy = self.fp.read(2) * self.scale_factor
                        valz = self.fp.read(2) * self.scale_factor
                        extra = self.fp.read(2)

                    if len(data) <= mark_n:
                        data.append([])

                    data[mark_n].append((valx, valy, valz))

    def read_param(self):

        param_ele = self.read_byte()
        param_dims = self.read_byte()

        # print "PARAM: %d  %d" % (param_ele, param_dims)

        fn = None

        if param_ele == -1 or param_ele == 1:
            fn = self.read_byte

        if param_ele == 2:
            fn = self.read_short

        if param_ele == 4:
            fn = self.read_float

        if fn is None:
            print("Invalid Parameter")
            return

        if param_dims == 0:
            # single
            return fn()

        if param_dims == 1:

            len = self.read_byte()

            if param_ele == -1 or param_ele == 1:
                # string
                return self.fp.read(len).decode("ascii").strip()

            # array
            return [fn() for i in range(abs(len))]

        if param_dims == 2:

            # matrix

            unit_size = self.read_ubyte()
            num_units = self.read_ubyte()

            if param_ele == -1 or param_ele == 1:

                # array of strings

                data = []

                for i in range(num_units):
                    item = self.fp.read(unit_size)
                    data.append(item.decode("ascii").strip())

                return data

            data = []

            for i in range(num_units):
                row = []
                for j in range(unit_size):
                    row.append(fn())
                data.append(row)

            return data

        return None

    def dump(self):

        print("Points:       %d" % self.points)
        print("Analog:       %d" % self.analog)
        print("Frame1:       %d" % self.frame1)
        print("FrameN:       %d" % self.frameN)
        print("Max Interp:   %d" % self.max_interpolation)
        # print("Scale Factor: %f" % self.scale_factor)
        print("data offset   %d" % self.body_data_offset)
        print("frames_field  %d" % self.frames_per_field)
        print("frame_rate    %f" % self.frame_rate)

    def close(self):
        self.fp.close()

    def convert_axis(self):

        if 'MANUFACTURER' in self.data:
            if 'SOFTWARE' in self.data['MANUFACTURER']:
                if self.data['MANUFACTURER']['SOFTWARE'] == "Motive":
                    return True

        return False


def load(c3d_path):
    c3d = C3D()
    c3d.load(c3d_path)
    c3d.read_header()
    c3d.close()
    return c3d


def test():

    import json
    import os.path

    c3d = C3D()
    d = os.path.dirname(__file__)
    d = os.path.join(d, "../data/Josh_ROM_Out-01.c3d")    # revert to this

    d = os.path.abspath(d)
    c3d.read_header(d)
    c3d.dump()

    c3d.read_data()

    c3d.close()

    for group in c3d.data.keys():
        print(group)

        for item in c3d.data[group]:
            print(" " + str(item))


if __name__ == "__main__":
    test()
