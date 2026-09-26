#!/usr/bin/env python3
"""Interactive CLI Consultation: Chat with Kent-AI (Phase 6).

Run a friendly, live homeopathic clinical intake consultation right in your terminal.
Upon completion, automatically displays the full repertorization report with remedy rankings.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.chatbot.dialogue_manager import DialogueManager
from src.chatbot.state_machine import ConversationStateMachine, IntakeState
from src.pipeline.orchestrator import PipelineOrchestrator


def main():
    parser = argparse.ArgumentParser(description="Interactive Kent-AI Clinical Intake Chatbot.")
    parser.add_argument("--mock", action="store_true", help="Use deterministic mock templates instead of live LLM")
    parser.add_argument("--model", type=str, default="llama3:8b", help="Ollama model name (default: llama3:8b)")
    args = parser.parse_args()

    print("=" * 70)
    print(" 🌿 Kent-AI — Conversational Homeopathic Intake Assistant")
    print("=" * 70)
    print(f"Backend: {'Mock Mode' if args.mock else f'Live Ollama ({args.model})'}")
    print("Type your responses naturally. Type 'quit' or 'exit' at any time to stop.\n")

    # Initialize full pipeline orchestrator
    orchestrator = PipelineOrchestrator(mock_mode=args.mock)
    dm = DialogueManager(
        orchestrator=orchestrator,
        model_name=args.model,
        mock_mode=args.mock,
    )

    # Initial greeting
    greeting = dm.get_greeting()
    print(f"Kent-AI > {greeting}\n")

    while not dm.state_machine.can_terminate():
        state = dm.state_machine.current_state.value
        filled_count = len(dm.state_machine.filled_slots)
        
        try:
            prompt_indicator = f"[{state} | Slots: {filled_count}/7] Patient > "
            user_input = input(prompt_indicator).strip()
        except (KeyboardInterrupt, EOFError):
            print("\nConsultation paused.")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "q"):
            print("\nEnding consultation early.")
            break

        bot_reply = dm.process_turn(user_input)
        print(f"\nKent-AI > {bot_reply}\n")

    # If completed, display the final report
    report = dm.get_patient_report()
    if report:
        print("\n" + "=" * 70)
        print(" 📋 FINAL CLINICAL REPERTORIZATION REPORT")
        print("=" * 70)
        print(report.to_markdown())
    else:
        # Generate report from partial transcript if ended early
        transcript = dm.get_full_transcript()
        if transcript.strip():
            print("\nGenerating report from recorded symptoms...")
            report = orchestrator.process_transcript(transcript)
            print("\n" + "=" * 70)
            print(" 📋 CLINICAL REPERTORIZATION REPORT")
            print("=" * 70)
            print(report.to_markdown())


if __name__ == "__main__":
    main()
