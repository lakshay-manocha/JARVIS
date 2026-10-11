"""
JARVIS Screen + Mouse Integration Test

WARNING:
This test moves the real mouse and clicks.
"""

from __future__ import annotations

from time import sleep

from agent_engine.perception.screen import (
    get_screen_aware,
)

from agent_engine.automation.agents.mouse.mouse_agent import (
    MouseAutomationAgent,
)


def main() -> None:

    print()
    print("=" * 70)
    print("JARVIS SCREEN + MOUSE INTEGRATION TEST")
    print("=" * 70)

    # =====================================================================
    # SCREEN
    # =====================================================================

    screen = get_screen_aware()

    print("\n[1] Warming screen model...")

    screen.warmup()

    print("[+] Screen model ready.")

    # =====================================================================
    # FIND TARGET
    # =====================================================================

    query = input(
        "\nEnter text/UI element to locate: "
    ).strip()

    if not query:
        print("Query cannot be empty.")
        return

    print(
        f"\n[2] Searching for: '{query}'"
    )

    result = screen.find(query)

    print("\nScreen Result:")
    print("-" * 50)

    for key, value in result.items():
        print(
            f"{key:15}: {value}"
        )

    if not result["found"]:

        print(
            "\n[!] Target was not found."
        )

        return

    # =====================================================================
    # COORDINATES
    # =====================================================================

    x = result["x"]
    y = result["y"]

    print(
        f"\n[+] Target coordinates: "
        f"({x}, {y})"
    )

    # =====================================================================
    # MOUSE
    # =====================================================================

    mouse = MouseAutomationAgent()

    mouse.initialize()

    print(
        "\n[3] Moving mouse to target..."
    )

    mouse.actions.move_mouse(
        x=x,
        y=y,
    )

    sleep(1)

    print(
        "[+] Mouse reached target."
    )

    # =====================================================================
    # OPTIONAL CLICK
    # =====================================================================

    answer = input(
        "\nClick target? [y/N]: "
    ).strip().lower()

    if answer == "y":

        print(
            "[4] Clicking..."
        )

        mouse.actions.click(
            button="left"
        )

        print(
            "[+] Click completed."
        )

    else:

        print(
            "[4] Click skipped."
        )

    # =====================================================================
    # STATISTICS
    # =====================================================================

    print("\nScreen Statistics:")
    print("-" * 50)

    print(
        screen.stats
    )

    print(
        "\nTest completed."
    )


if __name__ == "__main__":
    main()