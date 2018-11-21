#!/bin/bash

ln -s /usr/local/bin/SnackBar/snackbar.service /lib/systemd/system/snackbar.service
systemctl enable snackbar.service
systemctl daemon-reload
