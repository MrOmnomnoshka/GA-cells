# DEBUG MODE
DEBUG = True
DETAIL_FN = r"D:\DIPLOMA\app\researcher\models\prisme.igs"
SCHEMA_FN = r"D:\DIPLOMA\app\researcher\load_schemas\load_schema_prisme.txt"
# Model size
X_MIN, X_MAX = 0, 44
Y_MIN, Y_MAX = 0, 40
Z_MIN, Z_MAX = 0, 30

# Experiment parameters
POPULATION_SIZE = 8
MAX_STRESS = 200_000
SAVE_TO_CSV_EVERY_N = 2
TIME_LIMIT = 15
GENERATION_LIMIT = 100
# INACTIVITY LIMIT = 1000  # TODO: MAKE THIS
SAVE_PARENTS = True
SAVE_TEMP_FILES = True
BACKUP_TO_CSV = True
SYMMETRY_OX = True
RESTART_AFTER_ERROR = False

SMART_MESHING = False
MESH_QUALITY = 9  # 1(good) - 10(bad)

# GA - Chromosome
MUT_SIZE = 10
MUT_CHANSE = 20
AN_MIN, AN_MAX = 2, 6  # 3-8
RT_MIN, RT_MAX = 0, 360
SZ_MIN, SZ_MAX = 1, 99
XA_MIN, XA_MAX = 1, 3  # 1-10
YA_MIN, YA_MAX = 1, 3  # 1-10
