from agent_engine.perception.screen.screen_aware import (
    get_screen_aware,
)


def main():

    screen = get_screen_aware()

    print("\n=== SCREEN SIZE ===")

    size = screen.get_screen_size()

    print(size)

    print("\n=== SCREEN CAPTURE ===")

    capture = screen.capture_screen()

    print(
        "Captured:",
        capture["width"],
        "x",
        capture["height"],
    )

    print("\n=== OCR TEST ===")

    text = input(
        "Enter visible text to locate "
        "(or press Enter to skip): "
    )

    if text.strip():

        result = screen.locate_text(text)

        print(result)

    print("\n=== ELEMENT TEST ===")

    query = input(
        "Enter visible UI element to locate "
        "(or press Enter to skip): "
    )

    if query.strip():

        result = screen.locate_element(query)

        print(result)

    print("\nNo mouse or keyboard operation was performed.")


if __name__ == "__main__":
    main()