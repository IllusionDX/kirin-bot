import os

PREFIX = ";"
TOKEN = str(os.getenv("TOKEN"))

ext_path = "./extensions"
ext_lst = []

for file in os.listdir(ext_path):
    if file.endswith(".py"):
        ext_lst.append(f"{ext_path[2:]}.{file[:-3]}")

filters = {
    "safe" : "100073",
    "explicit" : "37432",
    "all" : "56027"
}