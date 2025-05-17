import os


def print_directory_tree(start_path, prefix=""):
    items = os.listdir(start_path)
    items.sort()

    for i, item in enumerate(items):
        if item == "__pycache__" or item == "__init__.py":
            continue  # 제외할 항목

        path = os.path.join(start_path, item)
        is_last = i == len(items) - 1
        branch = "└── " if is_last else "├── "
        print(prefix + branch + item)

        if os.path.isdir(path):
            extension = "    " if is_last else "│   "
            print_directory_tree(path, prefix + extension)


# 사용 예시
print_directory_tree("D:/OneDrive - HKNC/@ Project_CQMS/# Workstation_2")
