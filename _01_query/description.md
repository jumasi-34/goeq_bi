## test_query 주피터 노트북

쿼리문을 test 하기 위해서 주피터 노트북을 활용한다.

## query 폴더 관리
- 쿼리문을 관리하기 위한 폴더임
- db별로, 주제별로 폴더를 생성하여 쿼리문을 관리
  - 주제내에서 필요한 CTE문은 동일 폴더 내에서 작성한다.
  - 
- common CTE 파일
  - 마스터 코드관리나 직원 정보와 같은 공통으로 사용해야하는 쿼리의 경우 COMMON_CTE에서 관리한다.
- helper 파일
  - 자주 사용하는 decode문을 처리하기 위해서 사용하는 폴더
- config 파일
  - config, const를 관리한다.
