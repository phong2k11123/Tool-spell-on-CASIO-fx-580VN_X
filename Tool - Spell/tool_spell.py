# Tool spell 1 line on CASIO fx-580VN X [UPDATE - 21/11/2026 - 4:45 PM]
# Developed by White (Update developer) & AxesMC (Original developer)
import ast
import re
def read_file(path):
    with open(path, encoding="utf-8") as f:
        return ast.literal_eval("{" + f.read() + "}")
def has_letter(h):
    return h is not None and any(c in "ABCDEF" for c in h)
def starts_with_letter(h):
    return h is not None and h[0] in "ABCDEF"
def hex_to_int(h):
    return int(h, 16)
def pair_violates(a, b):
    return hex_to_int(a) * 256 + hex_to_int(b) >= 0x9991
def filter_hex_bytes(bytes_in):
    out = []
    i = 0
    n = len(bytes_in)
    while i < n:
        b = bytes_in[i]
        if b.startswith("F") and i + 1 < n:
            out.append(b)
            out.append(bytes_in[i + 1])
            i += 2
        else:
            out.append(b)
            i += 1
    return out
def fill_section(queue, n_us, n_sl, n_st):
    us = [(None, False)] * n_us
    sl = [(None, False)] * n_sl
    st = [(None, False)] * n_st
    for i in range(n_us):
        if queue:
            us[i] = queue.pop(0)
        else:
            break
    if n_sl >= 1 and queue:
        if starts_with_letter(queue[0][0]):
            sl[0] = ("30", True)
        else:
            sl[0] = queue.pop(0)
    if n_sl >= 2 and queue:
        next_byte = queue[0][0]
        if sl[0][0] == "30":
            sl[1] = queue.pop(0)
        elif pair_violates(sl[0][0], next_byte):
            sl[1] = ("30", True)
        else:
            sl[1] = queue.pop(0)
    pushed = False
    for i in range(n_st):
        if not queue:
            break
        if has_letter(queue[0][0]):
            st[i] = ("30", True)
            pushed = True
        else:
            st[i] = queue.pop(0)
    if pushed and n_sl >= 2 and sl[-1][0] is not None and sl[-1][0].startswith("F"):
        prev = sl[-1]
        sl[-1] = ("30", True)
        queue.insert(0, prev)
    return us, sl, st
def format_section(name, us, sl, st, has_next):
    us_hex = "".join(b for b, _ in us if b is not None)
    sl_hex = "".join(b for b, _ in sl if b is not None)
    st_hex = "".join(b for b, _ in st if b is not None)
    if not us_hex and not sl_hex and not st_hex:
        return None
    prefix = "0000" if name == "A" else ""
    line = f"{name}=1.{prefix}{us_hex}{sl_hex}"
    if st_hex:
        line += f"×10{st_hex}"
    if has_next:
        line += ":"
    return line
def build_units(A, B, C):
    flat = []
    def add_section(section, name):
        us, sl, st = section
        has_content = any(b is not None for g in [us, sl, st] for b, _ in g)
        if not has_content:
            return
        if name in ("B", "C"):
            flat.append(("dot1", None, False))
        for group in [us, sl, st]:
            for b, ins in group:
                if b is not None:
                    flat.append(("byte", b, ins))
    add_section(A, "A")
    add_section(B, "B")
    add_section(C, "C")
    units = []
    i = 0
    while i < len(flat):
        kind, b, ins = flat[i]
        if kind == "dot1":
            units.append(("dot1", "1."))
            i += 1
            continue
        if ins:
            units.append(("ins30", b))
            i += 1
            continue
        if b.startswith("F") and i + 1 < len(flat):
            nk, nb, nins = flat[i + 1]
            if nk == "byte" and not nins:
                units.append(("fxxx", b + nb))
                i += 2
                continue
        units.append(("byte", b))
        i += 1
    return units
def compute_keys(units):
    items = list(units)
    p = len(items)
    keys = []
    while p > 0:
        kind = items[p - 1][0]
        if kind == "ins30":
            keys.append("DEL")
            items.pop(p - 1)
            p -= 1
        elif kind == "dot1":
            keys.append("DEL")
            keys.append("DEL")
            items.pop(p - 1)
            p -= 1
        else:
            keys.append("LEFT")
            p -= 1
    return keys
def format_keys(keys):
    if not keys:
        return ""
    parts = []
    i = 0
    while i < len(keys):
        j = i
        while j < len(keys) and keys[j] == keys[i]:
            j += 1
        n = j - i
        sym = "◀" if keys[i] == "LEFT" else "DEL"
        if n == 1:
            parts.append(f"[{sym}]")
        else:
            parts.append(f"([{sym}])×{n}")
        i = j
    return " ".join(parts)
def assign_hex(input_hex):
    s = "".join(c for c in input_hex if c in "0123456789abcdefABCDEF")
    if len(s) % 2 != 0:
        return "Error: hex length must be even", ""
    bytes_in = [s[i:i + 2].upper() for i in range(0, len(s), 2)] if s else []
    filtered = filter_hex_bytes(bytes_in) if bytes_in else []
    total = len(filtered) + 2
    if total > 22:
        return f"Error: exceeds 20 bytes", ""
    queue = [(b, False) for b in filtered] + [("3C", False), ("23", False)]
    A = fill_section(queue, 3, 2, 1)
    B = fill_section(queue, 5, 2, 1)
    C = fill_section(queue, 5, 2, 1)
    if queue:
        return f"Error: exceeds 20 bytes", ""
    sections = [("A", A), ("B", B), ("C", C)]
    has_content = []
    for name, (us, sl, st) in sections:
        uh = "".join(b for b, _ in us if b is not None)
        sh = "".join(b for b, _ in sl if b is not None)
        th = "".join(b for b, _ in st if b is not None)
        has_content.append(bool(uh or sh or th))
    lines = ["𝒙:"]
    for idx, (name, section) in enumerate(sections):
        has_next = any(has_content[idx + 1:])
        line = format_section(name, *section, has_next)
        if line:
            lines.append(line)
    units = build_units(A, B, C)
    keys = compute_keys(units)
    keys_str = format_keys(keys)
    assign_text = "\n".join(lines)
    return assign_text, keys_str
def assign_to_key(assign_text):
    if not assign_text or assign_text.startswith("Error"):
        return "", ""
    sections = []
    for line in assign_text.split("\n"):
        if "=" not in line:
            continue
        name, rhs = line.split("=", 1)
        name = name.strip()
        if name in ("A", "B", "C"):
            sections.append((name, rhs.strip()))
    if not sections:
        return "", ""
    prefix_map = {
        "A": ["[ALPHA]", "[(-)]"],
        "B": ["[ALPHA]", "[°' \"]"],
        "C": ["[ALPHA]", "[𝒙⁻¹]"],
    }
    parts = []
    for name, rhs in sections:
        parts += prefix_map[name]
        parts += ["[ALPHA]", "[CALC]"]
        i = 0
        while i < len(rhs):
            ch = rhs[i]
            if ch in "0123456789":
                j = i
                while j < len(rhs) and rhs[j] == ch:
                    j += 1
                n = j - i
                if n == 1:
                    parts.append(f"[{ch}]")
                else:
                    parts.append(f"([{ch}])×{n}")
                i = j
            elif ch in "ABCDEF":
                parts.append("[▶]")
                i += 1
            elif ch == "×":
                parts.append("[×10ˣ]")
                if rhs[i+1:i+3] == "10":
                    i += 3
                else:
                    i += 1
            elif ch == ":":
                parts += ["[ALPHA]", "[∫]"]
                i += 1
            elif ch == ".":
                parts.append("[.]")
                i += 1
            else:
                i += 1
    n = len(sections)
    abc = ""
    if n == 1:
        parts += ["[CALC]", "([=])×2"]
        abc = "[SHIFT] [7] [4] [8] [◀] [9] ([DEL])×11 [◀] [1] [2] [3] [4] [5] [6] [▶] [ALPHA] [∫] [▶] [ALPHA] [CALC] [ALPHA] [(-)] [CALC] ([=])×2 [▲]"
    elif n == 2:
        parts += ["[CALC]", "([=])×3"]
        abc = "[SHIFT] [7] [4] [8] [SHIFT] [7] [4] [9] ([◀] [9] [DEL])×2 ([DEL])×10 [◀] [1] [2] [3] [4] [5] [6] [▶] [ALPHA] [∫] [▶] [ALPHA] [CALC] [ALPHA] [(-)] [ALPHA] [∫] [▶] [ALPHA] [CALC] [ALPHA] [°' \"] [CALC] ([=])×3 ([▲])×2"
    elif n == 3:
        parts += ["[CALC]", "([=])×4"]
        abc = "[SHIFT] [7] [4] [8] [SHIFT] [7] [4] [9] [SHIFT] [7] [1] [4] ([◀] [9] [DEL])×3 ([DEL])×10 [◀] [1] [2] [3] [4] [5] [6] [▶] [ALPHA] [∫] [▶] [ALPHA] [CALC] [ALPHA] [(-)] [ALPHA] [∫] [▶] [ALPHA] [CALC] [ALPHA] [°' \"] [ALPHA] [∫] [▶] [ALPHA] [CALC] [ALPHA] [𝒙⁻¹] [CALC] ([=])×4 ([▲])×3"
    return " ".join(parts), abc
def text_to_key_chars(text_spell, chars_key):
    parts = []
    for c in text_spell:
        if c in chars_key:
            parts.append(chars_key[c])
        else:
            parts.append("[▶]")
    merged = []
    i = 0
    while i < len(parts):
        j = i
        while j < len(parts) and parts[j] == parts[i]:
            j += 1
        n = j - i
        if n == 1:
            merged.append(parts[i])
        else:
            merged.append(f"({parts[i]})×{n}")
        i = j
    return " ".join(merged)
def count_vietnamese_chars(text):
    return len(re.findall(
        r"[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễ"
        r"ìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữ"
        r"ỳýỵỷỹđÀÁẠẢÃÂẦẤẬẬẨẪĂẰẮẶẲẴ"
        r"ÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖ"
        r"ƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]",
        text
    ))
def build_assign_count(count):
    if count == 1:
        return "[SHIFT] [7] [3] [9] ([◀] [9] [DEL])×2 ([DEL])×10"
    if count == 0:
        return "[SHIFT] [7] [3] [9] [◀] [9] ([DEL])×11"
    return f"[SHIFT] [7] [3] [9] ([◀] [9] [DEL])×{count + 1} ([DEL])×10"
def build_zero_key(num):
    if num == 0:
        return ""
    if num == 1:
        return "[0]"
    return f"([0])×{num}"
chars_hex = read_file("chars_hex.txt")
hex_key = read_file("hex_key.txt")
chars_key = read_file("chars_key.txt")
while True:
    text_spell = input("Enter text:")
    if len(text_spell) > 17:
        print("Error")
        continue
    invalid_chars = []
    for c in text_spell:
        if c == " ":
            continue
        if c not in chars_hex and c not in chars_key:
            invalid_chars.append(c)
    if invalid_chars:
        print(f"Error: characters not found in chars_hex/chars_key: {' '.join(sorted(set(invalid_chars)))}")
        print()
        continue
    char_pad = 17 - len(text_spell)
    char_pad_1, char_pad_2 = divmod(char_pad, 2)
    text_spell = (" " * char_pad_1) + text_spell + (" " * char_pad_1) + (" " * char_pad_2)
    print(f"SPELL [{text_spell}] 1 LINE on CASIO fx-580VN X")
    hex_list = []
    for c in text_spell:
        if c in chars_hex:
            hex_list.append(chars_hex[c])
    get_hex = " ".join(hex_list)
    key_list = []
    for byte_hex in hex_list:
        for ch in byte_hex:
            if ch in hex_key:
                key_list.append(hex_key[ch])
    count = len(key_list)
    key_count = build_assign_count(count)
    get_key = " ".join(key_list)
    assign_text, delete_hex = assign_hex(get_hex)
    if assign_text.startswith("Error"):
        print(assign_text)
        assign_text = ""
        delete_hex = ""
    key_assignhex, abc = assign_to_key(assign_text)
    key_chars = text_to_key_chars(text_spell, chars_key)
    spaces = text_spell.count(" ")
    chars_vn = count_vietnamese_chars(text_spell)
    num = (17 - (spaces + chars_vn)) + 14
    key_0 = build_zero_key(num)
    print("- Step 1: Reset")
    print(" [SHIFT] [9] [3] ([=])×2")
    print("- Step 2: Basic overflow")
    print(" [SHIFT] [MENU SETUP] [1] [3] [𝒙] [ALPHA] [CALC] [SHIFT] ([𝒙])×2 [SHIFT] [)] [9] [SHIFT] [)] ([9])×3 [CALC] [=] [AC] [◀] ([DEL])×2 [CALC] [=] [◀] [SHIFT] [.]")
    print("- Step 3: Assign hex")
    parts = []
    if get_key:
        parts.append(get_key)
    if key_count:
        parts.append(key_count)
    if key_assignhex:
        parts.append(f"[ALPHA] [∫] {key_assignhex}")
    print(" " + " ".join(parts))
    print("- Step 4: 124an")
    print(" [𝒙] [ALPHA] [CALC] [SHIFT] ([𝒙])×2 [SHIFT] [)] [9] [SHIFT] [)] [9] [CALC] [=] [◀] ([SHIFT] [.])×2 ([◀])×2 [DEL] [▼] [.] [◀] ([DEL])×8 [▶] [ALPHA] [CALC] [𝒙²] [+] [×10ˣ] [1] [=]")
    print("- Step 5: Export hex")
    print(f" [𝒙] [ALPHA] [CALC] [SHIFT] ([𝒙])×2 [SHIFT] [)] [9] [SHIFT] [)] [9] [CALC] [=] [◀] [SHIFT] [.] {abc} {delete_hex}")
    print("- Step 6: Complete hex")
    print(f" {key_chars} {key_0} [SHIFT] [(] [▶] [2] [𝒙] [CALC] [=]")
    print()
