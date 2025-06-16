import snowflake.connector

try:
    conn = snowflake.connector.connect(
        user="21300584",
        password="Jumasi21300584",
        account="ls58031.ap-northeast-2.privatelink",
        warehouse="SMALL_WH",
        database="HKT_DW",
        schema="KPPMES",
        ocsp_fail_open=False,  # 중요
    )
    print("✅ 연결 성공")
except Exception as e:
    print("❌ 연결 실패:", e)
