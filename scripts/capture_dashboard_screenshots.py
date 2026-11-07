"""End-to-end script to capture comprehensive high-resolution screenshots of Kent-AI Dashboard."""

import os
import sys
import time
import subprocess
import urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO_ROOT = Path(__file__).resolve().parent.parent
SCREENSHOTS_DIR = REPO_ROOT / "docs" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

PORT = 8550
URL = f"http://localhost:{PORT}"


def wait_for_server(url: str, timeout: float = 35.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.5)
    return False


def wait_streamlit_idle(page, timeout_ms: int = 15000):
    """Wait until Streamlit finishes running script and DOM is stable."""
    try:
        page.wait_for_selector('[data-test-script-state="idle"]', timeout=timeout_ms)
    except Exception:
        pass
    time.sleep(1.5)


def click_tab(page, tab_name: str):
    """Click a top-level tab by text."""
    tab = page.locator(f"[role='tab']:has-text('{tab_name}')")
    if tab.count() > 0:
        tab.first.click()
        wait_streamlit_idle(page)


def main():
    print(f"Target screenshots directory: {SCREENSHOTS_DIR}", flush=True)

    # Ensure disclaimer is marked acknowledged in db
    try:
        from src.data.case_store import set_app_setting, save_case
        from src.dashboard.components.demo_case import create_demo_case

        set_app_setting("has_acknowledged_disclaimer", True)
        demo_case = create_demo_case()
        save_case(demo_case)
        print("Demo case pre-saved to case_store.", flush=True)
    except Exception as e:
        print("Note on database setup:", e, flush=True)

    # Launch Streamlit server with DEVNULL to avoid Windows pipe buffer deadlocks
    env = os.environ.copy()
    env["KENT_MOCK_PIPELINE"] = "1"
    streamlit_exe = str(REPO_ROOT / ".venv" / "Scripts" / "streamlit.exe")

    server_cmd = [
        streamlit_exe,
        "run",
        str(REPO_ROOT / "src" / "dashboard" / "app.py"),
        f"--server.port={PORT}",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
    ]
    print(f"Launching Streamlit server on port {PORT}...", flush=True)
    server_proc = subprocess.Popen(
        server_cmd,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    try:
        if not wait_for_server(URL, timeout=30.0):
            print("Failed to connect to Streamlit server within timeout.", flush=True)
            return

        print("Streamlit server is ready. Launching Playwright browser...", flush=True)
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                viewport={"width": 1500, "height": 950},
                device_scale_factor=1.5,
            )
            page = context.new_page()

            print(f"Navigating to {URL}...", flush=True)
            page.goto(URL, wait_until="load", timeout=30000)
            print("Waiting for initial hydration...", flush=True)
            page.wait_for_selector("button:has-text('1. Intake')", timeout=30000)
            wait_streamlit_idle(page)
            print("App loaded and idle.", flush=True)

            # Check if disclaimer modal dialog is open and dismiss it if visible
            try:
                ack_btn = page.locator("button:has-text('I Acknowledge & Understand')")
                if ack_btn.count() > 0 and ack_btn.first.is_visible():
                    ack_btn.first.click()
                    wait_streamlit_idle(page)
            except Exception:
                pass

            # -----------------------------------------------------------------
            # 1. Step 1: Guided Chat & Intake
            # -----------------------------------------------------------------
            print("\n--- 1. Capturing 01_step1_intake_chat.png ---", flush=True)
            click_tab(page, "Case Workspace")
            step1_btn = page.locator("button:has-text('1. Intake')")
            if step1_btn.count() > 0:
                step1_btn.first.click()
                wait_streamlit_idle(page)

            shot1 = SCREENSHOTS_DIR / "01_step1_intake_chat.png"
            page.screenshot(path=str(shot1), full_page=False)
            print(f"Saved: {shot1.name} ({shot1.stat().st_size:,} bytes)", flush=True)

            # -----------------------------------------------------------------
            # 2. Step 1: Paste Notes Mode
            # -----------------------------------------------------------------
            print("\n--- 2. Capturing 02_step1_paste_notes.png ---", flush=True)
            paste_option = page.locator("button:has-text('Paste notes')")
            if paste_option.count() > 0:
                paste_option.first.click()
                wait_streamlit_idle(page)

                # Fill clinical narrative
                narrative_box = page.locator("textarea")
                if narrative_box.count() > 0:
                    sample_narrative = (
                        "Patient is a 42-year-old female presenting with severe nocturnal anxiety and panic attacks. "
                        "She experiences intense fear of death with sudden restlessness, pacing the room after midnight (between 12:00 AM and 2:00 AM). "
                        "Complains of burning sensation in stomach and head, thirst for small sips of warm water at frequent intervals. "
                        "Symptoms are markedly aggravated by cold air and cold drinks, and noticeably ameliorated by warmth and quiet rest. "
                        "Reports no nausea and no fever."
                    )
                    narrative_box.first.fill(sample_narrative)
                    time.sleep(0.5)

                # Click Extract & review button
                try:
                    ext_btn = page.locator("button:has-text('Extract & review')")
                    if ext_btn.count() > 0 and ext_btn.first.is_visible():
                        ext_btn.first.click()
                        wait_streamlit_idle(page, timeout_ms=30000)
                except Exception as e:
                    print("Extract button note:", e, flush=True)

                shot2 = SCREENSHOTS_DIR / "02_step1_paste_notes.png"
                page.screenshot(path=str(shot2), full_page=False)
                print(
                    f"Saved: {shot2.name} ({shot2.stat().st_size:,} bytes)", flush=True
                )

            # -----------------------------------------------------------------
            # 3. Load Demo Case to unlock Steps 2, 3, 4
            # -----------------------------------------------------------------
            print("\n--- Loading Demo Case DEMO-MIND-001 ---", flush=True)
            try:
                demo_btn = page.locator("button:has-text('Load Demo Case')")
                if demo_btn.count() > 0:
                    demo_btn.first.click()
                    wait_streamlit_idle(page)
                    print("Demo case loaded successfully via UI.", flush=True)
            except Exception as e:
                print("Note on Load Demo Case button:", e, flush=True)

            # -----------------------------------------------------------------
            # 4. Step 2: Review Symptoms (7-dimension clinical review cards)
            # -----------------------------------------------------------------
            print("\n--- 3. Capturing 03_step2_review_cards.png ---", flush=True)
            step2_btn = page.locator("button:has-text('2. Review')")
            if step2_btn.count() > 0:
                step2_btn.first.click()
                wait_streamlit_idle(page)
                shot3 = SCREENSHOTS_DIR / "03_step2_review_cards.png"
                page.screenshot(path=str(shot3), full_page=False)
                print(
                    f"Saved: {shot3.name} ({shot3.stat().st_size:,} bytes)", flush=True
                )

            # -----------------------------------------------------------------
            # 5. Step 3: Analysis & Totality Matrix
            # -----------------------------------------------------------------
            print("\n--- 4. Capturing 04_step3_analysis_matrix.png ---", flush=True)
            step3_btn = page.locator("button:has-text('3. Analysis')")
            if step3_btn.count() > 0:
                step3_btn.first.click()
                wait_streamlit_idle(page)

                # Click Run Repertorization Analysis if available
                run_anal = page.locator(
                    "button:has-text('Run Repertorization Analysis')"
                )
                if run_anal.count() > 0 and run_anal.first.is_visible():
                    print("Clicking Run Repertorization Analysis...", flush=True)
                    run_anal.first.click()
                    wait_streamlit_idle(page, timeout_ms=35000)

                shot4 = SCREENSHOTS_DIR / "04_step3_analysis_matrix.png"
                page.screenshot(path=str(shot4), full_page=False)
                print(
                    f"Saved: {shot4.name} ({shot4.stat().st_size:,} bytes)", flush=True
                )

            # -----------------------------------------------------------------
            # 6. Step 4: Clinical Report View
            # -----------------------------------------------------------------
            print("\n--- 5. Capturing 05_step4_clinical_report.png ---", flush=True)
            step4_btn = page.locator("button:has-text('4. Report')")
            if step4_btn.count() > 0:
                step4_btn.first.click()
                wait_streamlit_idle(page)
                shot5 = SCREENSHOTS_DIR / "05_step4_clinical_report.png"
                page.screenshot(path=str(shot5), full_page=False)
                print(
                    f"Saved: {shot5.name} ({shot5.stat().st_size:,} bytes)", flush=True
                )

            # -----------------------------------------------------------------
            # 7. Tab 2: Case Library
            # -----------------------------------------------------------------
            print("\n--- 6. Capturing 06_case_library.png ---", flush=True)
            click_tab(page, "Case Library")
            shot6 = SCREENSHOTS_DIR / "06_case_library.png"
            page.screenshot(path=str(shot6), full_page=False)
            print(f"Saved: {shot6.name} ({shot6.stat().st_size:,} bytes)", flush=True)

            # -----------------------------------------------------------------
            # 8. Tab 3: Rubric Explorer
            # -----------------------------------------------------------------
            print("\n--- 7. Capturing 07_rubric_explorer.png ---", flush=True)
            click_tab(page, "Rubric Explorer")
            # If search input is present, search for "anxiety night" to show rich rubric results
            try:
                search_input = page.locator("input[placeholder*='search']").first
                if search_input.count() > 0:
                    search_input.fill("anxiety night")
                    page.keyboard.press("Enter")
                    wait_streamlit_idle(page)
            except Exception:
                pass
            shot7 = SCREENSHOTS_DIR / "07_rubric_explorer.png"
            page.screenshot(path=str(shot7), full_page=False)
            print(f"Saved: {shot7.name} ({shot7.stat().st_size:,} bytes)", flush=True)

            # -----------------------------------------------------------------
            # 9. Tab 4: Materia Medica
            # -----------------------------------------------------------------
            print("\n--- 8. Capturing 08_materia_medica.png ---", flush=True)
            click_tab(page, "Materia Medica")
            shot8 = SCREENSHOTS_DIR / "08_materia_medica.png"
            page.screenshot(path=str(shot8), full_page=False)
            print(f"Saved: {shot8.name} ({shot8.stat().st_size:,} bytes)", flush=True)

            # -----------------------------------------------------------------
            # 10. Tab 5: Methodology
            # -----------------------------------------------------------------
            print("\n--- 9. Capturing 09_methodology_settings.png ---", flush=True)
            click_tab(page, "Methodology")
            shot9 = SCREENSHOTS_DIR / "09_methodology_settings.png"
            page.screenshot(path=str(shot9), full_page=False)
            print(f"Saved: {shot9.name} ({shot9.stat().st_size:,} bytes)", flush=True)

            browser.close()
            print("\nAll 9 views captured successfully!", flush=True)

    finally:
        print("Terminating Streamlit server...", flush=True)
        server_proc.terminate()
        try:
            server_proc.wait(timeout=5)
        except Exception:
            server_proc.kill()
        print("Server shutdown complete.", flush=True)


if __name__ == "__main__":
    main()
