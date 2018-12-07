#!/bin/bash

#!/bin/bash
# Installation Script
#
if [[ $(whoami) != 'root' ]]; then
  echo ""
  echo "please run this script as root!"
  exit
fi

echo "--- Install requirements ---"
echo ""
apt-get update
apt-get install -y --no-install-recommends python3-pip
pip3 install -r requirements.txt --upgrade

echo "--- Install service ---"
echo ""
name="snackbar"
workingDir=`pwd`
python3=`which python3`
exec="${python3} ${workingDir}/SnackBar.py --port 5000 --host 0.0.0.0"

cat > ${name}.service << EOF
[Unit]
Description=${name}
After=multi-user.target

[Service]
Type=simple
WorkingDirectory=${workingDir}
ExecStart=${exec}
Restart=always

[Install]
WantedBy=multi-user.target
EOF

mv  ${name}.service /lib/systemd/system/${name}.service
chmod 644 /lib/systemd/system/${name}.service
systemctl daemon-reload
systemctl enable ${name}.service

echo "--- start service ---"
echo ""
systemctl start ${name}.service
echo "--- install done ---"
echo ""
echo "show status with:"
echo "sudo systemctl status ${name}.service"

echo ""
echo "show log with:"
echo "sudo journalctl -f -u ${name}.service"
