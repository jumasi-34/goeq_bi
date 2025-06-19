# OE Quality Evaluation Dashboard

## 1. Global OE Quality Evaluation Objective

### 1.1 목표
- 상품 품질 수준을 종합적으로 평가하고 분석하는 체계를 구축하여 **고객 만족도 및 시장경쟁력 향상**
- 개발과 Field 중간 Bridge로 **단계별 개선 Point 도출 및 개선 요청**
- 개별 제품 단위의 양산 품질 수준을 확인하기 위한 상세 뷰 구축 → **제품별 weak Point 도출**
- 품질 평가 지표를 통해 제품의 주요 품질 요소를 **실시간 모니터링**

## 2. Evaluation Method

### 2.1 평가 대상 및 기간
- **대상**: 24년도 이후 OE 신규 규격
- **평가 기간**: 양산 1년

### 2.2 평가 항목
- **완제품 기준**: 부적합 (Scrap & Rework), G/T 중량 합격률, U/F 초검 합격률, RR, CTL
- **추가 예정**: OE QI(Quality index), Field - Return rate, 4M 변경 이력 (부적합 개선)

### 2.3 평가 지표 상세

| Evaluation Item | Description | Aggregation Method | INDEX Conversion Method | Remarks |
|:---------------:|-------------|-------------------|-------------------------|---------|
| **부적합** | 전체 생산 대비<br>스크랩 발생 비율 | Scrap 발생 수량 ÷ 생산수량 × 1,000,000 ppm | ppm 수준에 따라 0~100 사이로 역비례변환<br>Max: `3,000 ppm` / Min: `20,000 ppm` | |
| **Green Tire Weight** | Green Tire 중량 합격률 | 2.5% 이내 합격 ÷ 총 검사 × 100% | Max: `99.5%` / Min: `97.0%` | |
| **Uniformity** | Uniformity 초검 합격률 | 합격 수량 ÷ 검사 수량 × 100% | Max: `95.0%` / Min: `40.0%` | 공장별 OE합격 등급 기준 |
| **RR** | OE Requirement 대비<br>RR Margin | 상한 마진 & 하한 마진 중 최소값<br>상한 마진: (규격 상한 - 평균) / 표준 편차<br>하한 마진: (평균 - 규격 하한) / 표준 편차 | Max: `3σ` / Min: `0σ` | |
| **CTL** | CTL 합격률 | 전체 합격 항목의 합 ÷ 전체 측정 항목의 합 × 100% | Max: `95.0%` / Min: `30.0%` | 측정 목적<br>측정 항목 |

### 2.4 참고 사항
- **공장별 OE 합격 등급 기준**: `DP`, `KP`, `MP`, `UP`, `TP` → 4등급까지, `JP`, `HP`, `CP` → 3등급까지
- **CTL 측정 목적**: `P_Lot`, `P_Initial Sample`, `P_OE Special Control`, `P_Special Control` (4 항목)
- **CTL 측정 항목**: `BS.12`, `ILG`, `NBD`, `FCD`, `RCG`, `CRCC`, `CRCB`, `UTG.G0`, `UTG.G1`, `UTG.Sho`, `1BHAW`, `2BHAW`, `1TUAH`, `BFH`, `I/P`, `TShG.C+y` (16 항목)

## 3. Operational Strategy

### 3.1 전체 Overview Page 구성
- 규격별 전체 생산비율을 반영하여 worst 규격 도출 → 생산량으로 우선 순위 반영
- 공장별로 OE 품질 관리 비교하여 Worst 공장에 대한 개선 요청
- Worst 규격에 대한 상세 view page를 통해 양산 Trend 및 weak point check

### 3.2 개발 시 양시 Data 비교
- 신규규격에 대한 정보, 양시 일자, RR Data 연계하여 양시 ↔ 양산 Data 비교 (T:DR, ACES 연계 예정)
- 개발과 양산 데이터 비교를 통한 Insight 도출 및 개선
- 25년도 개정된 R-Level (양산성 확보 측면) 비교 및 Index 조정
- **Simulation**: (1032200, 1034087)

### 3.3 Field & OE 품질 이슈 연계
- 제품별 OE 품질 이슈 (OE QI)와 Field 품질이슈 연계를 통해 부적합 개선 Item 도출 및 공장 개선 요청
- **Simulation**: (1030061)

### 3.4 변경 Point에 따른 양산 Trend 및 유효성 검증
- 일자 조정을 통해 4M변경 이후 양산 Trend 확인
- 품질 이슈 발생 이후, 개선 내역에 대한 개선 효과 유효성 검증 Check

## 4. Expected Effects

### 4.1 주요 기대 효과
1. 실시간 모니터링으로 OE 규격별 Weak point를 도출하여 품질 Level up
2. 양시 & 양산 Data 비교 및 개선 Feedback을 통한 양산성이 확보된 개발 Spec 반영
3. Field & OE In-line 주로 발생하는 품질 이슈와 부적합의 연계 분석으로 개선 item 도출
4. Spec에 대한 변곡점 관리 가능
5. OE품질팀의 합의 없이 Spec 변경이 발생될 경우, 역으로 변경점 확인 가능

## 5. Future Plans

### 5.1 데이터 연계 확장
- 현재 공장 양산 Data를 활용하여 BI 구성하였으나, 개발, IQM, Field Data도 연계하여 반영 예정
- 예시: OE QI, Field Return Rate, 4M 변경, 양시 Data

### 5.2 시스템 구현
- 공장별 관리 수준 및 Worst 규격 도출하는 Overview page 구현
- 개발 R-level과 data 비교하여 기준 및 Mass-level index 최적화 진행