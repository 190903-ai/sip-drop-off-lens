# Metric decomposition v1 (structural, before evidence)

**North-star:** % of first-time MF investors (cohort by first-SIP month) with an **active SIP at month 12**
(active = ≥1 successful instalment in the last 30 days).

This version is built from how SIPs work, not from any assumed user problem. v2 will attach
discovery-engine evidence (frequency, severity, addressability) to each branch.

## 1. The identity

```
Active@M12 = P(first instalment succeeds)                       [A. Activation]
           × P(no voluntary stop/pause through M12)             [C. Intent to continue]
           × P(no involuntary lapse in the M12 window)          [B. Instalment reliability]
           + P(lapsed users re-activated by M12)                [D. Recovery]
```

Note on the definition: "≥1 successful instalment in the last 30 days" means **a single skipped or
bounced monthly instalment around month 12 makes a user inactive** even if they never meant to quit.
That makes involuntary failures (B) and recovery (D) more important than they first look.
(Also check edge cases: quarterly SIPs would read as inactive by definition; weekly/daily SIPs are
more robust.)

## 2. Tree

```
Active SIP at M12 (first-time investors)
│
├── A. Activation: does the SIP actually start? (M0–M1)
│   ├── A1 Mandate / autopay registration completed
│   ├── A2 First instalment debited successfully
│   └── A3 SIP date aligned with when money is in the account (e.g. salary date)
│
├── B. Instalment reliability: involuntary drop-off (every month)
│   ├── B1 Debit success rate per instalment
│   │   ├── insufficient balance on debit date
│   │   ├── mandate expired / bank changed / mandate limit too low
│   │   └── platform / bank technical failure
│   ├── B2 User awareness of a failed instalment (do they even notice?)
│   └── B3 Recovery after a failure (retry, pay manually, or silently lapse)
│
├── C. Intent to continue: voluntary drop-off
│   ├── C1 Actions: skip → pause → reduce amount → cancel  (and the opposite: step-up)
│   └── C2 Drivers of the action (the "why" the discovery engine must quantify)
│       ├── Perceived progress: expectation vs what they see (returns comprehension,
│       │   time horizon, what number they look at, comparison with FD / others)
│       ├── Affordability: cash-flow shocks, income stability, competing goals
│       ├── Trust: in the platform, in mutual funds, in the advice that started them
│       ├── Salience: forgetting why they started, no goal attached, "out of sight"
│       └── Social influence: friends, family, creators changing their mind
│
└── D. Recovery: getting lapsed users back before M12
    ├── D1 Lapsed users who restart within 30/60/90 days
    └── D2 Barriers to restarting (friction, guilt, "I'll restart later")
```

## 3. Candidate product metrics per branch (to finalise in Part 7)

| Branch | Leading indicator (observable in product) |
|---|---|
| A | Mandate registration success %, first-instalment success %, SIP-date-vs-salary-date alignment |
| B | Instalment success %, bounce rate by reason, % failures followed by manual payment within 7 days |
| C | Skip / pause / reduce / cancel rate by month since start; step-up rate; returns-screen visits before cancel |
| D | Restart rate within 30/60/90 days of lapse |

## 3b. Evidence note: "stopping a SIP" ≠ churn (Reddit check, 2026-10-21)
In a 60-post r/mutualfunds sample, 16 of 20 "stop" posts were **restructuring**: cancelling one fund's
SIP while continuing to invest (consolidating overlap, regular→direct, replacing hasty first picks).
The metric counts a user as active if they have *any* active SIP, so restructuring is not drop-off
unless the replacement SIP lapses or the gap exceeds 30 days. Product implication: SIP cancellations
are a noisy proxy for churn; measure at the user level, not the SIP level.

## 4. Open questions for the discovery engine
- Which branch shows up most in what people say (B vs C vs D)?
- Within C, which driver comes **before** the action, and in which month?
- Which branches are controllable inside Groww without recommending funds or using fear/FOMO?
