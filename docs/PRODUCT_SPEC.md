# Finance AI Product Spec

## Mission

Finance AI is a local-first personal financial operating system that helps users understand their financial position, maintain clean financial records, and make better decisions using deterministic calculations plus private AI reasoning.

## Core Principle

The app should answer three questions:

1. What changed?
2. What is risky?
3. What should I do next?

## Version 1 Scope

Version 1 will focus on practical household finance management.

### Primary Navigation

- Dashboard
- Transactions
- Budget
- Debt
- Assets
- Goals
- Reports
- AI Chat
- Settings

## Dashboard

The dashboard is the command center.

### Required Metrics

- Net Worth
- Monthly Cash Flow
- Cash Balance
- Total Debt
- Emergency Fund Months
- Debt-to-Income Ratio
- Savings Rate
- Open Action Items

### Dashboard Sections

#### Financial Snapshot

At-a-glance numbers showing current financial posture.

#### What Changed

Highlights changes since the previous month.

Examples:
- Net worth increased/decreased
- Debt changed
- Cash flow changed
- Spending category increased

#### What Needs Attention

Risk or warning flags.

Examples:
- Emergency fund below target
- Credit card interest rate is high
- Budget category exceeded
- Debt-to-income ratio is elevated

#### Recommended Next Actions

Actionable suggestions generated from deterministic calculations and AI interpretation.

Examples:
- Increase debt payment by a specific amount
- Review dining spending
- Build emergency fund before investing more
- Update missing account balances

## Data Entry Philosophy

Users should not be forced to enter everything manually in the app.

The app will support structured Excel templates for easy bulk entry and maintenance.

Excel templates feed into SQLite.

SQLite is the source of truth.

## Data Flow

Excel templates / CSV imports / manual entries  
→ Import validation  
→ SQLite database  
→ Finance engine calculations  
→ Dashboard and reports  
→ AI interpretation and recommendations

## Core Modules

### Money Flow

Tracks income, expenses, cash flow, budgets, recurring transactions, and spending trends.

### Balance Sheet

Tracks accounts, assets, debts, liquidity, and net worth.

### Plan & Scenarios

Tracks goals, debt payoff plans, emergency fund targets, and future what-if scenarios.

### Protection & Execution

Tracks action items, financial review tasks, insurance, tax reminders, and decision logs.

## AI Design

The AI never directly modifies financial data.

The AI may:
- Explain financial summaries
- Recommend actions
- Identify missing data
- Propose structured tool actions
- Generate reports

The AI may not:
- Directly write to the database
- Directly edit Excel files
- Invent missing numbers
- Execute destructive actions without confirmation

## Calculation Philosophy

Python performs calculations.

AI explains calculations.

Calculations that belong in Python:
- Net worth
- Cash flow
- Savings rate
- Debt-to-income ratio
- Emergency fund months
- Budget variance
- Debt payoff projections
- Goal funding requirements

## Future Expansion

Possible future modules:

- Investments
- Retirement readiness
- Tax planning
- Insurance coverage
- Estate planning checklist
- Scenario engine
- Bank CSV import rules
- AI-generated monthly financial review

## Product North Star

Open CFO helps the user identify the highest-impact next financial action, then stress-test that action through transparent scenario planning.

The app should be exceptional at two things:

1. Next Best Action
2. Scenario Planning

### Next Best Action

The app should consistently answer:

- What should I do next?
- Why does it matter?
- What data supports it?
- What tradeoff am I making?
- How confident is this recommendation?

### Scenario Planning

The app should allow users to model what-if questions such as:

- What if I pay extra toward debt?
- What if income changes?
- What if expenses increase or decrease?
- What if I make a major purchase?
- What if I receive a windfall?
- What if investment returns differ from assumptions?

Python performs the scenario calculations.

The AI explains the results, assumptions, and tradeoffs.

## AI Runtime

Open CFO's AI layer is model-agnostic.

Responsibilities:

- Prompt management
- Context assembly
- Thinking state
- Strategic reasoning
- Model abstraction

The runtime should support multiple local models through LM Studio.

The user may choose different models for different workloads.