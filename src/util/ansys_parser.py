import re


def get_dimensions(ansys_manager):
    command = ansys_manager.run("KLIST")
    all_lines = re.findall(r'\d.+', command)[2:]
    str_numbers = [re.findall(r'[\w\d\.\-+E]+', s[:-24]) for s in all_lines]
    numbers = [list(map(float, num)) for num in str_numbers]

    dimensions = []
    for i in range(3):
        dimension = [xyz[1 + i] for xyz in numbers]
        mx, mn = round(max(dimension), 8), round(min(dimension), 8)
        dimensions.append(mx - mn)
    return dimensions


def get_model_mass(ansys_manager):
    command = ansys_manager.run("IRLIST")
    phrase = "TOTAL MASS = "
    start = command.index(phrase) + len(phrase)
    mass = re.findall(r'[\d.\-+E]+', command[start:])[0]
    return float(mass)


def get_pressed_areas(ansys_manager):
    command = ansys_manager.run("SFALI")
    all_lines = re.findall(r'\d.+', command)[2:]
    a = [re.findall(r'[\w\d\.\-+E]+', s) for s in all_lines]
    press_amount = len(a)
    return press_amount


def get_supported_areas(ansys_manager):
    command = ansys_manager.run("DALIS")
    all_lines = re.findall(r'\d.+', command)[2:]
    a = [re.findall(r'[\w\d\.\-+E]+', s) for s in all_lines]
    support_amount = len(a) // 3  # support on all (x,y,z) axes
    return support_amount


def get_element_id(text):
    val_and_id = re.findall(r"NO\.=\s*\d*|NUMBER =\s*\d*|VALUE=\s*\d*|OUTPUT AREA =\s*\d*", text)  # for some reason '()' didn't work here
    id = re.findall(r"\d+", val_and_id[0])
    return int(id[0])


def get_max_element_id_from_command(ansys_manager, element):
    res = ansys_manager.run("*GET, KMax, " + element + ",, NUM, MAX")
    return get_element_id(res)


def analyze_load_schema(load_schema):
    """Displacement: DL - lines DA - areas  DK - keypoints  D - nodes
       Pressure: SFL - lines    SFA - areas SF - nodes"""
    all_selected = re.findall(r"FLST.*\w|^D[^DENSITY]\w*|SF\w*", load_schema, re.M)  # re.M - multi-line flag
    analyzed = {"DL": 0, "DA": 0, "DK": 0, "D": 0, "SFL": 0, "SFA": 0, "SF": 0}
    for i in range(1, len(all_selected), 2):
        key = all_selected[i]
        if key in analyzed.keys():  # adding value if this key exists
            analyzed.update({key: analyzed.get(key) + int(all_selected[i - 1][-1:])})
    return analyzed


def get_max_press(ansys_manager):
    ansys_manager.run("/ POST1")
    ansys_manager.run("SET, FIRST")
    ansys_manager.run("NSORT, S, EQV")
    ansys_manager.run("*GET, STRESS_MAX, SORT,, MAX")
    command = ansys_manager.run("*STATUS, STRESS_MAX")
    start = command.index("\n STRESS_MAX")
    max_stress = re.findall('\d+\\.\d+', command[start:])[0]
    return float(max_stress)
