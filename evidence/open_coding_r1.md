# Open coding, round 1: why first-time SIPs lapse

## Method
- **Sample:** 150 items from `data/samples/open_coding_r1.jsonl`, all pre-rated highly relevant. The split is 75 Play Store reviews and 75 YouTube comments. By language: 118 English, 24 Hinglish, 8 Hindi. The AI's `first_time` guess is yes for 24, no for 29 and unknown for 97.
- **Coding:** Every item was read in full. YouTube items were read together with their `video_title`. Hindi and Hinglish items were read in the original, not machine-translated.
- **Clustering:** Codes were written per item without a prior frame. They were then grouped into 25 themes. One item can carry several themes. Counts are the number of items, out of 150, that show a theme in the text. Inferred themes are not counted.
- **Coder:** One coder (an AI) did the whole pass. Inter-coder agreement has not been checked.

**Read every count with this in mind:** source drives theme heavily. Platform and operations themes come only from the Play Store. Returns, conviction and validation-seeking themes come almost only from YouTube. Counts describe *this sample*, not prevalence.

## Theme table

| # | Theme | Definition | Count /150 (PS / YT) | Example quotes |
|---|---|---|---|---|
| H | **Outsourced decision / validation-seeking** | Asks a creator which fund to pick, to "rate my portfolio", or whether to continue | **21** (0/21) | "259G aditya birla sunlife small cap… 3 saal se 1000 ki sip hai continue karna hai ya nahi please tell me" (yt_UgwkdKFQjuAuXf3_93B4AaABAg); "Sir kindly rate my portfolio out of 10" (yt_UgxvGnPbe40IiOdZmqN4AaABAg) |
| I | **Long-horizon conviction / continuing** | Says they are continuing or will hold for years, often citing a horizon | **20** (0/20) | "Me sip kabhi band nhi Karuga jab tak Mera gol 25 years complete nhi hota" (yt_UgzUjeckPy_sGut4mv54AaABAg); "15 sal bad hi check karunga. Aya to aya gaya to gaya." (yt_UgxyTKnHp43jDZiVpnZ4AaABAg) |
| M | **Basic mechanics knowledge gap** | Doesn't know how a SIP works: how to start or add money, where to see amounts, tax on exit, when to withdraw, what happens if the app shuts | **20** (1/19) | "Can you tell me so when do people actually withdraw the money?" (yt_UgwuA-1JGkULOSn6csh4AaABAg.AOYPUd7f3M-ASnW0dM-Xvg); "1 sal bad usko nikal liya to uska jo profit hua woh to sara tax main chala jayege 😭" (yt_UgxQyrIIbbHW-73YDb94AaABAg.AOu5GC-ZonxAOuQReMp1fr) |
| B | **Order, redemption or allotment delays; money not reflected** | Money debited but units not allotted, redemption is slow, an instalment "disappeared" | **16** (16/0) | "worst experience while redeeming… that is the reason I discontinued investing in mutual funds on Groww app" (ps_d93f1aee-3981-4d0b-9ca8-2fcc9e27e769) |
| E | **Support failure / no accountability** | Support doesn't answer, tickets stay open, or the AMC and app each blame the other | **16** (16/0) | "During a financial emergency, Groww asked me to contact Axis, while Axis asked me to go back to Groww" (ps_52e016dd-b91f-43e2-9a0a-9d7ced1046e2) |
| F | **Flat, negative or low returns observed** | Reports their own SIP or fund is negative, flat or "not growing", often with doubt | **15** (2/13) | "pr intrest nhi ban rha h kya karun bhai" (yt_UgwhxZ82Mb_zEmquU0h4AaABAg); "Motilal mid cap os falling like anything should I continue my sip? 😢" (yt_UgzJz_b-KmU6dDPvaTF4AaABAg.AFxsVUFSsu2AS3ry7tyf3a) |
| A | **Autopay / mandate / instalment failure and bounce penalties** | SIP debit fails, mandate can't be approved, no retry, bounce charge. *11 items are SIP-specific; 3 are IPO autopay.* | **14** (14/0) | "auto payment fails in mutual fund sip and there is no retry done by the app" (ps_b94b83bb-16e9-4b69-b9a5-c6ad6b52874b); "472 ka penalty marta hai 100 ki sip miss hua to aur koi reminder… nahi" (ps_4abb04a9-f38e-4c03-a5cf-e0c35b00eb18) |
| C | **Portfolio data wrong, missing or stale** | Values are wrong or not updated, features or ratios were removed, P&L shows late | **14** (14/0) | "it often shows wrong amount invested… i have to double check on kuvera or tickertape" (ps_83ec220f-e7d8-49a0-908e-a37d3aaa802c) |
| D | **Cost / plan-type / platform trust erosion** | Hidden charges, regular rather than direct plans, MF Prime, forced demat opening, "cheating" | **14** (14/0) | "You guys started selling Regular MFs in the name of prime" (ps_ef3e96c3-8b49-4397-a468-e382c935a6ce); "they are forcing me to open their stock account too" (ps_e7f835ec-d787-47ff-b0a2-cef3baab1798) |
| R | **Aggressive allocation by early investors** | Portfolio mostly in small-cap, mid-cap or thematic funds | **10** (0/10) | "I made this aggresive fund portfolio because im under 30… still i see all mf are still underperforming" (yt_UgzXOG1nt9uALQ30UOV4AaABAg) |
| T | **Exit / stop / considering stop** | Stopped, sold, closed the account, uninstalled, or is planning to | **9** (8/1) | "i withdrawal all" (ps_0931366b-c95f-4dc4-a720-17280293f85d); "planning to sell everything and will put in rd instead of sip" (yt_Ugzf-eVVIp7RvIl13DB4AaABAg) |
| Q | **Timing / tinkering mindset** | Buying dips, lumpsum timing, liquid-fund STP tricks, wanting the market to fall | **9** (0/9) | "dabaake DIPs kiye jab jab nifty 1.5 se 2 percent down gaya" (yt_Ugyt-tYfXxv2z-cP_O54AaABAg) |
| V | **Onboarding ease praised** | The app is simple and beginner-friendly, and starting was easy | **9** (9/0) | "As a 22 years old begglinner investor… i started my fast sip last month without any hassle" (ps_0854e615-3dbf-48c7-ab59-60613462fd91) |
| X | **Navigation / UI / KYC friction** | Can't find the cart, funds or SIP amounts; KYC paperwork | **9** (8/1) | "I don't see the cart option under mutual funds" (ps_6d79bce7-2b6d-4aa2-8f04-ba72bb7536c5) |
| L | **Cash-flow / life event** | Emergency, illness, low income, one income spread over many goals, need to withdraw | **8** (4/4) | "I recently got operated on my knee… just need one month to get back on track… tried to skip one installment but the useless feature doesn't work" (ps_e10390c4-9c4e-4406-a83d-bda8dc96ce29) |
| K | **Increase / top-up / step-up** | Raised the amount, doubled it, or is unsure about topping up | **8** (1/7) | "Negative returns since started recently but have doubled the SIP" (yt_Ugxa_BzfgBSU4YWA4-94AaABAg) |
| G | **Expectation vs benchmark gap** | Measures the SIP against FD/RD, lumpsum, NAV point-to-point, or a specific return they expected | **6** (1/5) | "I thought in 3-5 yrs i will definitely get minimum 10-12 percent" (yt_Ugzf-eVVIp7RvIl13DB4AaABAg); "10 months ho gye… only 250 rupees hi increase hue h.. isse jyada to bank ki FD se mil jata h" (yt_UgxWZ-X7571BoJ4GEvt4AaABAg) |
| O | **Daily P&L tracking / external trackers** | Checks daily gain or loss, or keeps another app for tracking | **6** (5/1) | "I have to keep another App just to track my Daily Gains/Losses of MFs" (ps_4a16d02f-f219-4e8d-866b-762eed990af4) |
| J | **SIP as discipline / goal savings** | Values the SIP as forced saving or tied to a named goal, not to returns | **6** (0/6) | "What I've actually benefited more from is the discipline of saving" (yt_Ugze0Ut90XUyW7SFjwh4AaABAg); "returns is not that high… But atleast I'm saving something instead of spending" (yt_UgyiNeg9qYj6GR6IV2B4AaABAg.ASLuJPtbFgqASN0eX5x9fz) |
| N | **Started because someone pushed** | A creator's video or a family member triggered the start | **6** (1/5) | "Tum logon k chaker main meri ek aur SIP start ho gai" (yt_UgwHJAISbGdyhsGxNEN4AaABAg); "I installed the app only because I was told by my son" (ps_2f0011cd-3d92-4a92-ae41-33667c4edecb) |
| S | **Can't modify the SIP (skip, edit, increase, manual pay)** | The app blocks skipping, editing the amount, increasing, or paying manually | **5** (4/1) | "I can't increase Sip money instantly. It has to be wait for 6 months to 1 year" (ps_f1ca2f35-cdbb-4955-9bd8-8ca9f0241def) |
| Y | **Continues after creator reassurance** | Says outright that a creator's advice kept them going | **4** (0/4) | "I am keeping my SIP continue. Thanks for your valuable advice" (yt_UgyoYPPdmz0feRxRH254AaABAg) |
| U | **Distrust of MFs or the market itself** | "Scam", "controlled by big players", doubts that the numbers shown are honest | **4** (2/2) | "MF is completely scams all controlled by big players" (yt_Ugzf-eVVIp7RvIl13DB4AaABAg) |
| W | **Creator skepticism / contradiction** | Notices creators contradicting themselves | **3** (0/3) | "pehle ap ne 5sal tk negative bola ab ap 2mahine badh 10 sal tk negative bolrhe ho… mene apke bolne pr 2lamsum or sip kiya" (yt_UgytMrD7ZlC_X2kmn9F4AaABAg) |
| P | **Deliberately not looking** | Copes by not checking | **2** (0/2) | "keep sips ongoing and app delete kar do. Dekho hi mat" (yt_UgwGG8OGzvf85yAfw5x4AaABAg) |

**Segment signals (thin):**

| Segment | Count | Items |
|---|---|---|
| Student / teen | 3 | ps_a88c81e5…, yt_UgyR48XKrnO… (age 15), yt_UgwmPTg5Rp6… |
| Explicitly young | 2 | ps_0854e615… (22), yt_UgzXOG1nt9u… (under 30) |
| Older | 2 | yt_Ugzku64BZS6… (starting at 65), yt_Ugze0Ut90XU… (38, started at 32) |
| Low or single income | 2 | yt_UgyRiNullV5… (earns ₹10k/month, 4 SIPs), yt_UgypwnFTeqM… |
| Rural | 1 | yt_UgzvY8Zhxl6….AREa |
| Family-influenced elder | 1 | ps_2f0011cd… |
| Salaried | 1 | ps_4b9a15df… (salary, EMI, SIP) |
| Self-employed or homemaker | 0 | none |

## Surprises and contradictions to the "markets fell" story

1. **Most actual exits in the sample are caused by the platform, not the market.** Of the 9 exit or stop items, 7 are triggered by operations or trust events. These include a slow redemption, a ₹350 NACH bounce charge ("so i immediately closed my demat account"), MF Prime auto-switching ("i withdrawal all"), hidden charges (an account closed after 2 days), and autopay failures. Only 1 exit (yt_Ugzf-eVVIp7…) is clearly returns-driven, and even that one is framed against a *specific expectation* (10-12% in 3-5 years) plus FD/RD and tax distrust.
2. **Flat or negative returns often produce *more* investing, not less.** Several writers double or top up (yt_Ugxa_BzfgBS…), or say they *want* the market to stay down to collect cheap NAV (yt_UgyW-7tnuAz…, yt_UgwUf_z8edn…). The same observation, "returns are negative", leads to opposite actions. So the difference lies in how returns are *interpreted*, not in returns themselves.
3. **Returns are misread in specific, repeatable ways:**
   - Point-to-point NAV ("start NAV 540, now 715, lumpsum would have been better", yt_UgwgP-XyuJO…).
   - Absolute rupees against an FD ("only ₹250 in 10 months", yt_UgxWZ-X7571…).
   - The fund's headline return against the investor's own SIP ("SIP 2 years minus but you show 30% return", ps_399bdfbe…).
   - Doubting whether daily gain or loss is even honest (yt_Ugynn2kcaCW…).
4. **The plumbing makes pausing harder than stopping.** In the clearest life-event case (knee surgery), the user *wanted* a one-month skip, the skip feature failed, and the user turned on the app. Elsewhere, a ₹472 penalty followed a missed ₹100 SIP (ps_4abb04a9…).
5. **Conviction is borrowed.** The most common YouTube behaviour (21 of 75 YouTube comments) is handing the hold/switch/stop decision to a creator in a comment box. When the creator's message shifts, the investor's anger is aimed at the creator (yt_UgytMrD7ZlC…).
6. **Continuers rarely talk about returns.** They talk about *discipline* ("atleast I'm saving something"), a goal (a house down payment, "goal of 25 years"), or *not looking*.

## Gaps: what this sample can't tell us
- **Source bias:** Play Store reviews skew to bugs, operations failures and anger (most are 1★). YouTube comments skew to people already looking for reassurance or advice. Neither shows the *silent* drop-off: people who stop without ever complaining or commenting.
- **No Reddit yet.** Reddit is likely richer on reasoning: XIRR literacy, FD comparisons, self-employed income, and "I stopped because…" narratives. **The codebook must be re-checked against Reddit before scaling.**
- **First-time status is mostly unknown** (97 of 150). The target population (first SIP, 0-12 months) is directly visible in perhaps 10-15 items.
- **Segments are almost absent.** There is nothing on self-employed, gig or irregular income, homemakers, or the source of money beyond a teen and a ₹10k earner.
- **Stage is rarely stated,** so we can't yet tell what changes in months 1-12.
- **Checking frequency** is stated only for "daily" (complaints about a daily P&L lag) or "never" (coping). The middle is unobserved.
- **Several Play Store items are about stocks, IPO or F&O.** They were included only for their MF or autopay angle, and they inflate the operations themes.
- **One item (ps_083e2485…) is truncated in the source data.**

## Candidate root-cause hypotheses

### H1. Return-interpretation gap
First-timers have no frame for reading their *own* SIP's performance. They compare point-to-point NAV, absolute rupees against an FD, or the fund's headline return against their own result. Normal flat periods then read as "SIP isn't working".

- **Support: 17 items** in the union of F (15) and G (6). The clearest are yt_UgwgP-XyuJO…, ps_399bdfbe…, yt_UgxWZ-X7571…, yt_Ugzf-eVVIp7…, yt_UgwkEo36-8E… and yt_UgwqAEDY2du….
- **Disproved if:** stoppers in Reddit or a larger sample read XIRR or rupee returns correctly and stop anyway, or if doubt about returns doesn't co-occur with stop or considering-stop more than with continue.

### H2. Borrowed conviction
The SIP (and the fund) was chosen on someone else's say-so: a creator, a son, or "tum logon k chakkar". The investor owns no reasoning, so every wobble needs outside validation. When the source is silent or contradicts itself, the commitment has nothing to rest on.

- **Support: 32 items** in the union of H (21), N (6), Y (4) and W (3).
- **Disproved if:** self-directed starters lapse at the same rate as influenced ones, or validation-seekers continue at higher rates than others.

### H3. Payment plumbing breaks the habit
Mandate or autopay failures, missing retries, bounce or penalty charges, and skips that don't work turn a one-month hiccup into a stopped SIP. The lapse can happen with no decision to quit.

- **Support: 14 items** in the union of SIP-specific A (11) and S (5). The clearest are ps_e10390c4… and ps_f5bff1c5….
- **Disproved if:** internal data shows few lapsed first SIPs whose last event is a failed debit or an unresolved mandate. This is cheap to test with Groww data.

### H4. Cash-flow rigidity
The fixed monthly amount doesn't adapt to emergencies or irregular income. Because the available option is binary (continue or cancel), the investor cancels.

- **Support: 8 items (L). This is thin.** The sample lacks irregular earners.
- **Disproved if:** Reddit and segment data show self-employed or irregular-income first-timers persist like salaried ones, or that cash-need stops resume quickly on their own.

### H5. Trust erosion in the platform, spilling onto the product
Hidden or unclear charges, regular plans sold as "Prime", forced demat, wrong portfolio values and slow redemptions make the user feel cheated. They then leave Groww, and sometimes MFs altogether.

- **Support: 7 of the 9 exits.** Underlying themes are D (14), C (14) and B (16).
- **Disproved if:** these users continue SIPs at other platforms or AMCs. In that case this is platform churn rather than SIP abandonment, though it still hurts the Groww metric. Also disproved if trust complaints come mostly from long-tenure users rather than first-timers.

### H6. Volatility mismatch (exploratory)
Early investors pile into small-cap, mid-cap or thematic funds (R: 10) and meet larger drawdowns than they were mentally prepared for.

- **Constraint:** we can't recommend funds. The lever would only be helping investors understand the range of outcomes for whatever they chose.
- **Disproved if:** stopping is unrelated to how aggressive the portfolio is.
