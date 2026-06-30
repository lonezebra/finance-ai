# Finance AI

Finance AI is a local-first personal finance desktop application.

It uses:
- LM Studio + Qwen for local AI
- SQLite as the source of truth
- Excel templates for easy data entry and import
- PySide6 for the desktop interface

## Goal

Create a private personal CFO that can help track income, expenses, debt, assets, goals, and financial decisions.

## Core Principle

The AI never directly changes financial data. It proposes actions. Python validates and applies them after user confirmation.