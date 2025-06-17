"""
OE Assessment 결과 집계 스크립트

이 스크립트는 OE Assessment 결과를 집계하고 SQLite 데이터베이스에 저장합니다.
데이터는 SQLite 데이터베이스에서 로드되며, 결과는 mass_assess_result 테이블에 저장됩니다.
"""

# 표준 라이브러리
import os
import sys
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass

# 데이터 처리 및 분석 라이브러리
import numpy as np
import pandas as pd
from scipy.stats import norm

# 프로젝트 루트 경로 설정
project_root = os.getenv("PROJECT_ROOT", os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# 데이터베이스 및 쿼리 관련 모듈
from _00_database.db_client import get_client
from _01_query.GMES.q_production import curing_prdt_daily
from _01_query.GMES.q_ncf import ncf_daily
from _01_query.GMES.q_weight import gt_wt_assess
from _01_query.GMES.q_ctl import get_ctl_raw_query
from _01_query.helper_sql import format_date_to_yyyymmdd

# 전처리 모듈
from _02_preprocessing.GMES.df_rr import get_rr_df, get_rr_oe_list_df
from _02_preprocessing.GMES.df_uf import calculate_uf_pass_rate

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)), "product_assessment.log"
            )
        ),
        logging.StreamHandler(),
    ],
)

# 테이블 스키마 정의
MASS_ASSESS_RESULT_SCHEMA = [
    ("m_code", "TEXT"),
    ("min_date", "TEXT"),
    ("max_date", "TEXT"),
    ("total_qty", "INTEGER"),
    ("ncf_qty", "INTEGER"),
    ("uf_pass_rate", "REAL"),
    ("gt_wt_pass_rate", "REAL"),
    ("rr_pass_rate_pdf", "REAL"),
    ("ctl_pass_rate", "REAL"),
    ("created_at", "TEXT"),
]


@dataclass
class DateRange:
    start_date: str
    end_date: str
    formatted_start: str
    formatted_end: str


def calculate_pass_rate_with_pdf(df: pd.DataFrame) -> pd.DataFrame:
    """확률밀도함수를 사용하여 합격률을 계산합니다.

    Args:
        df: RR 데이터프레임

    Returns:
        pd.DataFrame: 합격률이 추가된 데이터프레임
    """

    def get_pass_rate(row: pd.Series) -> float:
        if pd.isna(row["SPEC_MAX"]) or pd.isna(row["SPEC_MIN"]):
            return np.nan

        mean, std = row["avg"], row["std"]
        if std == 0 or pd.isna(std):
            return np.nan

        upper_prob = norm.cdf(row["SPEC_MAX"], loc=mean, scale=std)
        lower_prob = norm.cdf(row["SPEC_MIN"], loc=mean, scale=std)
        return upper_prob - lower_prob

    return df.assign(rr_pass_rate_pdf=df.apply(get_pass_rate, axis=1))


def get_date_range(start_date: datetime) -> DateRange:
    """날짜 범위를 계산합니다."""
    end_date = start_date + timedelta(days=180)
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")

    return DateRange(
        start_date=start_date_str,
        end_date=end_date_str,
        formatted_start=format_date_to_yyyymmdd(start_date_str),
        formatted_end=format_date_to_yyyymmdd(end_date_str),
    )


def collect_production_data(mcode: str, date_range: DateRange) -> pd.DataFrame:
    """생산 데이터를 수집하고 집계합니다."""
    prdt_df = get_client("snowflake").execute(
        curing_prdt_daily(
            mcode_list=[mcode],
            start_date=date_range.formatted_start,
            end_date=date_range.formatted_end,
        )
    )
    return (
        prdt_df.groupby(["m_code"])
        .agg(
            min_date=("wrk_date", "min"),
            max_date=("wrk_date", "max"),
            total_qty=("prdt_qty", "sum"),
        )
        .reset_index()
    )


def collect_ncf_data(mcode: str, date_range: DateRange) -> pd.DataFrame:
    """NCF 데이터를 수집하고 집계합니다."""
    ncf_df = get_client("snowflake").execute(
        ncf_daily(
            mcode_list=[mcode],
            start_date=date_range.formatted_start,
            end_date=date_range.formatted_end,
        )
    )
    return ncf_df.groupby(["m_code"]).agg(ncf_qty=("dft_qty", "sum")).reset_index()


def process_ctl_data(ctl_df: pd.DataFrame) -> pd.DataFrame:
    """CTL 데이터를 처리합니다."""
    ctl_df = ctl_df.groupby(["m_code", "jdg"]).size().reset_index(name="count")
    ctl_pivot = ctl_df.pivot(index="m_code", columns="jdg", values="count").fillna(0)

    if "OK" in ctl_pivot.columns and "NI" in ctl_pivot.columns:
        ctl_pivot["ctl_pass_rate"] = ctl_pivot["OK"] / (
            ctl_pivot["NI"] + ctl_pivot["OK"]
        )
    else:
        ctl_pivot["ctl_pass_rate"] = 0

    return ctl_pivot.reset_index()


def merge_all_data(
    prdt_df: pd.DataFrame,
    ncf_df: pd.DataFrame,
    uf_df: pd.DataFrame,
    gt_wt_df: pd.DataFrame,
    rr_df: pd.DataFrame,
    ctl_df: pd.DataFrame,
) -> pd.DataFrame:
    """모든 데이터를 병합합니다."""
    # 컬럼명 통일 (소문자로)
    rr_df = rr_df.rename(columns={"M_CODE": "m_code"})
    gt_wt_df = gt_wt_df.rename(columns={"M_CODE": "m_code"})
    uf_df = uf_df.rename(columns={"M_CODE": "m_code"})

    # 데이터프레임 컬럼 확인 및 로깅
    logging.info(f"Production data columns: {prdt_df.columns.tolist()}")
    logging.info(f"NCF data columns: {ncf_df.columns.tolist()}")
    logging.info(f"UF data columns: {uf_df.columns.tolist()}")
    logging.info(f"GT weight data columns: {gt_wt_df.columns.tolist()}")
    logging.info(f"RR data columns: {rr_df.columns.tolist()}")
    logging.info(f"CTL data columns: {ctl_df.columns.tolist()}")

    # 데이터 병합
    result_df = prdt_df.copy()

    # NCF 데이터 병합
    if not ncf_df.empty:
        result_df = result_df.merge(ncf_df, on=["m_code"], how="left")

    # UF 데이터 병합
    if not uf_df.empty:
        result_df = result_df.merge(uf_df, on=["m_code"], how="left")

    # GT weight 데이터 병합
    if not gt_wt_df.empty:
        result_df = result_df.merge(gt_wt_df, on=["m_code"], how="left")

    # RR 데이터 병합
    if not rr_df.empty:
        rr_cols = ["m_code", "count", "rr_pass_rate_pdf"]
        available_cols = [col for col in rr_cols if col in rr_df.columns]
        result_df = result_df.merge(rr_df[available_cols], on=["m_code"], how="left")

    # CTL 데이터 병합
    if not ctl_df.empty:
        result_df = result_df.merge(
            ctl_df[["m_code", "ctl_pass_rate"]], on=["m_code"], how="left"
        )

    # 결측값 처리
    result_df = result_df.fillna(0)

    return result_df


def process_single_mcode(row: pd.Series) -> pd.DataFrame:
    """단일 M-code에 대한 데이터를 처리합니다."""
    mcode = row["M_CODE"]
    mcode_rr = row["M_CODE_RR"]
    date_range = get_date_range(pd.to_datetime(row["START_MASS_PRODUCTION"]))

    try:
        logging.info(f"Processing M-code: {mcode}, RR M-code: {mcode_rr}")
        logging.info(f"Date range: {date_range.start_date} to {date_range.end_date}")

        # 데이터 수집
        logging.info("Collecting production data...")
        prdt_df = collect_production_data(mcode, date_range)
        logging.info(f"Production data shape: {prdt_df.shape}")
        if prdt_df.empty:
            logging.warning(f"No production data found for M-code: {mcode}")
            return pd.DataFrame()

        logging.info("Collecting NCF data...")
        ncf_df = collect_ncf_data(mcode, date_range)
        logging.info(f"NCF data shape: {ncf_df.shape}")

        logging.info("Calculating UF pass rate...")
        uf_df = calculate_uf_pass_rate(
            mcode, date_range.formatted_start, date_range.formatted_end
        )
        logging.info(f"UF data shape: {uf_df.shape}")

        logging.info("Collecting GT weight data...")
        gt_wt_df = get_client("snowflake").execute(
            gt_wt_assess(
                mcode_list=mcode,
                start_date=date_range.formatted_start,
                end_date=date_range.formatted_end,
            )
        )
        logging.info(f"GT weight data shape: {gt_wt_df.shape}")

        # RR 데이터 처리
        logging.info("Processing RR data...")
        _, rr_df, _ = get_rr_df(
            mcode_list=mcode_rr,
            start_date=date_range.start_date,
            end_date=date_range.end_date,
        )
        rr_list = get_rr_oe_list_df()
        rr_list = rr_list[rr_list["M_CODE"] == mcode_rr][
            ["M_CODE", "PLANT", "SPEC_MAX", "SPEC_MIN"]
        ]
        # 컬럼명 통일 (소문자로)
        rr_list = rr_list.rename(columns={"M_CODE": "m_code"})
        rr_df = pd.merge(rr_df, rr_list, on=["m_code", "PLANT"], how="left")
        rr_df = calculate_pass_rate_with_pdf(rr_df)
        logging.info(f"RR data shape: {rr_df.shape}")

        # CTL 데이터 처리
        logging.info("Processing CTL data...")
        ctl_df = get_client("snowflake").execute(
            get_ctl_raw_query(
                start_date=date_range.formatted_start,
                end_date=date_range.formatted_end,
                mcode=mcode,
            )
        )
        ctl_df = process_ctl_data(ctl_df)
        logging.info(f"CTL data shape: {ctl_df.shape}")

        # 데이터 병합
        logging.info("Merging all data...")
        result_df = merge_all_data(prdt_df, ncf_df, uf_df, gt_wt_df, rr_df, ctl_df)
        logging.info(f"Final merged data shape: {result_df.shape}")
        logging.info(f"Final merged data columns: {result_df.columns.tolist()}")

        return result_df

    except Exception as e:
        logging.error(f"Error processing M-code {mcode}: {str(e)}")
        return pd.DataFrame()


def main():
    try:
        # 타겟 데이터 로드
        logging.info("SQLite 데이터베이스 연결 시도...")
        sqlite_client = get_client("sqlite")
        logging.info(f"데이터베이스 경로: {sqlite_client.db_path}")

        # 테이블 존재 여부 확인 및 생성
        tables = sqlite_client.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        )
        if "mass_assess_result" not in tables["name"].values:
            logging.info(
                "mass_assess_result 테이블이 존재하지 않습니다. 테이블을 생성합니다."
            )
            create_table_query = f"""
            CREATE TABLE mass_assess_result (
                {', '.join([f'{col} {dtype}' for col, dtype in MASS_ASSESS_RESULT_SCHEMA])}
            )
            """
            sqlite_client.execute(create_table_query)
            logging.info("mass_assess_result 테이블이 생성되었습니다.")

        logging.info("mass_assess_target 테이블에서 데이터 로드 시도...")
        target_df = sqlite_client.execute("SELECT * FROM mass_assess_target")
        logging.info(f"Loaded {len(target_df)} target records")

        if target_df.empty:
            logging.error("mass_assess_target 테이블이 비어있습니다.")
            return

        # 각 M-code 처리
        all_results = []
        for idx, row in target_df.iterrows():
            try:
                logging.info(
                    f"Processing M-code {row['M_CODE']} ({idx + 1}/{len(target_df)})"
                )
                result_df = process_single_mcode(row)
                if not result_df.empty:
                    # 생성 시간 추가
                    result_df["created_at"] = datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                    all_results.append(result_df)
                    logging.info(f"Successfully processed M-code: {row['M_CODE']}")
                else:
                    logging.warning(f"No data returned for M-code: {row['M_CODE']}")
            except Exception as e:
                logging.error(f"Error processing M-code {row['M_CODE']}: {str(e)}")

        if all_results:
            # 결과 저장
            logging.info(f"Total {len(all_results)} results to save")
            final_df = pd.concat(all_results, ignore_index=True)
            logging.info(f"Final DataFrame shape: {final_df.shape}")
            logging.info(f"Final DataFrame columns: {final_df.columns.tolist()}")
            logging.info(f"Final DataFrame head:\n{final_df.head()}")

            logging.info("Saving results to mass_assess_result table...")
            try:
                # 기존 데이터 삭제
                sqlite_client.execute("DELETE FROM mass_assess_result")

                # 새로운 데이터 저장
                sqlite_client.insert_dataframe(final_df, "mass_assess_result")

                # 저장 후 테이블 확인
                saved_data = sqlite_client.execute(
                    "SELECT COUNT(*) as count FROM mass_assess_result"
                )
                logging.info(f"Saved data count: {saved_data['count'].iloc[0]}")
                logging.info("Results successfully saved to mass_assess_result table")
            except Exception as e:
                logging.error(f"Error saving to database: {str(e)}")
                raise
        else:
            logging.warning("No data was processed - all_results is empty")

    except Exception as e:
        logging.error(f"An error occurred in main(): {str(e)}")
        raise


if __name__ == "__main__":
    main()
