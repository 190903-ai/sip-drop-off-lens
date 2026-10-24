// Plain-English names for codebook v1.10 codes (data/freeze_2026-10-24/codebook.json)
export const LABELS: Record<string, string> = {
  // outcome groups (analyze.py OUTCOME)
  stayed: "Stayed", left: "Left", wobbling: "Wobbling", restructured: "Restructured",
  changed_app: "Changed app", unknown: "Not stated",
  dropoff: "Stopped or wavering", item: "Other relevant post",
  // groups
  first_time: "First-time", experienced: "Experienced",
  // sources
  reddit: "Reddit", playstore: "Play Store", appstore: "App Store", youtube: "YouTube",
  tradingqna: "TradingQ&A", blog: "Blog", app_review: "App reviews", community: "Community",
  groww: "Groww", etmoney: "ET Money", paytmmoney: "Paytm Money", indmoney: "INDmoney", coin: "Coin (Zerodha)",
  kuvera: "Kuvera",
  // action
  continued: "Continued", increased: "Increased", reduced: "Reduced", paused: "Paused", stopped: "Stopped",
  switched_platform: "Switched app", attempted_blocked: "Tried but blocked",
  nearly_stopped: "Nearly stopped", considering_stop: "Thinking of stopping",
  considering_switch_platform: "Thinking of switching app", considering_start: "Thinking of starting",
  redeemed: "Redeemed",
  // stage
  pre_start: "Before starting", early_0_3m: "First 3 months", "3_12m": "3–12 months", "12m_plus": "12+ months",
  // root cause
  return_misreading: "Misread returns", expectation_violation: "Expectation not met",
  safe_asset_benchmark: "Compared with FD / safe asset", borrowed_conviction: "Someone else's conviction",
  cashflow_rigidity: "Cash-flow rigidity", payment_plumbing: "Payment / mandate plumbing",
  platform_trust_erosion: "Platform trust erosion", product_distrust: "Product distrust",
  volatility_mismatch: "Volatility mismatch", timing_mindset: "Timing the market",
  portfolio_rationalisation: "Portfolio clean-up", other: "Other",
  // stop trigger
  own_returns_negative_flat: "Returns flat / negative", market_news: "Market news", payment_failure: "Payment failure",
  charge_penalty: "Charge or penalty", platform_change: "Platform change", order_redemption_delay: "Order / redemption delay",
  data_discrepancy: "Data mismatch", cash_need_life_event: "Cash need / life event", advice_received: "Advice received",
  modify_blocked: "Modify blocked", self_review: "Own portfolio review", missing_notification: "Missing notification",
  tax_rule_change: "Tax rule change", app_malfunction: "App malfunction", debit_after_cancel: "Debited after cancel",
  support_failure: "Support failure",
  // stay reason
  long_horizon_belief: "Long-horizon belief", averaging_understanding: "Understands averaging",
  past_recovery_seen: "Has seen a recovery", advice_reassurance: "Reassured by advice", goal_linked: "Linked to a goal",
  automation_inertia: "Autopilot", affordable_amount: "Affordable amount",
  // metric branch
  activation: "Activation", reliability: "Reliability", intent: "Intent", recovery: "Recovery", none: "None",
  // checking
  daily_pnl: "Daily P&L", current_value_amount: "Current value (₹)", returns_pct: "Returns %", xirr: "XIRR",
  nav: "NAV", fund_level_returns: "Fund-level returns", transaction_status: "Transaction status",
  avoids_checking: "Avoids checking",
  daily_or_more: "Daily or more", weekly_monthly: "Weekly / monthly", rarely_by_choice: "Rarely, by choice",
  event_driven: "When something happens",
  // behaviour change
  checking_faded: "Checks less", checking_rose: "Checks more", autopilot_forgot: "On autopilot",
  amount_increased: "Amount increased", amount_reduced: "Amount reduced", paused_resumed: "Paused, then resumed",
  funds_added: "Added funds", funds_consolidated: "Consolidated funds", mode_switched: "Switched plan / mode",
  learned_more: "Learned more", confidence_fell: "Confidence fell", confidence_rose: "Confidence rose",
  // in-app confusion
  value_mismatch: "Value mismatch", return_figure_meaning: "What a return figure means",
  payment_mandate_status: "Payment / mandate status", modify_sip: "Changing a SIP", charges_plan_type: "Charges / plan type",
  navigation_ui: "Navigation / UI", order_timeline: "Order timeline", account_kyc_demat: "Account / KYC / demat",
  tax_withdrawal: "Tax on withdrawal",
  // outside the app
  creator_comment: "Asked a creator", family_friend: "Asked family / friends", reddit_forum: "Asked a forum",
  advisor_ca: "Asked an adviser / CA", other_tracker: "Used another tracker", other_platform: "Used another platform",
  complaint_escalation: "Escalated a complaint", manual_payment: "Paid manually", self_research: "Researched alone",
  // segments
  salaried: "Salaried", self_employed_business: "Self-employed / business", irregular_gig: "Irregular / gig income",
  student_no_income: "Student / no income", homemaker: "Homemaker", retired: "Retired",
  own_earnings: "Own earnings", family_money: "Family money", savings_lumpsum: "Savings / lump sum",
  minor_under_18: "Under 18", student_18_plus: "Student (18+)", early_career_20s: "Early career (20s)",
  mid_career_30s_40s: "Mid career (30s–40s)", pre_retirement_50s: "Pre-retirement (50s)", senior_60_plus: "60+",
  youtube_creator: "YouTube creator", family: "Family", friend_colleague: "Friend / colleague", app_platform: "The app",
  advisor_distributor: "Adviser / distributor", self_directed: "Self-directed", online_community: "Online community",
  // unmet need
  understand_my_returns: "Understand my returns", reliable_payment_recovery: "Reliable payment recovery",
  flexible_pause_modify: "Flexible pause / modify", independent_reassurance: "Independent reassurance",
  transparent_costs: "Transparent costs", accurate_timely_portfolio: "Accurate, timely portfolio",
  responsive_support: "Responsive support", basics_education: "Basics explained", consent_control: "Consent and control",
  goal_linkage: "Link to a goal", portfolio_construction_help: "Portfolio construction help",
  // emotion
  anxious: "Anxious", angry_frustrated: "Angry or frustrated", disappointed_regret: "Disappointed / regret",
  confused: "Confused", calm_confident: "Calm and confident", hopeful_excited: "Hopeful", neutral: "Neutral",
  // motivation / expectation
  creator_push: "A creator's push", family_friend_push: "Family / friend push", saving_discipline: "Saving discipline",
  specific_goal: "A specific goal", wealth_returns: "Wealth / returns", learning_experiment: "Learning / trying it",
  app_ease: "The app made it easy", tax_saving: "Tax saving",
  specific_return_target: "A specific return target", beat_safe_asset: "Beat FD / safe assets",
  steady_growth: "Steady growth", long_term_volatility_accepted: "Accepts volatility long term",
  savings_not_returns: "Saving, not returns",
};

export const label = (c: string | null | undefined) => (c ? LABELS[c] ?? c.replace(/_/g, " ") : "");

export const FIELD_LABELS: Record<string, string> = {
  action: "Action", stage: "Stage", root_cause: "Root cause", stop_trigger: "Trigger", unmet_need: "Unmet need",
  emotion: "Emotion", metric_branch: "Metric branch", in_app_confusion: "In-app confusion",
  outside_app_workaround: "Outside the app", influencer_source: "Influenced by", stay_reason: "Stay reason",
  start_motivation: "Why they started", expectation: "Expectation", behaviour_change: "Behaviour change",
  checking_behaviour: "What they check", check_frequency: "How often", life_stage: "Life stage",
  income_type: "Income", source_of_money: "Money from", investor_experience: "Experience", platform: "Platform",
};

export const SOURCE_NAME = (s: { src: string; app?: string | null; sub?: string | null }) =>
  s.src === "reddit" && s.sub ? `r/${s.sub}` :
  (s.src === "playstore" || s.src === "appstore") && s.app ? `${label(s.src)} · ${label(s.app)}` : label(s.src);

export const pct = (x: number | undefined | null) => (x == null ? "–" : `${Math.round(x * 100)}%`);
