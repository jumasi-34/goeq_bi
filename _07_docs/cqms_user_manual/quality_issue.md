# 품질이슈 PF
```
---
config:
  layout: dagre
---
flowchart LR
    A["Define<br>The Problem"] ==> B["Save"]
    B ==> C["Root Cause &amp; <br> Countermeasure"]
    C ==> D{"Approval"}
    D == Approved ==> E["Conclusion"]
    D -. Rejected .-> C
    E ==> F{"Approval"}
    F == Approved ==> G["End"]
    F -. Rejected to 8D Report .-> E
    F -. Rejected to Root Cause Analysis .-> C
     A:::highlight
     C:::highlight
     E:::highlight
    classDef highlight fill:#ffe599,stroke:#b8860b,stroke-width:2px
```
1. 등록하기
![Quality Issue Process Flow](../../_06_assets/cqms/qi_01_registration.gif)

2. M-Code 등록 > 발생일 등록 > Stage 선택
![Quality Issue Process Flow](../../_06_assets/cqms/qi_02_mcode.gif.gif)


![Quality Issue Process Flow](../../_06_assets/cqms/qi_03_return.gif.gif.gif)
