sudo systemctl daemon-reload
sudo systemctl enable blumbot.service

Stop service:
sudo systemctl stop blumbot.service

Start service:
sudo systemctl start blumbot.service

Restart service:
sudo systemctl restart blumbot.service

Check status:
sudo systemctl status blumbot.service

Check logs:
sudo journalctl -u blumbot.service

Check logs in real time:
sudo journalctl -u blumbot.service -f
