from Snackbar_app import init_app, start_schedule, stop_schedule, options

if options.debug:
    loglevel = "debug"
else:
    loglevel = "info"

errorlog = "-"  # stderr
# accesslog = "-"  # stdout
worker_tmp_dir = "/dev/shm"
graceful_timeout = 120
timeout = 120
keepalive = 5
workers = 4
threads = 4


def on_starting(server):
    print(f"starting server: {server}")
    init_app()
    start_schedule()


def on_exit(server):
    print(f"stopping server: {server}")
    stop_schedule()
    pass
