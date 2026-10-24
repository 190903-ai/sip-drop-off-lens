# Golden set: review of disagreements (adjudicated)

The user labelled 25 posts blind (no AI answers visible), then reviewed every disagreement with both answers shown and chose the final answer. Blind labels are unchanged in golden_set.xlsx; final answers are in data/golden_review.json.

| Field | n | Blind agreement (AI vs human) | AI vs final answer | Human blind vs final answer |
| --- | --- | --- | --- | --- |
| Story or not | 25 | 18/25 (72%) | 20/25 (80%) | 23/25 (92%) |
| New vs experienced | 17 | 14/17 (82%) | 16/17 (94%) | 15/17 (88%) |
| What they did | 16 | 6/16 (38%) | 11/16 (69%) | 11/16 (69%) |
| Event (trigger) | 16 | 9/16 (56%) | 14/16 (88%) | 11/16 (69%) |
| Real reason | 16 | 7/16 (44%) | 11/16 (69%) | 12/16 (75%) |
| All four tag fields | 65 | 36/65 (55%) | 52/65 (80%) | 49/65 (75%) |

Pass bar: 80%.

## Every disagreement and how it was resolved

| Post | Field | Human (blind) | AI | Final | Outcome | Human reason |
| --- | --- | --- | --- | --- | --- | --- |
| #2 | story_class | dropoff_story | not_a_story | dropoff_story | AI wrong |  |
| #3 | story_class | dropoff_story | stayed_story | dropoff_story | AI wrong | This is related to earlier SIP which can help find the reason behind cancellation of SIPs |
| #3 | action | stopped | continued | stopped | AI wrong |  |
| #3 | root_cause | unknown | cashflow_rigidity | unknown | AI wrong |  |
| #4 | story_class | stayed_story | dropoff_story | stayed_story | AI wrong | because no matter the amount, the same SIP was still active i believe. Though, I am not clear on it |
| #4 | investor_experience | experienced | unknown | unknown | blind label revised |  |
| #4 | stop_trigger | other | unknown | unknown | blind label revised |  |
| #5 | story_class | dropoff_story | stayed_story | stayed_story | blind label revised |  |
| #6 | action | restructured | increased | increased | blind label revised | new SIP was raised for the same fund with increased amount but previous one was deleted. |
| #6 | stop_trigger | modify_blocked | unknown | modify_blocked | AI wrong | he clearly mentioned he was not able to raise the amount of SIP so he had to create new one every year and delete the previous one |
| #6 | root_cause | cashflow_rigidity | unknown | unknown | blind label revised |  |
| #8 | stop_trigger | unknown | modify_blocked | modify_blocked | blind label revised |  |
| #8 | root_cause | unknown | platform_trust_erosion | unknown | AI wrong | The malfunction happened after the user cancelled the SIP so we cannot really tell the real reason behind the cancellation of the sip |
| #9 | story_class | dropoff_story | stayed_story | stayed_story | blind label revised |  |
| #9 | investor_experience | experienced | unknown | experienced | AI wrong |  |
| #9 | action | considering_stop | continued | considering_stop | AI wrong |  |
| #9 | stop_trigger | own_returns_negative_flat | unknown | own_returns_negative_flat | AI wrong |  |
| #9 | root_cause | volatility_mismatch | unknown | volatility_mismatch | AI wrong |  |
| #10 | root_cause | other | platform_trust_erosion | platform_trust_erosion | blind label revised |  |
| #11 | action | continued | considering_stop | continued | AI wrong | talks nothing about cancelling the older SIPs |
| #11 | stop_trigger | self_review | own_returns_negative_flat | own_returns_negative_flat | blind label revised |  |
| #12 | story_class | dropoff_story | not_a_story | dropoff_story | AI wrong |  |
| #13 | story_class | not_a_story | dropoff_story | not_a_story | AI wrong |  |
| #14 | investor_experience | unknown | experienced | experienced | blind label revised |  |
| #14 | root_cause | other | unknown | other | AI wrong | It was mainly due to his change of place |
| #15 | action | increased | considering_stop | increased | AI wrong | because he already has so many funds and asking advice for investing in more funds |
| #15 | root_cause | borrowed_conviction | other | borrowed_conviction | AI wrong | The post shows that he will invest surely based in the people's advices on his post. He will not take the decision himself, he will get influenced by others |
| #17 | action | considering_stop | attempted_blocked | attempted_blocked | blind label revised |  |
| #18 | action | paused | attempted_blocked | attempted_blocked | blind label revised |  |
| #18 | stop_trigger | unknown | modify_blocked | modify_blocked | blind label revised |  |
| #18 | root_cause | unknown | platform_trust_erosion | platform_trust_erosion | blind label revised |  |
| #20 | root_cause | unknown | platform_trust_erosion | platform_trust_erosion | blind label revised |  |
| #21 | action | continued | considering_stop | continued | AI wrong |  |
| #21 | stop_trigger | own_returns_negative_flat | self_review | self_review | blind label revised |  |
| #22 | action | considering_stop | switched_platform | switched_platform | blind label revised |  |
| #23 | action | unknown | paused | paused | blind label revised |  |
