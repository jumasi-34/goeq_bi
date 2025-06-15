"""
프로젝트의 모든 Python 파일에서 하드코딩된 경로를 config.PROJECT_ROOT로 변경하는 스크립트
"""

import os
import re
from pathlib import Path


def update_file(file_path):
    """파일의 경로 설정을 업데이트합니다."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 이미 config.PROJECT_ROOT를 사용하는 경우 건너뛰기
    if "config.PROJECT_ROOT" in content:
        return False

    # 하드코딩된 경로 패턴
    old_path_pattern = (
        r'sys\.path\.append\(r"D:\\OneDrive - HKNC\\@ Project_CQMS\\# Workstation_2"\)'
    )

    # 새로운 경로 설정
    new_path = "from _05_commons import config\nsys.path.append(config.PROJECT_ROOT)"

    # 변경이 필요한지 확인
    if re.search(old_path_pattern, content):
        # 하드코딩된 경로를 새로운 경로로 교체
        new_content = re.sub(old_path_pattern, new_path, content)

        # 파일에 변경사항 저장
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True

    return False


def main():
    # 프로젝트 루트 디렉토리
    project_root = Path(__file__).parent

    # 수정된 파일 수 카운터
    modified_files = 0

    # 모든 Python 파일 검색
    for root, _, files in os.walk(project_root):
        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                if update_file(file_path):
                    print(f"Updated: {file_path}")
                    modified_files += 1

    print(f"\n총 {modified_files}개의 파일이 수정되었습니다.")


if __name__ == "__main__":
    main()
