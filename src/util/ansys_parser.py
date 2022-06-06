import re


def get_dimensions(ansys_manager):
    # TODO: это не всегда верно, в крайних точках модели могут быть кривые без кейпоинтов, и размеры выводяться меньше
    command = ansys_manager.run("KLIST")
    all_lines = re.findall(r'\d.+', command)[2:]  # Skip two first lines with ANSYS info
    str_numbers = [re.findall(r'[\w\d\.\-+E]+', s) for s in all_lines]
    numbers = [list(map(float, num)) for num in str_numbers]
    numbers2 = [map(float, num) for num in str_numbers]

    dimensions = []
    for i in range(3):
        dimension = [xyz[1 + i] for xyz in numbers]
        mx, mn = round(max(dimension), 8), round(min(dimension), 8)
        dimensions.append((mn, mx))
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


def get_element_ids(text):
    # can't redo with lookbehind :(          (?<=OUTPUT.*)\d+
    val_and_id = re.findall(r"NO\.=\s*\d*|NUMBER =\s*\d*|VALUE=\s*\d*|OUTPUT AREA =\s*\d*|OUTPUT VOLUME =\s*\d*|"
                            r"(?<=OUTPUT VOLUMES =).+", text)  # for some reason '()' didn't work here
    r_id = re.findall(r"\d+", val_and_id[0])
    return r_id


def get_max_element_id_from_command(ansys_manager, element):
    res = ansys_manager.run("*GET, KMax, " + element + ",, NUM, MAX")
    return int(get_element_ids(res)[0])


def analyze_load_schema_on_actions(load_schema):
    """Displacement: DL - lines DA - areas  DK - keypoints  D - nodes
       Pressure: SFL - lines    SFA - areas SF - nodes"""
    all_selected = re.findall(r"FLST.*\w|^D[^DENSITY]\w*|SF\w*", load_schema, re.M)  # re.M - multi-line flag
    analyzed = {"DL": 0, "DA": 0, "DK": 0, "D": 0, "SFL": 0, "SFA": 0, "SF": 0}
    for i in range(1, len(all_selected), 2):
        key = all_selected[i]
        if key in analyzed.keys():  # adding value if this key exists
            analyzed.update({key: analyzed.get(key) + int(all_selected[i - 1][-1:])})
    return analyzed


def analyze_load_schema_on_items(load_schema):
    all_selected = re.findall(r"(?<=FITEM,2,)-?\d+", load_schema)  # re.M - multi-line flag
    return [abs(int(num)) for num in all_selected]


def get_all_areas(ansys_manager):
    res = ansys_manager.run("ALIST")
    all_areas_info = re.findall(r"^\s+\d+(?=.*N)", res, re.M)
    all_num = [int(num) for num in all_areas_info]
    return all_num


def get_max_press(ansys_manager):
    ansys_manager.run("/ POST1")
    ansys_manager.run("SET, FIRST")
    ansys_manager.run("NSORT, S, EQV")
    ansys_manager.run("*GET, STRESS_MAX, SORT,, MAX")
    command = ansys_manager.run("*STATUS, STRESS_MAX")
    start = command.index("\n STRESS_MAX")
    max_stress = re.findall('\d+\\.\d+', command[start:])[0]
    return float(max_stress)
