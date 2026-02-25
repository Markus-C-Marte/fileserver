#!/bin/bash
cp /srv/samba/EXT/vault/fileserver/flash-app.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now flash-app
