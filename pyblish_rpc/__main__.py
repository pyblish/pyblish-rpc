import server

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=6000,
                        help="Port to use")
    parser.add_argument("--delay", type=float, default=0.5,
                        help="Higher value means slower")

    args = parser.parse_args()

    server.start_debug_server(**args.__dict__)
