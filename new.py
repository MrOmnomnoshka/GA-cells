import os

saveFrom = "D:\\master_degree\\nodes.txt"
saveTo = "D:\\master_degree\\nodes.csv"

code = os.system("java -jar %s %s %s" % ('D:\\master_degree\\pyansys-test3\\nodes_parser.jar', saveFrom, saveTo))
print(code)