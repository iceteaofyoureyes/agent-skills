from ba_kit import main


if __name__ == "__main__":
    raise SystemExit(main(["validate-state", *__import__("sys").argv[1:]]))
