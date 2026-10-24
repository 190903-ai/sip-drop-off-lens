# Golden set: AI vs human agreement

Labelled by the user: **25 of 25** items. Pass bar: 80% agreement.

## Story detection (story_class)

- Agreement: **72%** (18/25) BELOW BAR
- Cohen's kappa: **0.56**

| human \ AI | dropoff_story | stayed_story | not_a_story |
|---|---|---|---|
| dropoff_story | 9 | 3 | 2 |
| stayed_story | 1 | 4 | 0 |
| not_a_story | 1 | 0 | 5 |

## Codebook tags (items both call a story)

| field | agreement | n |
|---|---|---|
| investor_experience | 82% | 17 |
| action | 38% | 16 |
| stop_trigger | 56% | 16 |
| root_cause | 44% | 16 |
| metric_branch | n/a | 0 |

## Disagreements (review these for the Evidence Log)

- #2 `tq_163724`: human **dropoff_story**, AI **not_a_story**
- #3 `bl_jagoinvestor_647700`: human **dropoff_story**, AI **stayed_story**
- #3 `bl_jagoinvestor_647700` action: human **stopped**, AI ['continued']
- #3 `bl_jagoinvestor_647700` root_cause: human **unknown**, AI ['cashflow_rigidity']
- #4 `yt_Ugxz3PJlsZKFHQ0i07l4AaABAg`: human **stayed_story**, AI **dropoff_story**
- #4 `yt_Ugxz3PJlsZKFHQ0i07l4AaABAg` investor_experience: human **experienced**, AI ['unknown']
- #4 `yt_Ugxz3PJlsZKFHQ0i07l4AaABAg` stop_trigger: human **other**, AI ['unknown']
- #5 `yt_UgzJz_b-KmU6dDPvaTF4AaABAg`: human **dropoff_story**, AI **stayed_story**
- #6 `ps_11e5788b-c47f-4cab-83d8-bbea181cadc5` action: human **restructured**, AI ['increased']
- #6 `ps_11e5788b-c47f-4cab-83d8-bbea181cadc5` stop_trigger: human **modify_blocked**, AI ['unknown']
- #6 `ps_11e5788b-c47f-4cab-83d8-bbea181cadc5` root_cause: human **cashflow_rigidity**, AI ['unknown']
- #8 `ps_3a38bfb0-708e-494f-bd1a-97e47d44ccf0` stop_trigger: human **unknown**, AI ['modify_blocked']
- #8 `ps_3a38bfb0-708e-494f-bd1a-97e47d44ccf0` root_cause: human **unknown**, AI ['platform_trust_erosion']
- #9 `rd_m5hmhvi`: human **dropoff_story**, AI **stayed_story**
- #9 `rd_m5hmhvi` investor_experience: human **experienced**, AI ['unknown']
- #9 `rd_m5hmhvi` action: human **considering_stop**, AI ['continued']
- #9 `rd_m5hmhvi` stop_trigger: human **own_returns_negative_flat**, AI ['unknown']
- #9 `rd_m5hmhvi` root_cause: human **volatility_mismatch**, AI ['unknown']
- #10 `ps_aac4a6cd-5b8e-4be2-af22-406466e18014` root_cause: human **other**, AI ['platform_trust_erosion']
- #11 `tq_491514` action: human **continued**, AI ['considering_stop']
- #11 `tq_491514` stop_trigger: human **self_review**, AI ['own_returns_negative_flat']
- #12 `ps_a27b9cbd-920e-4e5e-8919-fd0e5c44ac1a`: human **dropoff_story**, AI **not_a_story**
- #13 `tq_79953`: human **not_a_story**, AI **dropoff_story**
- #14 `bl_jagoinvestor_352991` investor_experience: human **unknown**, AI ['experienced']
- #14 `bl_jagoinvestor_352991` root_cause: human **other**, AI ['unknown']
- #15 `rd_1kr7wvi` action: human **increased**, AI ['considering_stop']
- #15 `rd_1kr7wvi` root_cause: human **borrowed_conviction**, AI ['other']
- #17 `ps_802acc64-50b1-4aff-b57c-cac20737a57a` action: human **considering_stop**, AI ['attempted_blocked']
- #18 `ps_d83e571b-b7d9-4b8a-b085-36f01d2f5233` action: human **paused**, AI ['attempted_blocked']
- #18 `ps_d83e571b-b7d9-4b8a-b085-36f01d2f5233` stop_trigger: human **unknown**, AI ['modify_blocked']
- #18 `ps_d83e571b-b7d9-4b8a-b085-36f01d2f5233` root_cause: human **unknown**, AI ['platform_trust_erosion']
- #20 `ps_abff78d5-0c1f-4136-bb82-6aac081a237b` root_cause: human **unknown**, AI ['platform_trust_erosion']
- #21 `rd_1p69v0f` action: human **continued**, AI ['considering_stop']
- #21 `rd_1p69v0f` stop_trigger: human **own_returns_negative_flat**, AI ['self_review']
- #22 `ps_9f4ecce9-da48-4e2d-8289-d17291082c67` action: human **considering_stop**, AI ['switched_platform']
- #23 `ps_e1e288c5-8727-443b-a752-ff4ca47f2848` action: human **unknown**, AI ['paused']
