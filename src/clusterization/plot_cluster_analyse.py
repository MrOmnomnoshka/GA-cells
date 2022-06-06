import sys

from src.clusterization.clusterization import ResearchesClusterization

if __name__ == "__main__":
    # root_folder = sys.argv[1]
    root_folder = r"D:\DIPLOMA\app\researcher\temp_files"
    cluster = ResearchesClusterization(researches_folder=root_folder)
    cluster.plot_cluster_data()
