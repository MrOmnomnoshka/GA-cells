# DEBUG MODE
DEBUG = False
DETAIL_NAME = "prisme"  # "uho"
DETAIL_FN = rf"D:/DIPLOMA/app/researcher/models/{DETAIL_NAME}.igs"
SCHEMA_FN = rf"D:/DIPLOMA/app/researcher/load_schemas/{DETAIL_NAME}.txt"

# Model size
if DETAIL_NAME == "uho":
    X_MIN, X_MAX = -21.0, 21.0  # -22, 22
    Y_MIN, Y_MAX = -16.0, 63.0  # -17, 64
    Z_MIN, Z_MAX = 0.0, 6.0
    OFFSET = 1.0
elif DETAIL_NAME == "prisme":
    X_MIN, X_MAX = -19.0, 19.0  # -20, 20
    Y_MIN, Y_MAX = -21.0, 21.0  # -22, 22
    Z_MIN, Z_MAX = -15.0, 15.0
    OFFSET = 1.0
elif DETAIL_NAME == "block_200_300_20":
    X_MIN, X_MAX = -100.0, 100.0
    Y_MIN, Y_MAX = -150.0, 150.0  # -150, 150
    Z_MIN, Z_MAX = -10.0, 10.0
    OFFSET = 0.0
else:
    X_MIN, X_MAX = Y_MIN, Y_MAX = Z_MIN, Z_MAX = 0.0, 0.0
    OFFSET = 0.0

# Experiment parameters
POPULATION_SIZE = 10  # *==IN UI==*
MAX_STRESS = 200_000  # *==IN UI==*
SAVE_TO_CSV_EVERY_N = 2  # *==IN UI==*
TIME_LIMIT = 15  # *==IN UI==*    # TODO: make this
GENERATION_LIMIT = 75  # *==IN UI==*
# INACTIVITY LIMIT = 1000  # TODO: MAKE THIS
SAVE_PARENTS = False  # *==IN UI==*  # TODO: пересмотреть (сохраянть при селекции 2 предков по лучшему фтнесу)
SAVE_ELITE = True  # *==IN UI==*
SAVE_TEMP_FILES = True  # *==IN UI==*
BACKUP_TO_CSV = True  # *==IN UI==*
RESTART_AFTER_ERROR = False  # *==IN UI==*  # TODO: dosen't work
SYMMETRY_OY = True  # *==IN UI==*  # TODO: add syym Ox
ELITE_STRATEGY = True  # *==IN UI==*
ELITE_AMOUNT = 4  # *==IN UI==*

SMART_SIZING = False
MESH_QUALITY = 2  # 1(good) - 10(bad)

MAX_TIME_ON_ONE_RESEARCH = 120  # in seconds (=2min)  # TODO: add this

# GA - Agent
MUT_CHANSE = 80  # 70           # *==IN UI==*
MUT_SIZE = 4  # 7               # *==IN UI==*
AN_MIN, AN_MAX = 3, 9  # 3-9    # *==IN UI==*
RT_MIN, RT_MAX = 0, 360         # *==IN UI==*
SZ_MIN, SZ_MAX = 30, 99         # *==IN UI==*
XA_MIN, XA_MAX = 1, 9           # 1-10 # *==IN UI==*
YA_MIN, YA_MAX = 1, 9           # 1-10 # *==IN UI==*
CELLS_DEPTH = False             # *==IN UI==*
CELLS_INTERSECT = False  # TODO:? make them be in one another

# FITNESS FUNCTION ('-1'->min, '0'->off, '1'->max)
FIT_VOLUME = 1      # *==IN UI==*
FIT_SIZE = 1        # *==IN UI==*
FIT_AMOUNT = 0      # *==IN UI==*
FIT_MASS = -1       # *==IN UI==*
FIT_STRESS = -1     # *==IN UI==*
