# Illustrative business case — assumptions, not observed savings

Owner hypothesis: an insurer's compliance/product-control team reviewing public
OSAGO offers. No official insurer/regulator partnership or pilot exists.

Illustrative monthly workload: **200 documents**. Assumed manual review: **25
minutes/document**. Assumed analyst-assisted review after screening: **18 minutes**.
Assumed analyst cost: **60,000 UZS/hour**. These are deliberately labelled invented
planning assumptions to be replaced by timed human-workflow measurements.

Potential analyst time difference: `200 × (25 − 18) / 60 = 23.33 hours/month`.
Illustrative labor value: `(200 × 7 / 60) × 60,000 = 1,400,000 UZS/month` before hosting,
support, legal maintenance, training and error-handling costs. This is neither
customer savings nor a claim that automated screening eliminates human review.

Infrastructure assumption: **USD 20/month** fixed hosting cost for capacity
planning, not a current provider quote or purchase authorization. At **200
requests/month**, fixed infrastructure allocation is **USD 0.10/request**; at
**2,000 requests**, **USD 0.01/request**. Variable CPU cost formula:
`allocated_vCPUs × measured_processing_seconds × assumed_USD_per_vCPU_hour / 3600`,
with an assumed allocation of **2 vCPUs** and rate **USD 0.02/vCPU-hour**.
For the measured hybrid median real-document time of 6.164 seconds, this gives
about **USD 0.0000685** of allocated compute per analysis under these assumptions,
excluding initialization, idle capacity and memory/storage charges. The monthly
fixed-hosting allocation is a separate costing scenario; do not add the two as
if they were an actual provider bill. Latency is taken from actual benchmark artifacts; no
exchange rate or provider price is invented as a factual current quote.

External AI API charge per request: **USD 0**, because local inference uses no
external AI API. Electricity, hardware depreciation, operations, idle time,
developer/tool costs and initial model provisioning are not zero and are not
measured by this prototype. See actual RSS/latency before selecting hosting.

First useful validation: timed analyst study against a blind document sample,
expert review of false positives/negatives, willingness to pay and legal rule
maintenance cost. Complaint totals from the Committee are evidence of a problem;
they cannot be converted into addressable-contract counts or a revenue forecast.
