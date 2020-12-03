# CPU registers

registers = bytearray(2 * 6)

r8keys = {
    'A': 0, 'F': 1,
    'B': 2, 'C': 3,
    'D': 4, 'E': 5,
    'H': 6, 'L': 7,
}

r16keys = {
    'AF': 0, 'BC': 2,
    'DE': 4, 'HL': 6,
    'PC': 8, 'SP': 10,
}

flag_keys = {
    'Z': 7,
    'N': 6,
    'H': 5,
    'C': 4,
}


# memory

memory = bytearray(2 ** 16)


# accessor classes

class r8Meta(type):

    def __getitem__(cls, key):
        if key not in r8keys:
            raise KeyError(key)
        return registers[r8keys[key]]

    def __setitem__(cls, key, value):
        if key not in r8keys:
            raise KeyError(key)
        if int != type(value) or not -0x80 <= value <= 0xff:
            raise ValueError(value)
        registers[r8keys[key]] = value & 0xff

    def __getattr__(cls, name):
        return cls[name]

    def __setattr__(cls, name, value):
        cls[name] = value


class r8(metaclass=r8Meta):
    pass


class r16Meta(type):

    def __getitem__(cls, key):
        if key not in r16keys:
            raise KeyError(key)
        i = r16keys[key]
        return int.from_bytes(registers[i:2+i], 'big')

    def __setitem__(cls, key, value):
        if key not in r16keys:
            raise KeyError(key)
        if int != type(value) or not -0x8000 <= value <= 0xffff:
            raise ValueError(value)
        i = r16keys[key]
        registers[i:2+i] = int.to_bytes(value & 0xffff, 2, 'big')

    def __getattr__(cls, name):
        return cls[name]

    def __setattr__(cls, name, value):
        cls[name] = value


class r16(metaclass=r16Meta):
    pass


class flagMeta(type):

    def __getitem__(cls, key):
        if key not in flag_keys:
            raise KeyError(key)
        return bool(r8.F >> flag_keys[key] & 1)

    def __setitem__(cls, key, value):
        if key not in flag_keys:
            raise KeyError(key)
        if bool != type(value):
            raise ValueError(value)
        i = flag_keys[key]
        r8.F = r8.F & ~(1 << i) | value << i

    def __getattr__(cls, name):
        return cls[name]

    def __setattr__(cls, name, value):
        cls[name] = value


class flag(metaclass=flagMeta):
    pass


class mem8Meta(type):

    def __getitem__(self, key):
        if int != type(key) or not 0 <= key <= 0x10000 - 1:
            raise KeyError(key)
        return memory[key]

    def __setitem__(self, key, value):
        if int != type(key) or not 0 <= key <= 0x10000 - 1:
            raise KeyError(key)
        if int != type(value) or not 0x00 <= value <= 0xff:
            raise ValueError(value)
        memory[key] = value


class mem8(metaclass=mem8Meta):
    pass


class mem16Meta(type):

    def __getitem__(self, key):
        if int != type(key) or not 0 <= key <= 0x10000 - 2:
            raise KeyError(key)
        return int.from_bytes(memory[key:2+key], 'little')

    def __setitem__(self, key, value):
        if int != type(key) or not 0 <= key <= 0x10000 - 2:
            raise KeyError(key)
        if int != type(value) or not 0 <= value <= 0xffff:
            raise ValueError(value)
        memory[key:2+key] = int.to_bytes(value, 2, 'little')


class mem16(metaclass=mem16Meta):
    pass


class mem32Meta(type):

    def __getitem__(self, key):
        if int != type(key) or not 0 <= key <= 0x10000 - 4:
            raise KeyError(key)
        return int.from_bytes(memory[key:4+key], 'little')

    def __setitem__(self, key, value):
        if int != type(key) or not 0 <= key <= 0x10000 - 4:
            raise KeyError(key)
        if int != type(value) or not 0 <= value <= 0xffffffff:
            raise ValueError(value)
        memory[key:4+key] = int.to_bytes(value, 4, 'little')


class mem32(metaclass=mem32Meta):
    pass
