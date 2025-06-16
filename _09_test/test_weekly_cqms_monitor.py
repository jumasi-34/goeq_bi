"""
주간 CQMS 모니터링 대시보드 테스트 코드
"""

import unittest
import datetime as dt
import pandas as pd
import sys
import os

from _05_commons import config

# 시스템 환경 변수에서 프로젝트 루트 경로를 가져옵니다
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)


from _04_pages._03_MONITORING.ui_weekly_cqms_monitor import (
    get_week_range,
    get_global_data,
    display_metric_section,
    load_metric_data,
)


class TestWeeklyCQMSMonitor(unittest.TestCase):
    """주간 CQMS 모니터링 대시보드 테스트 클래스"""

    def setUp(self):
        """테스트 설정"""
        self.test_date = dt.date(2024, 3, 15)  # 금요일
        self.test_df = pd.DataFrame(
            {
                "PLANT": ["Global", "Plant1", "Plant2"],
                "Open": [10, 5, 3],
                "Close": [8, 4, 2],
                "On-going": [5, 2, 1],
            }
        )

    def test_get_week_range(self):
        """주 범위 계산 테스트"""
        start, end = get_week_range(self.test_date)
        self.assertEqual(start.weekday(), 0)  # 월요일
        self.assertEqual(end.weekday(), 6)  # 일요일
        self.assertEqual(end - start, dt.timedelta(days=6))

    def test_get_global_data(self):
        """Global 데이터 추출 테스트"""
        result = get_global_data(self.test_df)
        self.assertEqual(result["Open"], 10)
        self.assertEqual(result["Close"], 8)
        self.assertEqual(result["On-going"], 5)

    def test_get_global_data_empty(self):
        """Global 데이터가 없는 경우 테스트"""
        df_no_global = pd.DataFrame(
            {
                "PLANT": ["Plant1", "Plant2"],
                "Open": [5, 3],
                "Close": [4, 2],
                "On-going": [2, 1],
            }
        )
        result = get_global_data(df_no_global)
        self.assertEqual(result["Open"], 0)
        self.assertEqual(result["Close"], 0)
        self.assertEqual(result["On-going"], 0)

    def test_load_metric_data(self):
        """지표 데이터 로드 테스트"""
        start = dt.datetime(2024, 3, 11)
        end = dt.datetime(2024, 3, 17)
        df_current, df_before, title, metric_keys = load_metric_data(
            start, end, "quality"
        )
        self.assertIsInstance(df_current, pd.Series)
        self.assertIsInstance(df_before, pd.Series)
        self.assertIsInstance(title, str)
        self.assertIsInstance(metric_keys, list)

    def test_load_metric_data_invalid_type(self):
        """잘못된 지표 타입 테스트"""
        start = dt.datetime(2024, 3, 11)
        end = dt.datetime(2024, 3, 17)
        df_current, df_before, title, metric_keys = load_metric_data(
            start, end, "invalid_type"
        )
        self.assertTrue(df_current.empty)
        self.assertTrue(df_before.empty)
        self.assertEqual(title, "")
        self.assertEqual(metric_keys, [])


if __name__ == "__main__":
    unittest.main()
