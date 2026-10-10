# Known limitations and remaining work

1. Public deployment is deferred by the user. No hosted URL or independent public
   browser test exists. This project is **not hackathon submission-ready**.
2. All interpretations are `PENDING_LEGAL_REVIEW`. No legal professional has
   approved applicability, date transitions or disclosure/incorporation assumptions.
3. Three provisions only; no whole-document compliance determination. The product
   selection is user-confirmed OSAGO, not a trained product classifier.
4. Text-based PDFs only. OCR binary/resources were absent; OCR quality is unmeasured.
   The GROSS Latin sample's damaged text and INSON's letter-O numeric strings
   cause abstention. The engine never silently replaces letter O with zero.
5. Language/script labels use passage vocabulary and Unicode cues. Undetermined
   and mixed labels can include company names, addresses or OCR artifacts. No
   human-labelled language classifier accuracy is claimed.
6. Section detection is a rules-heading/attribution heuristic. Verified INSON
   boundary is page 9, but unseen appendix layouts can be missed. Preview/review
   is necessary; appendix text never proves the author's contractual terms match.
7. Deterministic wording extraction remains limited. The historical failure on
   `перечисляется` is preserved in the original measurements and fixed by narrow
   finite-verb recognition with wrong-event, negation and conditional regression
   cases. Those formerly fresh fixtures are now exposed regression data; they
   cannot support an independent generalization claim. Strict trigger parsing may
   abstain on legitimate but unrecognized paraphrases.
8. Historical semantic-only retrieval underperformed lexical/hybrid status
   accuracy. A conservative offer-topic scan now protects all modes against top-K
   omissions, including competing values. It only covers recognized topics, not
   every possible paraphrase. The evaluation does not establish an AI advantage.
   Real samples still show extensive abstention (8 of 9 rule results in this audit).
9. Synthetic labels are original AI-assisted engineering annotations, not legal
   expert ground truth. Three fresh documents are too few for generalization.
   Real samples have page labels, no complete transcription/legal-status labels.
10. Applicable dates outside 05.08.2024–10.10.2026 abstain. A 2024 historical LexUZ
    snapshot was unreachable; accessible 2019/current texts and current amendment
    annotations support the limited catalogue. Existing-contract transition
    interpretation remains for a legal reviewer.
11. Table reading order and multiple deadlines/amounts can prevent comparison.
    Exact quote/page integrity does not prove logical relevance or legal correctness.
12. One active analysis per process; model memory is substantial. Benchmark peak
    exceeded 1.3 GiB. Do not infer suitability for constrained hosting without
    actual resource/cold-start testing. No automatic downgrade of the AI component
    is presented as successful full-function deployment.
13. Review identity is a local demo label. Review records have no authentication,
    durable store, organization identity, tamper-evident signatures or legal approval.
14. Runtime has an offline inference path, but initial dependencies/model downloads
    need provisioning. Linux/container cold-start and offline-analysis measurements
    are recorded separately in `evaluation/container_results.json`; these do not
    establish performance on any future public host.
15. Application distribution-license decision and PyMuPDF AGPL/commercial obligations
    must be resolved before public release. No insurer PDF redistribution rights.
16. AI embeddings are limited to 512 tokens per passage. Long passages can be
    truncated for ranking; original evidence text is retained, and the scope
    guard examines the complete extracted passage. Windows extraction has a wall
    timeout but no verified hard process memory cap. Decompression/native-parser
    failures remain a reason to use an isolated approved environment.
17. This audit verifies the updated native localhost application. Previously
    recorded Docker/image verification applies to the older source checkpoint;
    the image must be rebuilt and retested before use with the redesign.
