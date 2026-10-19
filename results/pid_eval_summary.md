# P&ID branch evaluation (step 24)

Vision model qwen2.5vl:3b on CPU; seconds per drawing: [110.0, 88.7, 83.8].

| Drawing | Tags expected | Correct | Invented | Missed |
|---|---|---|---|---|
| P&ID-001 | 13 | 11 | - | T-101, T-102 |
| P&ID-002 | 13 | 12 | - | FCV-201 |
| P&ID-003 | 13 | 13 | - | - |

| QA metric (12 frozen questions, full graph) | Result |
|---|---|
| Routed to documents | 100% |
| Right drawing retrieved | 100% |
| Answer correct | 42% (5/12) |
| valve isolating a pump | 1/3 |
| controller + control valve | 1/3 |
| what an instrument measures, on what | 3/3 |
| which drawing / unit | 0/3 |
| Mean latency | 33.2 s |
