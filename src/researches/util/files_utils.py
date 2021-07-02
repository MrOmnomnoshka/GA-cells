import os
import glob

def get_list_of_rst_researches(root_folder: str):
    rst_pattern = root_folder + os.sep + "*" + os.sep + "*.rst"
    return glob.glob(rst_pattern)
