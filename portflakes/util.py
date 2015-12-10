def parse_8bit(user_input):
    return user_input.encode('ascii').decode('unicode_escape').encode('latin1')


def decode_8bit(raw):
    return raw.decode('unicode_escape')
