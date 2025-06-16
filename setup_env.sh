#!/bin/bash

# conda 환경 활성화
source ~/miniconda3/etc/profile.d/conda.sh
conda activate goeq

# 프로젝트 루트 설정
export PROJECT_ROOT=/home/jumasi/workstation
export CQMS_ENV=development

# 세션 설정
export SESSION_TIMEOUT_MINUTES=30
export MAX_LOGIN_ATTEMPTS=3

# Snowflake 설정
export SNOWFLAKE_ACCOUNT=your_account
export SNOWFLAKE_USER=your_username
export SNOWFLAKE_PASSWORD=your_password
export SNOWFLAKE_WAREHOUSE=your_warehouse
export SNOWFLAKE_DATABASE=your_database
export SNOWFLAKE_SCHEMA=your_schema

# SQLite 설정
export SQLITE_DB_PATH=data/cqms.db

# 환경 변수 확인
echo "환경 변수 설정 완료:"
env | grep -E "PROJECT_ROOT|CQMS_ENV|SNOWFLAKE|SESSION_TIMEOUT|SQLITE" 