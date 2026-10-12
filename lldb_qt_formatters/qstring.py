from lldb import SBError, SBValue


def format_summary(valobj: SBValue, internal_dict, options):
    """
    Format a summary string for QString values

    :param valobj:
    :param internal_dict: unused
    :param options: unused
    """
    if not valobj.process:
        return "Unknown"

    data_member = valobj.GetChildMemberWithName("d")
    ptr_member = data_member.GetChildMemberWithName("ptr")

    if ptr_member.IsValid():
        # Qt6: d is a QArrayDataPointer<char16_t> that holds ptr and size directly
        address = ptr_member.GetValueAsUnsigned()
        string_length = data_member.GetChildMemberWithName("size").GetValueAsUnsigned()
    else:
        # Qt5: d points to a QArrayData header, the characters start at d + offset
        array_member = data_member.deref
        offset_in_bytes = array_member.GetChildMemberWithName("offset").GetValueAsUnsigned()
        string_length = array_member.GetChildMemberWithName("size").GetValueAsUnsigned()
        address = data_member.GetValueAsUnsigned() + offset_in_bytes

    if string_length == 0:
        return '""'
    # Uninitialized variables (e.g. before their declaration line) hold garbage
    if address == 0 or string_length > (1 << 20):
        return "<invalid>"

    error = SBError()
    character_size = 2
    content = valobj.process.ReadMemory(address, string_length * character_size, error)
    if error.Fail():
        return "<unreadable>"

    return f'"{bytearray(content).decode("utf-16", errors="replace")}"'
