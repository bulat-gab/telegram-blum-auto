#!/bin/bash

sudo cp ./blumbot.service /etc/systemd/system/blumbot.service
sudo systemctl daemon-reload
sudo systemctl enable blumbot.service
