def parse_8bit(user_input):
    return user_input.encode('ascii').decode('unicode_escape').encode('latin1')
