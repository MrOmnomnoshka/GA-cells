import sys

from src.researches.clusterization.clusterization import ResearchesClusterization

if __name__ == "__main__":
    root_folder = sys.argv[1]
    cluster = ResearchesClusterization(researches_folder=root_folder)
    cluster.plot_cluster_data()
